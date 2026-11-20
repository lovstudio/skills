import importlib.util
import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

spec = importlib.util.spec_from_file_location('sync_skills', Path(__file__).with_name('sync-skills.py'))
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

CATALOG = (
    'version: 1\nskills:\n'
    '- name: alpha\n  repo: lovstudio/alpha-skill\n  name_zh: 阿尔法\n  display_name: Alpha\n'
    '- name: beta\n  repo: lovstudio/beta-skill\n  name_zh: 贝塔\n  display_name: Beta\n'
)
OLD_MIRROR = '---\nname: lov-alpha\n---\n# 阿尔法 · Alpha\n\nold mirror\n'
TOKEN = 'github_pat_test123'
AUTH_FAILURE = (
    'remote: Invalid username or token. Password authentication is not supported for Git operations.\n'
    f"fatal: Authentication failed for 'https://x-access-token:{TOKEN}@github.com/lovstudio/alpha-skill.git/'\n"
)
# CI sets these for every step, the unit tests included.
CI_ENV = {'GITHUB_ACTIONS', 'GITHUB_STEP_SUMMARY', 'SKILLS_SOURCE_TOKEN', 'SKILLS_CLONE_PROTOCOL', 'SKIP_CLONE'}


def fake_git(failures):
    """Stand-in for `git clone`: checks out an upstream SKILL.md and README.md unless the repo is in `failures`."""
    def run(cmd, **kwargs):
        url, dest = cmd[-2], Path(cmd[-1])
        for repo, stderr in failures.items():
            if url.endswith(f'{repo}.git'):
                raise subprocess.CalledProcessError(128, cmd, '', stderr)
        dest.mkdir(parents=True)
        (dest / 'SKILL.md').write_text('---\nname: lov-x\n---\n# Upstream title\n\nfresh\n', encoding='utf-8')
        name = url.rsplit('/', 1)[-1][:-len('-skill.git')]
        (dest / 'README.md').write_text(f'npx skills add lov-{name} -g -y\n', encoding='utf-8')
        return subprocess.CompletedProcess(cmd, 0, '', '')
    return mock.Mock(side_effect=run)


class HardenNpxCommandsTest(unittest.TestCase):
    NAMES = sync.install_names([
        {'name': 'alpha', 'runtime_name': 'lov-alpha'},
        {'name': 'deep-research', 'runtime_name': 'deep-research'},
        {'name': 'branding', 'runtime_name': 'lov-branding-skill'},
        {'name': 'unnamed'},
    ])

    def harden(self, text, filename='README.md'):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / filename
        path.write_text(text, encoding='utf-8')
        modified = sync.harden_npx_commands(Path(tmp.name), self.NAMES)
        return path.read_text(encoding='utf-8'), modified

    def test_bare_catalog_name_installs_through_npx_lovstudio(self):
        # `npx skills add <name>` clones <name> as a repository and fails; see _NPX_BARE_RE.
        cases = {
            'npx skills add alpha -g -y': 'npx lovstudio skills add alpha -g -y',
            'npx skills add lov-alpha -g -y': 'npx lovstudio skills add alpha -g -y',
            'npx skills add lovstudio-alpha -g -y': 'npx lovstudio skills add alpha -g -y',
            # READMEs write `lov-<name>` even where the runtime name is something else.
            'npx skills add lov-deep-research -g -y': 'npx lovstudio skills add deep-research -g -y',
            'npx skills add lov-branding -g -y': 'npx lovstudio skills add branding -g -y',
            'npx skills add lov-branding-skill -g -y': 'npx lovstudio skills add branding -g -y',
            'npx skills add lov-unnamed -g -y': 'npx lovstudio skills add unnamed -g -y',
            'npx skills add lov-alpha': 'npx lovstudio skills add alpha -g -y',
            'npx skills add alpha -y': 'npx lovstudio skills add alpha -y -g',
            'npx skills add alpha --project': 'npx lovstudio skills add alpha --project -y',
            '推荐 `npx skills add lov-alpha -g -y`，或手动安装。': '推荐 `npx lovstudio skills add alpha -g -y`，或手动安装。',
            '| `lov-alpha` | `npx skills add alpha -g -y` | 说明 |': '| `lov-alpha` | `npx lovstudio skills add alpha -g -y` | 说明 |',
            'Run npx skills add alpha to install it.': 'Run npx lovstudio skills add alpha -g -y to install it.',
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(self.harden(f'```bash\n{source}\n```\n'), (f'```bash\n{expected}\n```\n', 1))

    def test_other_sources_and_unknown_names_stay_as_written(self):
        for line in (
            'npx skills add lovstudio/skills --skill lov-alpha -g -y',
            'npx skills add lovstudio/alpha-skill -g -y',
            'npx skills add ./alpha --all -g',
            'npx skills add https://github.com/lovstudio/alpha-skill --skill lov-alpha',
            'npx skills add git@github.com:lovstudio/alpha-skill.git -g -y',
            'npx skills add alpha@1.2.0 -g -y',
            'npx skills add "$SKILL_SOURCE"',
            'npx skills add <name> -g -y',
            'npx skills add not-in-catalog -g -y',
            'npx skills add alpha --skill lov-alpha -g -y',
            'npx skills add alpha -a claude-code -g -y',
            'npx lovstudio skills add alpha -g -y',
            'npx -y lovstudio@latest skills add alpha',
        ):
            with self.subTest(line=line):
                self.assertEqual(self.harden(f'{line}\n'), (f'{line}\n', 0))

    def test_owner_repo_source_still_gets_non_interactive_flags(self):
        self.assertEqual(
            self.harden('npx skills add lovstudio/alpha-skill\n'),
            ('npx skills add lovstudio/alpha-skill --all -g\n', 1),
        )

    def test_changelog_keeps_the_command_it_recorded(self):
        text = '- README 安装命令改为 npx skills add lov-alpha -g -y\n'
        self.assertEqual(self.harden(text, 'CHANGELOG.md'), (text, 0))

    def test_rewritten_command_is_stable(self):
        once, _ = self.harden('npx skills add lov-alpha\n')
        self.assertEqual(self.harden(once), (once, 0))


class MainTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / 'skills.yaml').write_text(CATALOG, encoding='utf-8')
        (self.root / 'skills/alpha').mkdir(parents=True)
        (self.root / 'skills/alpha/SKILL.md').write_text(OLD_MIRROR, encoding='utf-8')
        self.summary = self.root / 'step-summary.md'
        paths = {'ROOT': self.root, 'YAML_PATH': self.root / 'skills.yaml', 'MIRROR_ROOT': self.root / 'skills'}
        for name, value in paths.items():
            patcher = mock.patch.object(sync, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, git, **env):
        clean = {key: value for key, value in os.environ.items() if key not in CI_ENV}
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {**clean, **env}, clear=True), mock.patch.object(sync.subprocess, 'run', git), \
                redirect_stdout(out), redirect_stderr(err):
            code = sync.main()
        return code, out.getvalue(), err.getvalue()

    def mirrored(self, name, filename='SKILL.md'):
        return (self.root / 'skills' / name / filename).read_text(encoding='utf-8')

    def test_empty_token_in_ci_fails_before_any_clone(self):
        git = fake_git({})
        code, out, _ = self.run_main(git, GITHUB_ACTIONS='true', SKILLS_SOURCE_TOKEN='', GITHUB_STEP_SUMMARY=str(self.summary))
        self.assertEqual(code, 1)
        self.assertIn('::error title=SKILLS_SOURCE_TOKEN is empty::', out)
        git.assert_not_called()
        self.assertEqual(self.mirrored('alpha'), OLD_MIRROR)
        self.assertFalse((self.root / 'skills/beta').exists())

    def test_clone_failure_keeps_that_mirror_and_still_syncs_the_rest(self):
        git = fake_git({'lovstudio/alpha-skill': AUTH_FAILURE})
        code, out, err = self.run_main(git, GITHUB_ACTIONS='true', SKILLS_SOURCE_TOKEN=TOKEN, GITHUB_STEP_SUMMARY=str(self.summary))
        self.assertEqual(code, 1)
        self.assertEqual(git.call_count, 2)
        self.assertEqual(git.call_args.kwargs['env']['GIT_TERMINAL_PROMPT'], '0')
        self.assertEqual(self.mirrored('alpha'), OLD_MIRROR)
        # Catalog display names are still applied to the entries that did refresh.
        self.assertIn('# 贝塔 · Beta\n\nfresh', self.mirrored('beta'))
        self.assertIn(
            '::error title=alpha kept its last mirror::lovstudio/alpha-skill: clone failed: '
            'remote: Invalid username or token. Password authentication is not supported for Git operations. | '
            "fatal: Authentication failed for 'https://github.com/lovstudio/alpha-skill.git/'",
            out,
        )
        summary = self.summary.read_text(encoding='utf-8')
        self.assertIn('### 1 of 2 free skills kept their last mirror', summary)
        self.assertIn('- `alpha` lovstudio/alpha-skill: clone failed: ', summary)
        for text in (out, err, summary):
            self.assertNotIn(TOKEN, text)

    def test_all_sources_refreshed_exits_zero(self):
        git = fake_git({})
        code, out, err = self.run_main(git, GITHUB_ACTIONS='true', SKILLS_SOURCE_TOKEN=TOKEN, GITHUB_STEP_SUMMARY=str(self.summary))
        self.assertEqual(code, 0)
        self.assertEqual(git.call_args_list[0].args[0][-2], f'https://x-access-token:{TOKEN}@github.com/lovstudio/alpha-skill.git')
        self.assertIn('# 阿尔法 · Alpha\n\nfresh', self.mirrored('alpha'))
        self.assertIn('# 贝塔 · Beta\n\nfresh', self.mirrored('beta'))
        self.assertEqual(self.mirrored('alpha', 'README.md'), 'npx lovstudio skills add alpha -g -y\n')
        self.assertEqual(self.mirrored('beta', 'README.md'), 'npx lovstudio skills add beta -g -y\n')
        self.assertNotIn('::error', out + err)
        self.assertFalse(self.summary.exists())

    def test_skip_clone_rewrites_the_install_command_of_an_existing_mirror(self):
        (self.root / 'skills/alpha/README.md').write_text('npx skills add lov-alpha -g -y\n', encoding='utf-8')
        git = fake_git({})
        code, out, _ = self.run_main(git, SKIP_CLONE='1')
        self.assertEqual(code, 0)
        # Only beta, which has no mirror yet, is cloned.
        self.assertEqual(git.call_count, 1)
        self.assertEqual(self.mirrored('alpha'), OLD_MIRROR)
        self.assertEqual(self.mirrored('alpha', 'README.md'), 'npx lovstudio skills add alpha -g -y\n')
        self.assertIn('update alpha (SKIP_CLONE=1)', out)

    def test_local_run_without_token_still_reports_and_fails(self):
        git = fake_git({'lovstudio/alpha-skill': "fatal: could not read Username for 'https://github.com': terminal prompts disabled\n"})
        code, out, err = self.run_main(git)
        self.assertEqual(code, 1)
        self.assertEqual(git.call_count, 2)
        self.assertIn('✗ alpha kept its last mirror: lovstudio/alpha-skill: clone failed: fatal: could not read Username', err)
        self.assertNotIn('::error', out + err)


if __name__ == '__main__':
    unittest.main()
