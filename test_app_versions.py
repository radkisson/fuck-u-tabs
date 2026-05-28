import unittest

from app import list_ug_versions


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
        html = "https://tabs.ultimate-guitar.com/tab/radiohead/creep-chords-99"
        self.assertEqual(list_ug_versions("https://example.com/whatever", html), [])


if __name__ == "__main__":
    unittest.main()
