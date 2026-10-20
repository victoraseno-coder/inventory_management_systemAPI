import unittest

import app as app_module


class SeedDataTests(unittest.TestCase):
    """The inventory array is built from the OpenFoodFacts-shaped seed file."""

    def test_seed_file_loads_items(self):
        store, next_id = app_module.load_seed_data()

        self.assertGreater(len(store), 0)
        self.assertEqual(next_id, len(store) + 1)

    def test_every_seeded_item_has_an_id_and_name(self):
        store, _ = app_module.load_seed_data()

        for item in store:
            self.assertIn("id", item)
            self.assertIsNotNone(item["name"])

    def test_seeded_ids_are_unique(self):
        store, _ = app_module.load_seed_data()

        ids = [item["id"] for item in store]
        self.assertEqual(len(ids), len(set(ids)))

    def test_seeded_items_keep_the_external_details(self):
        store, _ = app_module.load_seed_data()

        first = store[0]
        self.assertIn("brands", first["external_details"])
        self.assertIn("ingredients_text", first["external_details"])

    def test_missing_seed_file_gives_an_empty_store(self):
        original = app_module.SEED_FILE
        app_module.SEED_FILE = "does_not_exist.json"
        try:
            store, next_id = app_module.load_seed_data()
        finally:
            app_module.SEED_FILE = original

        self.assertEqual(store, [])
        self.assertEqual(next_id, 1)


if __name__ == "__main__":
    unittest.main()