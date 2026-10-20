import unittest

from app import create_app


class InventoryCrudTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config.update(TESTING=True)
        # Each test starts from an empty store so results do not depend on
        # the seed file or on the order the tests run in.
        self.app.config["STORE"] = []
        self.app.config["NEXT_ID"] = 1

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_get_inventory_returns_empty_list(self):
        response = self.client.get("/inventory")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_create_and_fetch_item(self):
        response = self.client.post(
            "/inventory",
            json={"name": "Keyboard", "quantity": 5, "price": 49.99},
        )
        self.assertEqual(response.status_code, 201)
        item = response.get_json()
        self.assertEqual(item["name"], "Keyboard")
        self.assertEqual(item["quantity"], 5)

        fetch_response = self.client.get(f"/inventory/{item['id']}")
        self.assertEqual(fetch_response.status_code, 200)
        self.assertEqual(fetch_response.get_json()["id"], item["id"])

    def test_create_requires_a_name(self):
        response = self.client.post("/inventory", json={"quantity": 2})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Name is required")

    def test_create_rejects_negative_quantity(self):
        response = self.client.post(
            "/inventory",
            json={"name": "Mouse", "quantity": -3},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Quantity must not be negative")

    def test_create_rejects_negative_price(self):
        response = self.client.post(
            "/inventory",
            json={"name": "Mouse", "price": -1.0},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Price must not be negative")

    def test_fetch_missing_item_returns_404(self):
        response = self.client.get("/inventory/9999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"], "Item not found")

    def test_ids_increment_across_items(self):
        first = self.client.post("/inventory", json={"name": "First"}).get_json()
        second = self.client.post("/inventory", json={"name": "Second"}).get_json()
        self.assertEqual(second["id"], first["id"] + 1)


if __name__ == "__main__":
    unittest.main()=