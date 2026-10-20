import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

import cli


def build_response(payload):
    """A stand-in for a requests Response that always succeeds."""
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


class CliTests(unittest.TestCase):
    def run_command(self, function, *args, **kwargs):
        """Call a CLI function and capture whatever it printed."""
        output = io.StringIO()
        with redirect_stdout(output):
            function(*args, **kwargs)
        return output.getvalue()

    def test_list_inventory_prints_items(self):
        payload = [{"id": 1, "name": "Keyboard", "quantity": 5}]
        with patch("cli.requests.get", return_value=build_response(payload)):
            output = self.run_command(cli.list_inventory)

        self.assertIn("Keyboard", output)

    def test_view_item_requests_the_right_path(self):
        with patch("cli.requests.get", return_value=build_response({"id": 3})) as mock_get:
            self.run_command(cli.view_item, 3)

        self.assertIn("/inventory/3", mock_get.call_args.args[0])

    def test_add_item_sends_expected_payload(self):
        payload = {"id": 7, "name": "Mouse", "quantity": 2, "price": 15.0}
        with patch("cli.requests.post", return_value=build_response(payload)) as mock_post:
            output = self.run_command(cli.add_item, "Mouse", 2, 15.0, barcode="123")

        sent = mock_post.call_args.kwargs["json"]
        self.assertEqual(sent["name"], "Mouse")
        self.assertEqual(sent["barcode"], "123")
        self.assertIn("Mouse", output)

    def test_update_item_sends_patch_request(self):
        payload = {"id": 3, "name": "Monitor", "quantity": 4, "price": 200.0}
        with patch("cli.requests.patch", return_value=build_response(payload)) as mock_patch:
            output = self.run_command(cli.update_item, 3, quantity=4, price=200.0)

        sent = mock_patch.call_args.kwargs["json"]
        self.assertEqual(sent["quantity"], 4)
        self.assertEqual(sent["price"], 200.0)
        self.assertIn("Monitor", output)

    def test_update_with_nothing_to_change_exits(self):
        with self.assertRaises(SystemExit):
            self.run_command(cli.update_item, 3)

    def test_delete_item_reports_success(self):
        with patch("cli.requests.delete", return_value=build_response({"message": "Item deleted"})):
            output = self.run_command(cli.delete_item, 5)

        self.assertIn("Item deleted", output)

    def test_lookup_passes_the_search_terms(self):
        payload = {"product_name": "Nutella", "brands": "Ferrero"}
        with patch("cli.requests.get", return_value=build_response(payload)) as mock_get:
            output = self.run_command(cli.lookup_product, query="nutella")

        self.assertEqual(mock_get.call_args.kwargs["params"], {"query": "nutella"})
        self.assertIn("Nutella", output)

    def test_lookup_without_arguments_exits(self):
        with self.assertRaises(SystemExit):
            self.run_command(cli.lookup_product)

    def test_import_sends_the_barcode(self):
        payload = {"id": 2, "name": "Nutella"}
        with patch("cli.requests.post", return_value=build_response(payload)) as mock_post:
            output = self.run_command(cli.import_item, barcode="3017620422003", quantity=4)

        sent = mock_post.call_args.kwargs["json"]
        self.assertEqual(sent["barcode"], "3017620422003")
        self.assertEqual(sent["quantity"], 4)
        self.assertIn("Nutella", output)

    def test_import_without_arguments_exits(self):
        with self.assertRaises(SystemExit):
            self.run_command(cli.import_item)

    def test_api_failure_exits_with_a_message(self):
        with patch("cli.requests.get", side_effect=cli.requests.RequestException("boom")):
            output = io.StringIO()
            with redirect_stdout(output):
                with self.assertRaises(SystemExit):
                    cli.list_inventory()

        self.assertIn("API error", output.getvalue())


if __name__ == "__main__":
    unittest.main()