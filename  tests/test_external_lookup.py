import unittest
from unittest.mock import MagicMock, patch

import app as app_module
from app import create_app


class FetchProductDetailsTests(unittest.TestCase):
    """Exercise the OpenFoodFacts client itself with requests mocked out."""

    def build_response(self, payload):
        response = MagicMock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        return response

    @patch("app.requests.get")
    def test_fetch_by_barcode_maps_the_product(self, mock_get):
        mock_get.return_value = self.build_response(
            {
                "status": 1,
                "product": {
                    "product_name": "Organic Almond Milk",
                    "brands": "Silk",
                    "image_url": "https://example.com/milk.jpg",
                    "categories": "Beverages",
                },
            }
        )

        details = app_module.fetch_product_details(barcode="123456789012")

        self.assertEqual(details["product_name"], "Organic Almond Milk")
        self.assertEqual(details["brands"], "Silk")
        self.assertIn("123456789012", mock_get.call_args.args[0])

    @patch("app.requests.get")
    def test_unknown_barcode_returns_empty_dict(self, mock_get):
        mock_get.return_value = self.build_response({"status": 0})

        self.assertEqual(app_module.fetch_product_details(barcode="000"), {})

    @patch("app.requests.get")
    def test_search_by_name_uses_the_first_match(self, mock_get):
        mock_get.return_value = self.build_response(
            {
                "products": [
                    {"product_name": "Dark Chocolate Bar", "brands": "Lindt"},
                    {"product_name": "Milk Chocolate Bar", "brands": "Other"},
                ]
            }
        )

        details = app_module.fetch_product_details(query="chocolate")

        self.assertEqual(details["product_name"], "Dark Chocolate Bar")

    @patch("app.requests.get")
    def test_search_with_no_results_returns_empty_dict(self, mock_get):
        mock_get.return_value = self.build_response({"products": []})

        self.assertEqual(app_module.fetch_product_details(query="nothing"), {})

    @patch("app.requests.get", side_effect=app_module.requests.RequestException)
    def test_network_failure_returns_empty_dict(self, mock_get):
        self.assertEqual(app_module.fetch_product_details(barcode="123"), {})


class ExternalLookupTests(unittest.TestCase):
    """Check that stored items are enriched with the external details."""

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config.update(TESTING=True)
        self.app.config["STORE"] = []
        self.app.config["NEXT_ID"] = 1

    @patch("app.fetch_product_details")
    def test_barcode_enriches_a_new_item(self, mock_fetch):
        mock_fetch.return_value = {
            "product_name": "Example Product",
            "brands": "Example Brand",
            "image_url": "https://example.com/image.jpg",
            "categories": "Snacks",
        }

        response = self.client.post(
            "/inventory",
            json={
                "name": "Example Product",
                "quantity": 2,
                "price": 3.5,
                "barcode": "1234567890",
            },
        )

        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body["external_details"]["product_name"], "Example Product")
        mock_fetch.assert_called_once_with(barcode="1234567890")

    @patch("app.fetch_product_details")
    def test_item_without_barcode_skips_the_lookup(self, mock_fetch):
        response = self.client.post("/inventory", json={"name": "Plain Item"})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["external_details"], {})
        mock_fetch.assert_not_called()

    @patch("app.fetch_product_details")
    def test_new_barcode_refreshes_the_details(self, mock_fetch):
        mock_fetch.return_value = {"product_name": "Updated Item", "brands": "Brand X"}

        created = self.client.post("/inventory", json={"name": "Old Item"}).get_json()
        response = self.client.patch(
            f"/inventory/{created['id']}",
            json={"barcode": "999"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["external_details"]["product_name"], "Updated Item"
        )


if __name__ == "__main__":
    unittest.main()