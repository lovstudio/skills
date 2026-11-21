import hashlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import yaml

spec = importlib.util.spec_from_file_location('mirror_catalog_cn', Path(__file__).with_name('mirror-catalog-cn.py'))
mirror = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mirror)

CATALOG = 'version: 1\nskills:\n- name: example\n  repo: lovstudio/example-skill\n  description: Public example\n'
DIGEST = hashlib.sha256(CATALOG.encode()).hexdigest()


class ValidateTest(unittest.TestCase):
    def test_accepts_the_site_contract(self):
        self.assertEqual(mirror.validate(CATALOG), 1)

    def test_rejects_what_the_site_would_reject(self):
        for text in [
            '',
            'skills: []\n',
            'skills: [\n',
            'skills:\n- name: example\n',
            'skills:\n- name: example\n  repo: "lovstudio/example\\n"\n  description: Trailing newline\n',
            'skills:\n- name: example\n  repo: lovstudio/ünïcode\n  description: Non-ASCII repo\n',
            CATALOG + '  test: true\n',
        ]:
            with self.subTest(text=text), self.assertRaises((ValueError, yaml.YAMLError)):
                mirror.validate(text)


class MainTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        Path(tmp.name, 'skills.yaml').write_text(CATALOG, encoding='utf-8')
        for name, value in {'ROOT': Path(tmp.name), 'head_commit': lambda: 'abc123', 'retired_names': lambda _: []}.items():
            patcher = mock.patch.object(mirror, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, argv, *, upload, readback, upload_documents=None, document_mismatches=None):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(mirror, 'upload', upload), mock.patch.object(mirror, 'public_sha256', readback), \
                mock.patch.object(mirror, 'upload_documents', upload_documents or (lambda *args: None)), \
                mock.patch.object(mirror, 'public_document_mismatches', document_mismatches or (lambda *args: [])), \
                redirect_stdout(out), redirect_stderr(err):
            code = mirror.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_apply_uploads_then_verifies_the_public_copy(self):
        uploads = []
        code, out, _ = self.run_main(['--apply'], upload=lambda *args: uploads.append(args), readback=lambda _: DIGEST)
        self.assertEqual(code, 0)
        self.assertEqual(uploads, [(CATALOG.encode(), DIGEST, 'abc123')])
        self.assertIn('APPLIED', out)

    def test_apply_fails_when_the_public_copy_differs(self):
        code, _, err = self.run_main(['--apply'], upload=lambda *args: None, readback=lambda _: 'stale')
        self.assertEqual(code, 1)
        self.assertIn('not verified', err)

    def test_invalid_catalog_is_never_uploaded(self):
        Path(mirror.ROOT, 'skills.yaml').write_text('skills: []\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.run_main(['--apply'], upload=mock.Mock(side_effect=AssertionError('uploaded')), readback=lambda _: DIGEST)

    def test_dry_run_compares_with_the_live_mirror_without_uploading(self):
        upload = mock.Mock(side_effect=AssertionError('dry run uploaded'))
        code, out, _ = self.run_main([], upload=upload, readback=lambda _: 'stale')
        self.assertEqual(code, 0)
        self.assertIn('mirror differs', out)

    def test_apply_publishes_documents_before_the_catalog_heartbeat(self):
        calls = []
        code, out, _ = self.run_main(
            ['--apply'],
            upload=lambda *args: calls.append('catalog'),
            readback=lambda _: DIGEST,
            upload_documents=lambda uploads, deletes, commit: calls.append(('documents', len(uploads), len(deletes), commit)),
        )
        self.assertEqual(code, 0)
        # The fixture's only Skill has no mirrored files, so its three keys are deleted.
        self.assertEqual(calls, [('documents', 0, 3, 'abc123'), 'catalog'])
        self.assertIn('every Skill document', out)

    def test_document_failure_still_refreshes_the_catalog_and_fails_the_run(self):
        for upload_documents, mismatches in [
            (mock.Mock(side_effect=PermissionError('AccessDenied')), lambda *args: []),
            (lambda *args: None, lambda *args: ['catalogs/skills/example/SKILL.md']),
        ]:
            with self.subTest(mismatches=mismatches):
                uploads = []
                code, _, err = self.run_main(
                    ['--apply'], upload=lambda *args: uploads.append(args), readback=lambda _: DIGEST,
                    upload_documents=upload_documents, document_mismatches=mismatches,
                )
                self.assertEqual(code, 1)
                self.assertEqual(len(uploads), 1)
                self.assertIn('Skill documents are not verified', err)

    def test_unknown_history_still_refreshes_the_catalog_and_fails_the_run(self):
        uploads, plans = [], []
        with mock.patch.object(mirror, 'retired_names', mock.Mock(side_effect=RuntimeError('shallow clone'))):
            code, _, err = self.run_main(
                ['--apply'], upload=lambda *args: uploads.append(args), readback=lambda _: DIGEST,
                upload_documents=lambda uploads, deletes, commit: plans.append(len(deletes)),
            )
        self.assertEqual(code, 1)
        self.assertEqual(len(uploads), 1)
        # The catalog's own entries are still planned without the history.
        self.assertEqual(plans, [3])
        self.assertIn('retired Skills unknown', err)

    def test_dry_run_reports_documents_without_uploading_them(self):
        code, out, _ = self.run_main(
            [], upload=mock.Mock(side_effect=AssertionError('uploaded')), readback=lambda _: DIGEST,
            upload_documents=mock.Mock(side_effect=AssertionError('uploaded documents')),
            document_mismatches=lambda *args: ['catalogs/skills/example/SKILL.md'],
        )
        self.assertEqual(code, 0)
        self.assertIn('"documents_out_of_sync": 1', out)
        self.assertIn('mirror differs', out)

    def test_destination_and_source_cannot_be_overridden(self):
        for argv in (['--bucket', 'other'], ['--apply', 'skills.yaml'], ['--dry-run']):
            with self.subTest(argv=argv):
                code, _, err = self.run_main(argv, upload=mock.Mock(side_effect=AssertionError), readback=mock.Mock())
                self.assertEqual(code, 2)
                self.assertIn('fixed', err)


class UploadTest(unittest.TestCase):
    def test_one_put_object_to_the_fixed_key_with_the_sts_session(self):
        calls = {}
        fake_sdk = types.SimpleNamespace(
            config=types.SimpleNamespace(load_default=types.SimpleNamespace),
            credentials=types.SimpleNamespace(StaticCredentialsProvider=lambda *creds: creds),
            PutObjectRequest=lambda **fields: fields,
            Client=lambda config: types.SimpleNamespace(put_object=lambda request: calls.setdefault('puts', []).append((config, request))),
        )
        env = {'ALIBABA_CLOUD_ACCESS_KEY_ID': 'id', 'ALIBABA_CLOUD_ACCESS_KEY_SECRET': 'secret', 'ALIBABA_CLOUD_SECURITY_TOKEN': 'token'}
        with mock.patch.dict(sys.modules, {'alibabacloud_oss_v2': fake_sdk}), mock.patch.dict(os.environ, env):
            mirror.upload(b'body', DIGEST, 'abc123')
        [(config, request)] = calls['puts']
        self.assertEqual((config.region, config.credentials_provider), ('cn-hangzhou', ('id', 'secret', 'token')))
        self.assertEqual((request['bucket'], request['key'], request['body']), ('lovstudio-downloads', 'catalogs/skills.yaml', b'body'))
        self.assertEqual(request['metadata'], {'source': mirror.SOURCE, 'source-sha256': DIGEST, 'source-commit': 'abc123'})
        self.assertEqual(request['content_type'], 'application/yaml; charset=utf-8')
        self.assertNotIn('acl', request)

    def test_public_url_is_the_object_the_site_reads(self):
        self.assertEqual(mirror.PUBLIC_URL, 'https://lovstudio-downloads.oss-cn-hangzhou.aliyuncs.com/catalogs/skills.yaml')


PLAN_CATALOG = """skills:
- {name: alpha, repo: lovstudio/alpha-skill, description: Free}
- {name: beta, repo: lovstudio/beta-skill, description: Paid, paid: true}
- {name: gamma, repo: lovstudio/gamma-skill, description: Internal, pricing: {visibility: internal}}
- {name: delta, repo: lovstudio/delta-skill, description: Test entry, test: true}
- {name: epsilon, repo: lovstudio/epsilon-skill, description: Free without a mirror}
"""


class DocumentPlanTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for name in ('alpha', 'beta', 'gamma', 'delta'):
            folder = self.root / 'skills' / name
            folder.mkdir(parents=True)
            (folder / 'SKILL.md').write_text(f'---\nname: {name}\n---\n', encoding='utf-8')
            (folder / 'README.md').write_text(f'# {name}\n', encoding='utf-8')
        patcher = mock.patch.object(mirror, 'ROOT', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_only_free_public_skills_are_published_and_everything_else_is_deleted(self):
        uploads, deletes = mirror.document_plan(PLAN_CATALOG, ['retired'])
        self.assertEqual([key for key, _ in uploads], ['catalogs/skills/alpha/SKILL.md', 'catalogs/skills/alpha/README.md'])
        self.assertEqual(uploads[0][1], b'---\nname: alpha\n---\n')
        # beta, gamma and delta still have mirrored files, e.g. from before beta turned paid
        # (fourier-portrait, 2026-11-21): their free-era copies must not stay public.
        self.assertEqual(deletes, ['catalogs/skills/alpha/skill-card.yaml'] + [
            f'catalogs/skills/{name}/{file}'
            for name in ('beta', 'gamma', 'delta', 'epsilon', 'retired')
            for file in ('SKILL.md', 'README.md', 'skill-card.yaml')
        ])

    def test_an_unpublished_entry_is_deleted_even_through_a_symlink(self):
        (self.root / 'skills' / 'beta' / 'README.md').unlink()
        (self.root / 'skills' / 'beta' / 'README.md').symlink_to(self.root / 'skills.yaml')
        _, deletes = mirror.document_plan(PLAN_CATALOG)
        self.assertIn('catalogs/skills/beta/README.md', deletes)

    def test_names_that_are_not_plain_keys_are_refused(self):
        for name in ('../evil', 'Upper', 'a/b', '-lead'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                mirror.document_plan(f'skills:\n- {{name: "{name}", repo: lovstudio/x, description: d}}\n')

    def test_a_symlinked_document_is_never_published(self):
        (self.root / 'skills' / 'alpha' / 'README.md').unlink()
        (self.root / 'skills' / 'alpha' / 'README.md').symlink_to(self.root / 'skills.yaml')
        with self.assertRaises(ValueError):
            mirror.document_plan(PLAN_CATALOG)


class RetiredNamesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name, 'repo')
        self.root.mkdir()
        self.git('init', '-q')
        for path in ('skills/alpha/SKILL.md', 'skills/old/SKILL.md', 'skills/Bad_Name/SKILL.md', 'skills/alpha/sub/SKILL.md'):
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text('---\nname: x\n---\n', encoding='utf-8')
        self.git('add', '-A')
        self.git('commit', '-q', '-m', 'mirror')
        self.git('rm', '-q', '-r', 'skills/old')
        self.git('commit', '-q', '-m', 'retire old')

    def git(self, *args, cwd=None):
        env = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.com',
               'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@example.com'}
        subprocess.run(['git', *args], cwd=cwd or self.root, check=True, capture_output=True, env=env)

    def test_names_mirrored_in_history_but_no_longer_listed(self):
        with mock.patch.object(mirror, 'ROOT', self.root):
            self.assertEqual(mirror.retired_names('skills:\n- {name: alpha, repo: lovstudio/alpha-skill, description: d}\n'), ['old'])

    def test_a_listed_name_is_not_retired_even_without_a_mirror(self):
        with mock.patch.object(mirror, 'ROOT', self.root):
            self.assertEqual(mirror.retired_names(
                'skills:\n- {name: alpha, repo: lovstudio/alpha-skill, description: d}\n'
                '- {name: old, repo: lovstudio/old-skill, description: d, paid: true}\n'
            ), [])

    def test_a_shallow_clone_is_refused(self):
        shallow = self.root.parent / 'shallow'
        self.git('clone', '-q', '--depth', '1', f'file://{self.root}', str(shallow), cwd=self.root.parent)
        with mock.patch.object(mirror, 'ROOT', shallow), self.assertRaises(RuntimeError):
            mirror.retired_names('skills: []\n')


class UploadDocumentsTest(unittest.TestCase):
    def test_puts_and_deletes_go_to_the_fixed_bucket_with_source_metadata(self):
        calls = {'puts': [], 'deletes': []}
        client = types.SimpleNamespace(
            put_object=lambda request: calls['puts'].append(request),
            delete_object=lambda request: calls['deletes'].append(request),
        )
        fake_sdk = types.SimpleNamespace(
            config=types.SimpleNamespace(load_default=types.SimpleNamespace),
            credentials=types.SimpleNamespace(StaticCredentialsProvider=lambda *creds: creds),
            PutObjectRequest=lambda **fields: fields,
            DeleteObjectRequest=lambda **fields: fields,
            Client=lambda config: client,
        )
        env = {'ALIBABA_CLOUD_ACCESS_KEY_ID': 'id', 'ALIBABA_CLOUD_ACCESS_KEY_SECRET': 'secret', 'ALIBABA_CLOUD_SECURITY_TOKEN': 'token'}
        uploads = [('catalogs/skills/alpha/SKILL.md', b'skill'), ('catalogs/skills/alpha/skill-card.yaml', b'card')]
        with mock.patch.dict(sys.modules, {'alibabacloud_oss_v2': fake_sdk}), mock.patch.dict(os.environ, env):
            mirror.upload_documents(uploads, ['catalogs/skills/alpha/README.md'], 'abc123')
        skill, card = calls['puts']
        self.assertEqual((skill['bucket'], skill['key'], skill['body']), ('lovstudio-downloads', 'catalogs/skills/alpha/SKILL.md', b'skill'))
        self.assertEqual(skill['content_type'], 'text/markdown; charset=utf-8')
        self.assertEqual(card['content_type'], 'application/yaml; charset=utf-8')
        self.assertEqual(skill['metadata'], {
            'source': 'https://raw.githubusercontent.com/lovstudio/skills/main/skills/alpha/SKILL.md',
            'source-sha256': hashlib.sha256(b'skill').hexdigest(),
            'source-commit': 'abc123',
        })
        self.assertNotIn('acl', skill)
        self.assertEqual(calls['deletes'], [{'bucket': 'lovstudio-downloads', 'key': 'catalogs/skills/alpha/README.md'}])


class PublicDocumentMismatchTest(unittest.TestCase):
    def test_compares_anonymous_copies_and_expects_deleted_keys_to_be_gone(self):
        public = {'catalogs/skills/a/SKILL.md': b'same', 'catalogs/skills/b/SKILL.md': b'old', 'catalogs/skills/c/README.md': b'left behind'}

        def urlopen(url, timeout):
            key = url.removeprefix(mirror.PUBLIC_BASE + '/').split('?')[0]
            if key not in public:
                raise mirror.urllib.error.HTTPError(url, 404, 'Not Found', {}, None)
            return contextlib_response(public[key])

        uploads = [('catalogs/skills/a/SKILL.md', b'same'), ('catalogs/skills/b/SKILL.md', b'new')]
        deletes = ['catalogs/skills/c/README.md', 'catalogs/skills/d/README.md']
        with mock.patch.object(mirror.urllib.request, 'urlopen', urlopen):
            self.assertEqual(
                sorted(mirror.public_document_mismatches(uploads, deletes, 'x')),
                ['catalogs/skills/b/SKILL.md', 'catalogs/skills/c/README.md'],
            )


    def test_dropped_connections_are_retried_but_real_answers_are_not(self):
        attempts = []

        def flaky(url, timeout):
            attempts.append(url)
            if len(attempts) < 3:
                raise mirror.urllib.error.URLError('EOF occurred in violation of protocol')
            return contextlib_response(b'same')

        with mock.patch.object(mirror.urllib.request, 'urlopen', flaky):
            self.assertEqual(mirror.public_document_mismatches([('catalogs/skills/a/SKILL.md', b'same')], [], 'x'), [])
        self.assertEqual(len(attempts), 3)

        def forbidden(url, timeout):
            raise mirror.urllib.error.HTTPError(url, 403, 'Forbidden', {}, None)

        with mock.patch.object(mirror.urllib.request, 'urlopen', forbidden), self.assertRaises(mirror.urllib.error.HTTPError):
            mirror.public_document_mismatches([('catalogs/skills/a/SKILL.md', b'same')], [], 'x')


def contextlib_response(body):
    response = mock.MagicMock()
    response.__enter__.return_value.read.return_value = body
    return response


if __name__ == '__main__':
    unittest.main()
