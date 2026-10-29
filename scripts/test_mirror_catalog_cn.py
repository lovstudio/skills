import hashlib
import importlib.util
import io
import os
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
        for name, value in {'ROOT': Path(tmp.name), 'head_commit': lambda: 'abc123'}.items():
            patcher = mock.patch.object(mirror, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, argv, *, upload, readback):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(mirror, 'upload', upload), mock.patch.object(mirror, 'public_sha256', readback), \
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


if __name__ == '__main__':
    unittest.main()
