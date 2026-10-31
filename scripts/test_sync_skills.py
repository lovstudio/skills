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
    """Stand-in for `git clone`: checks out an upstream SKILL.md unless the repo is in `failures`."""
    def run(cmd, **kwargs):
        url, dest = cmd[-2], Path(cmd[-1])
        for repo, stderr in failures.items():
            if url.endswith(f'{repo}.git'):
                raise subprocess.CalledProcessError(128, cmd, '', stderr)
        dest.mkdir(parents=True)
        (dest / 'SKILL.md').write_text('---\nname: lov-x\n---\n# Upstream title\n\nfresh\n', encoding='utf-8')
        return subprocess.CompletedProcess(cmd, 0, '', '')
    return mock.Mock(side_effect=run)


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

    def mirrored(self, name):
        return (self.root / 'skills' / name / 'SKILL.md').read_text(encoding='utf-8')

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
        self.assertNotIn('::error', out + err)
        self.assertFalse(self.summary.exists())

    def test_local_run_without_token_still_reports_and_fails(self):
        git = fake_git({'lovstudio/alpha-skill': "fatal: could not read Username for 'https://github.com': terminal prompts disabled\n"})
        code, out, err = self.run_main(git)
        self.assertEqual(code, 1)
        self.assertEqual(git.call_count, 2)
        self.assertIn('✗ alpha kept its last mirror: lovstudio/alpha-skill: clone failed: fatal: could not read Username', err)
        self.assertNotIn('::error', out + err)


if __name__ == '__main__':
    unittest.main()
