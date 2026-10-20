import unittest

from app import create_app


class InventoryUpdateDeleteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config.update(TESTING=True)
        self.app.config["STORE"] = []
        self.app.config["NEXT_ID"] = 1

    def create_item(self, **overrides):
        payload = {"name": "Mouse", "quantity": 3, "price": 19.5}
        payload.update(overrides)
        return self.client.post("/inventory", json=payload).get_json()

    def test_update_and_delete_item(self):
        item_id = self.create_item()["id"]

        updated = self.client.patch(
            f"/inventory/{item_id}",
            json={"quantity": 10, "price": 25.0},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["quantity"], 10)
        self.assertEqual(updated.get_json()["price"], 25.0)

        deleted = self.client.delete(f"/inventory/{item_id}")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.get_json()["message"], "Item deleted")

    def test_update_leaves_untouched_fields_alone(self):
        item_id = self.create_item()["id"]

        response = self.client.patch(f"/inventory/{item_id}", json={"price": 30.0})
        body = response.get_json()
        self.assertEqual(body["price"], 30.0)
        self.assertEqual(body["name"], "Mouse")
        self.assertEqual(body["quantity"], 3)

    def test_update_rejects_negative_quantity(self):
        item_id = self.create_item()["id"]

        response = self.client.patch(f"/inventory/{item_id}", json={"quantity": -1})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Quantity must not be negative")

    def test_update_missing_item_returns_404(self):
        response = self.client.patch("/inventory/9999", json={"quantity": 1})
        self.assertEqual(response.status_code, 404)

    def test_delete_missing_item_returns_404(self):
        response = self.client.delete("/inventory/9999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"], "Item not found")

    def test_deleted_item_is_gone_from_the_list(self):
        item_id = self.create_item()["id"]
        self.client.delete(f"/inventory/{item_id}")

        response = self.client.get("/inventory")
        self.assertEqual(response.get_json(), [])


if __name__ == "__main__":
    unittest.main()