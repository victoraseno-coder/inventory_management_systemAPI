import unittest
from unittest.mock import patch

from app import create_app


class LookupRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config.update(TESTING=True)
        self.app.config["STORE"] = []
        self.app.config["NEXT_ID"] = 1

    def test_lookup_requires_query_or_barcode(self):
        response = self.client.get("/products/lookup")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Provide a barcode or product name", response.get_json()["error"])

    @patch("app.fetch_product_details")
    def test_lookup_returns_product_details(self, mock_fetch):
        mock_fetch.return_value = {"product_name": "Nutella", "brands": "Ferrero"}

        response = self.client.get("/products/lookup?query=nutella")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["product_name"], "Nutella")

    @patch("app.fetch_product_details", return_value={})
    def test_lookup_reports_a_missing_product(self, mock_fetch):
        response = self.client.get("/products/lookup?barcode=000")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"], "Product not found")

    @patch("app.fetch_product_details")
    def test_import_adds_the_product_to_the_inventory(self, mock_fetch):
        mock_fetch.return_value = {"product_name": "Nutella", "brands": "Ferrero"}

        response = self.client.post(
            "/inventory/import",
            json={"barcode": "3017620422003", "quantity": 4, "price": 5.5},
        )

        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body["name"], "Nutella")
        self.assertEqual(body["quantity"], 4)

        listed = self.client.get("/inventory").get_json()
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["name"], "Nutella")

    def test_import_requires_query_or_barcode(self):
        response = self.client.post("/inventory/import", json={})
        self.assertEqual(response.status_code, 400)

    @patch("app.fetch_product_details", return_value={})
    def test_import_reports_a_missing_product(self, mock_fetch):
        response = self.client.post("/inventory/import", json={"barcode": "000"})
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()