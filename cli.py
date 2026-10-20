import argparse
import json

import requests


BASE_URL = "http://127.0.0.1:5000"


def request_data(method, path, payload=None, params=None):
    """Call the API and return the parsed body.

    Any network or HTTP failure is reported and exits, so each command can
    assume it received usable data.
    """
    try:
        if payload is None:
            response = method(BASE_URL + path, params=params)
        else:
            response = method(BASE_URL + path, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print("API error:", exc)
        raise SystemExit(1)


def list_inventory():
    data = request_data(requests.get, "/inventory")
    print(json.dumps(data, indent=2))


def view_item(item_id):
    data = request_data(requests.get, f"/inventory/{item_id}")
    print(json.dumps(data, indent=2))


def add_item(name, quantity, price, barcode=None):
    payload = {"name": name, "quantity": quantity, "price": price}
    if barcode:
        payload["barcode"] = barcode
    data = request_data(requests.post, "/inventory", payload)
    print(json.dumps(data, indent=2))


def update_item(item_id, quantity=None, price=None, name=None):
    payload = {}
    if name is not None:
        payload["name"] = name
    if quantity is not None:
        payload["quantity"] = quantity
    if price is not None:
        payload["price"] = price

    if not payload:
        print("Please provide something to update")
        raise SystemExit(1)

    data = request_data(requests.patch, f"/inventory/{item_id}", payload)
    print(json.dumps(data, indent=2))


def delete_item(item_id):
    data = request_data(requests.delete, f"/inventory/{item_id}")
    print(json.dumps(data, indent=2))


def lookup_product(query=None, barcode=None):
    if not query and not barcode:
        print("Please provide a product name or barcode")
        raise SystemExit(1)

    params = {}
    if query:
        params["query"] = query
    if barcode:
        params["barcode"] = barcode

    data = request_data(requests.get, "/products/lookup", params=params)
    print(json.dumps(data, indent=2))


def import_item(query=None, barcode=None, quantity=0, price=0.0):
    """Fetch a product from OpenFoodFacts and store it in the inventory."""
    if not query and not barcode:
        print("Please provide a product name or barcode")
        raise SystemExit(1)

    payload = {"quantity": quantity, "price": price}
    if query:
        payload["query"] = query
    if barcode:
        payload["barcode"] = barcode

    data = request_data(requests.post, "/inventory/import", payload)
    print(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Simple inventory CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="Show every item in the inventory")

    view_parser = subparsers.add_parser("view", help="Show one item")
    view_parser.add_argument("item_id", type=int)

    add_parser = subparsers.add_parser("add", help="Add an item to the inventory")
    add_parser.add_argument("--name", required=True)
    add_parser.add_argument("--quantity", type=int, default=0)
    add_parser.add_argument("--price", type=float, default=0.0)
    add_parser.add_argument("--barcode")

    update_parser = subparsers.add_parser("update", help="Change stock or price")
    update_parser.add_argument("item_id", type=int)
    update_parser.add_argument("--name")
    update_parser.add_argument("--quantity", type=int)
    update_parser.add_argument("--price", type=float)

    delete_parser = subparsers.add_parser("delete", help="Remove an item")
    delete_parser.add_argument("item_id", type=int)

    lookup_parser = subparsers.add_parser("lookup", help="Search OpenFoodFacts")
    lookup_parser.add_argument("--query")
    lookup_parser.add_argument("--barcode")

    import_parser = subparsers.add_parser(
        "import", help="Fetch from OpenFoodFacts and add to the inventory"
    )
    import_parser.add_argument("--query")
    import_parser.add_argument("--barcode")
    import_parser.add_argument("--quantity", type=int, default=0)
    import_parser.add_argument("--price", type=float, default=0.0)

    args = parser.parse_args()

    if args.command == "list":
        list_inventory()
    elif args.command == "view":
        view_item(args.item_id)
    elif args.command == "add":
        add_item(args.name, args.quantity, args.price, args.barcode)
    elif args.command == "update":
        update_item(args.item_id, args.quantity, args.price, args.name)
    elif args.command == "delete":
        delete_item(args.item_id)
    elif args.command == "lookup":
        lookup_product(args.query, args.barcode)
    elif args.command == "import":
        import_item(args.query, args.barcode, args.quantity, args.price)


if __name__ == "__main__":
    main()