import importlib.util
import io
import json
import os
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

spec = importlib.util.spec_from_file_location('refresh_website', Path(__file__).with_name('refresh-website.py'))
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)

HEAD = 'a' * 40
OLD = 'b' * 40
SECRET = 's3cret-value'
SYNC = {'catalog_skills': 2, 'delisted_skills': 0}


def answer(commit):
    return {'catalog_commits': {refresh.REPO: commit} if commit else None, 'pricing_sync': SYNC}


def http_error(code):
    return urllib.error.HTTPError(refresh.SITE, code, 'error', {}, io.BytesIO(b'{"error":"unauthorized"}'))


class MainTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.summary = Path(tmp.name, 'summary.md')

    def run_main(self, answers, secret=SECRET):
        sent, sleeps, out = [], [], io.StringIO()

        def revalidate(value):
            sent.append(value)
            item = answers.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        env = {'REVALIDATE_SECRET': secret, 'GH_TOKEN': '', 'GITHUB_STEP_SUMMARY': str(self.summary)}
        with mock.patch.dict(os.environ, env), mock.patch.object(refresh, 'revalidate', revalidate), \
                mock.patch.object(refresh, 'main_commit', lambda token: HEAD), \
                mock.patch.object(refresh.time, 'sleep', sleeps.append), redirect_stdout(out):
            code = refresh.main()
        self.assertNotIn(SECRET, out.getvalue())
        summary = self.summary.read_text(encoding='utf-8') if self.summary.exists() else ''
        return code, out.getvalue(), sent, sleeps, summary

    def test_without_the_secret_warns_and_sends_nothing(self):
        code, out, sent, _, summary = self.run_main([], secret='')
        self.assertEqual((code, sent), (0, []))
        self.assertIn('::warning title=Website not refreshed::', out)
        self.assertIn('not refreshed', summary)

    def test_confirms_the_commit_main_points_to(self):
        code, _, sent, sleeps, summary = self.run_main([answer(HEAD)])
        self.assertEqual((code, sent, sleeps), (0, [SECRET], []))
        self.assertIn(f'lovstudio/skills@{HEAD[:7]}', summary)
        self.assertIn(json.dumps(SYNC, separators=(',', ':')), summary)

    def test_refreshes_again_until_the_site_reads_main(self):
        code, out, sent, sleeps, _ = self.run_main([answer(OLD), http_error(504), answer(HEAD)])
        self.assertEqual((code, len(sent), sleeps), (0, 3, [refresh.RETRY_DELAY] * 2))
        self.assertIn(f'read {OLD[:7]} while main is {HEAD[:7]}', out)

    def test_waits_out_the_raw_cache_once_when_the_site_names_no_commit(self):
        code, out, sent, sleeps, summary = self.run_main([answer(None), answer(None)])
        self.assertEqual((code, len(sent), sleeps), (0, 2, [refresh.RAW_MAIN_MAX_AGE]))
        self.assertIn('::warning title=Website commit not confirmed::', out)
        self.assertIn('commit unconfirmed', summary)

    def test_fails_when_the_site_keeps_reading_an_old_commit(self):
        code, out, sent, sleeps, _ = self.run_main([answer(OLD)] * refresh.ATTEMPTS)
        self.assertEqual((code, len(sent)), (1, refresh.ATTEMPTS))
        self.assertEqual(sleeps, [refresh.RETRY_DELAY] * (refresh.ATTEMPTS - 1))
        self.assertIn('::error title=Website reads an old catalog::', out)

    def test_a_rejected_secret_fails_without_retrying(self):
        code, out, sent, sleeps, _ = self.run_main([refresh.Rejected('answered 401')])
        self.assertEqual((code, len(sent), sleeps), (1, 1, []))
        self.assertIn('::error title=Website refresh rejected::', out)


class RequestTest(unittest.TestCase):
    def test_revalidate_posts_the_catalog_refresh_with_the_secret(self):
        seen = []

        def urlopen(request, timeout):
            seen.append(request)
            return io.BytesIO(json.dumps(answer(HEAD)).encode())

        with mock.patch.object(refresh.urllib.request, 'urlopen', urlopen):
            self.assertEqual(refresh.revalidate(SECRET), answer(HEAD))
        request = seen[0]
        self.assertEqual((request.get_method(), request.full_url), ('POST', f'{refresh.SITE}/api/revalidate'))
        self.assertEqual(request.get_header('X-revalidate-secret'), SECRET)
        self.assertEqual(request.get_header('User-agent'), refresh.USER_AGENT)
        self.assertEqual(json.loads(request.data), refresh.BODY)

    def test_only_a_401_is_a_rejection(self):
        for code, kind in [(401, refresh.Rejected), (500, RuntimeError)]:
            with self.subTest(code=code), mock.patch.object(refresh.urllib.request, 'urlopen',
                                                            mock.Mock(side_effect=http_error(code))):
                with self.assertRaises(kind) as raised:
                    refresh.revalidate(SECRET)
                self.assertIn(f'answered {code}: {{"error":"unauthorized"}}', str(raised.exception))
                self.assertNotIn(SECRET, str(raised.exception))


if __name__ == '__main__':
    unittest.main()
