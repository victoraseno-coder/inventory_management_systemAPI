import json
import os

import requests
from flask import Flask, jsonify, request


app = Flask(__name__)

SEED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.json")
OPENFOODFACTS_URL = "https://world.openfoodfacts.org"
# OpenFoodFacts asks that clients identify themselves.
HEADERS = {"User-Agent": "InventoryManagementSystem/1.0 (educational project)"}
REQUEST_TIMEOUT = 10


def map_product(product):
    """Reduce an OpenFoodFacts product down to the fields the inventory keeps."""
    return {
        "product_name": product.get("product_name") or product.get("product_name_en"),
        "brands": product.get("brands"),
        "image_url": product.get("image_url"),
        "categories": product.get("categories"),
    }


def fetch_product_details(query=None, barcode=None):
    """Look a product up on OpenFoodFacts by barcode or name.

    Returns an empty dict on any failure so a lookup can never break a request.
    """
    try:
        if barcode:
            url = f"{OPENFOODFACTS_URL}/api/v2/product/{barcode}.json"
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            # OpenFoodFacts answers 200 with status 0 when the barcode is unknown.
            if data.get("status") == 1:
                return map_product(data.get("product", {}))
            return {}

        if query:
            url = f"{OPENFOODFACTS_URL}/cgi/search.pl"
            params = {
                "search_terms": query,
                "search_simple": 1,
                "action": "process",
                "json": 1,
            }
            response = requests.get(
                url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            products = response.json().get("products", [])
            if products:
                return map_product(products[0])
    except requests.RequestException:
        return {}
    except ValueError:
        # The response was not valid JSON.
        return {}
    return {}


def load_seed_data():
    """Build the starting inventory array from the OpenFoodFacts-shaped seed file."""
    try:
        with open(SEED_FILE, encoding="utf-8") as seed_file:
            records = json.load(seed_file)
    except (OSError, ValueError):
        return [], 1

    store = []
    for index, record in enumerate(records, start=1):
        product = record.get("product", {})
        store.append(
            {
                "id": index,
                "name": product.get("product_name"),
                "quantity": product.get("quantity", 0),
                "price": product.get("price", 0.0),
                "barcode": product.get("barcode"),
                "external_details": {
                    "product_name": product.get("product_name"),
                    "brands": product.get("brands"),
                    "ingredients_text": product.get("ingredients_text"),
                    "categories": product.get("categories"),
                },
            }
        )

    return store, len(store) + 1


def validate_payload(payload, require_name=True):
    """Check the fields a client can send. Returns an error string, or None."""
    if require_name:
        name = payload.get("name")
        if not name or not str(name).strip():
            return "Name is required"

    quantity = payload.get("quantity")
    if quantity is not None:
        if not isinstance(quantity, int) or isinstance(quantity, bool):
            return "Quantity must be a whole number"
        if quantity < 0:
            return "Quantity must not be negative"

    price = payload.get("price")
    if price is not None:
        if not isinstance(price, (int, float)) or isinstance(price, bool):
            return "Price must be a number"
        if price < 0:
            return "Price must not be negative"

    return None


def get_item_by_id(item_id):
    for item in app.config["STORE"]:
        if item["id"] == item_id:
            return item
    return None


app.config["STORE"], app.config["NEXT_ID"] = load_seed_data()


@app.get("/health")
def health_check():
    return jsonify({"status": "ok"})


@app.get("/inventory")
def get_inventory():
    return jsonify(app.config["STORE"])


@app.post("/inventory")
def create_item():
    payload = request.get_json(silent=True) or {}

    error = validate_payload(payload)
    if error:
        return jsonify({"error": error}), 400

    item = {
        "id": app.config["NEXT_ID"],
        "name": payload.get("name"),
        "quantity": payload.get("quantity", 0),
        "price": payload.get("price", 0.0),
        "barcode": payload.get("barcode"),
        # Only a barcode triggers a lookup, so adding an item by hand stays offline.
        "external_details": (
            fetch_product_details(barcode=payload["barcode"])
            if payload.get("barcode")
            else {}
        ),
    }

    app.config["STORE"].append(item)
    app.config["NEXT_ID"] += 1
    return jsonify(item), 201


@app.get("/inventory/<int:item_id>")
def get_item(item_id):
    item = get_item_by_id(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item)


@app.patch("/inventory/<int:item_id>")
def update_item(item_id):
    payload = request.get_json(silent=True) or {}
    item = get_item_by_id(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404

    error = validate_payload(payload, require_name=False)
    if error:
        return jsonify({"error": error}), 400

    # Only the fields present in the request body are touched.
    for key in ["name", "quantity", "price", "barcode"]:
        if key in payload:
            item[key] = payload[key]

    # A new barcode means the stored product details are stale.
    if payload.get("barcode"):
        item["external_details"] = fetch_product_details(barcode=payload["barcode"])

    return jsonify(item)


@app.delete("/inventory/<int:item_id>")
def delete_item(item_id):
    for index, item in enumerate(app.config["STORE"]):
        if item["id"] == item_id:
            app.config["STORE"].pop(index)
            return jsonify({"message": "Item deleted"})
    return jsonify({"error": "Item not found"}), 404


@app.get("/products/lookup")
def lookup_product():
    query = request.args.get("query", "").strip()
    barcode = request.args.get("barcode", "").strip()
    if not query and not barcode:
        return jsonify({"error": "Provide a barcode or product name"}), 400

    details = fetch_product_details(query=query or None, barcode=barcode or None)
    if not details:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(details)


@app.post("/inventory/import")
def import_item():
    """Look a product up on OpenFoodFacts and add it straight to the inventory."""
    payload = request.get_json(silent=True) or {}
    query = payload.get("query")
    barcode = payload.get("barcode")

    if not query and not barcode:
        return jsonify({"error": "Provide a barcode or product name"}), 400

    details = fetch_product_details(query=query, barcode=barcode)
    if not details:
        return jsonify({"error": "Product not found"}), 404

    item = {
        "id": app.config["NEXT_ID"],
        "name": details.get("product_name") or query,
        "quantity": payload.get("quantity", 0),
        "price": payload.get("price", 0.0),
        "barcode": barcode,
        "external_details": details,
    }

    app.config["STORE"].append(item)
    app.config["NEXT_ID"] += 1
    return jsonify(item), 201


def create_app():
    return app


if __name__ == "__main__":
    app.run(debug=True)