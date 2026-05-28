import unittest
import io
import contextlib
from unittest.mock import patch

from app import list_ug_versions, _is_ug_tab_url, main


class ListUgVersionsTests(unittest.TestCase):
    def test_list_versions_filters_by_song_and_deduplicates(self):
        url = "https://tabs.ultimate-guitar.com/tab/radiohead/creep-chords-12"
        html = """
        <script>
        "https:\\/\\/tabs.ultimate-guitar.com\\/tab\\/radiohead\\/creep-chords-12",
        "https:\\/\\/tabs.ultimate-guitar.com\\/tab\\/radiohead\\/creep-chords-99",
        "https:\\/\\/tabs.ultimate-guitar.com\\/tab\\/radiohead\\/creep-tabs-88",
        "https:\\/\\/tabs.ultimate-guitar.com\\/tab\\/radiohead\\/high-and-dry-chords-77",
        "https:\\/\\/tabs.ultimate-guitar.com\\/tab\\/radiohead\\/creep-chords-99"
        </script>
        """

        versions = list_ug_versions(url, html)

        self.assertEqual(
            versions,
            [
                "https://tabs.ultimate-guitar.com/tab/radiohead/creep-chords-12",
                "https://tabs.ultimate-guitar.com/tab/radiohead/creep-chords-99",
                "https://tabs.ultimate-guitar.com/tab/radiohead/creep-tabs-88",
            ],
        )

    def test_list_versions_returns_empty_for_invalid_input_url(self):
        sample_html = '<a href="https://tabs.ultimate-guitar.com/tab/radiohead/creep-chords-99">v</a>'
        self.assertEqual(list_ug_versions("https://example.com/whatever", sample_html), [])

    def test_list_versions_returns_empty_when_no_candidates_exist(self):
        url = "https://tabs.ultimate-guitar.com/tab/radiohead/creep-chords-12"
        self.assertEqual(list_ug_versions(url, "<html><body>No tab links</body></html>"), [])

    def test_list_versions_accepts_relative_and_encoded_links(self):
        url = "https://tabs.ultimate-guitar.com/tab/radiohead/creep-chords-12"
        html = """
        <a href="/tab/radiohead/creep-tabs-88">relative</a>
        <script>
        "https%3A%2F%2Ftabs.ultimate-guitar.com%2Ftab%2Fradiohead%2Fcreep-chords-99"
        </script>
        """
        self.assertEqual(
            list_ug_versions(url, html),
            [
                "https://tabs.ultimate-guitar.com/tab/radiohead/creep-tabs-88",
                "https://tabs.ultimate-guitar.com/tab/radiohead/creep-chords-99",
            ],
        )

    def test_list_versions_does_not_over_normalize_internal_tab_word(self):
        url = "https://tabs.ultimate-guitar.com/tab/example/my-tab-song-chords-1"
        html = """
        "https:\\/\\/tabs.ultimate-guitar.com\\/tab\\/example\\/my-tab-song-tabs-2"
        "https:\\/\\/tabs.ultimate-guitar.com\\/tab\\/example\\/my-song-tabs-3"
        """
        self.assertEqual(
            list_ug_versions(url, html),
            ["https://tabs.ultimate-guitar.com/tab/example/my-tab-song-tabs-2"],
        )


class UgTabUrlValidationTests(unittest.TestCase):
    def test_is_ug_tab_url_requires_exact_host(self):
        self.assertTrue(_is_ug_tab_url("https://tabs.ultimate-guitar.com/tab/radiohead/creep-chords-12"))
        self.assertFalse(_is_ug_tab_url("https://tabs.ultimate-guitar.com.evil.org/tab/radiohead/creep-chords-12"))
        self.assertFalse(_is_ug_tab_url("https://ultimate-guitar.com/tab/radiohead/creep-chords-12"))


class ListVersionsCliErrorTests(unittest.TestCase):
    def test_list_versions_handles_fetch_error_cleanly(self):
        stderr = io.StringIO()
        with patch("sys.argv", ["app.py", "--list-versions", "https://tabs.ultimate-guitar.com/tab/radiohead/creep-chords-12"]), \
             patch("app.fetch", side_effect=RuntimeError("dns failure")), \
             contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as cm:
                main()

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Unable to fetch URL for version listing: dns failure", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
