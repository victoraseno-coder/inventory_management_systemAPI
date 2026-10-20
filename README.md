# inventory_management_systemAPI

This project is a Flask-based Inventory Management API that supports CRUD operations for inventory items, integrates with the OpenFoodFacts API to retrieve product information, and includes a Python CLI client for interacting with the API.

Features
Create, read, update, and delete inventory items
Retrieve product information from the OpenFoodFacts API using a product name or barcode
Import a product from OpenFoodFacts straight into the inventory
Interact with the API through a Python CLI
Unit tests covering the API, the CLI, and the external API client
Prerequisites
Python 3.x
pip
Installation
Clone the repository.

Navigate to the project directory:

cd inventory-management-api
Create a virtual environment:
python3 -m venv venv
Activate the virtual environment:
source venv/bin/activate
Install the project dependencies:
pip install -r requirements.txt
Running the API
With the virtual environment activated, start the Flask application:

python app.py
The API will be available at:http://127.0.0.1:5000Inventory is stored in a Python array that is loaded at startup from inventory.json, so changes last only as long as the server is running.

API Endpoints
Method Endpoint Description
GET /health Health check
GET /inventory Retrieve all inventory items
POST /inventory Create a new inventory item
GET /inventory/<id> Retrieve a single inventory item
PATCH /inventory/<id> Update an inventory item
DELETE /inventory/<id> Delete an inventory item
GET /products/lookup Lookup product details by name or barcode
POST /inventory/import Fetch a product from OpenFoodFacts and add it to the inventory
Using the CLI
python cli.py list
python cli.py view 1
python cli.py add --name "Milk" --quantity 10 --price 2.50
python cli.py update 1 --quantity 15
python cli.py delete 1
python cli.py lookup --query "banana"
python cli.py import --barcode 3017620422003 --quantity 6 --price 5.49
Example API Requests
Create an item:

curl -X POST http://127.0.0.1:5000/inventory \
 -H "Content-Type: application/json" \
 -d '{"name":"Milk","quantity":10,"price":2.50}'
Get all items:

curl http://127.0.0.1:5000/inventory
Update an item:

curl -X PATCH http://127.0.0.1:5000/inventory/1 \
 -H "Content-Type: application/json" \
 -d '{"quantity":15}'
Running the Tests
python -m pytest -q
All external calls are mocked, so the tests run offline and never contact OpenFoodFacts.

Project Structure
inventory-management-api/ ├── app.py ├── cli.py ├── inventory.json ├── requirements.txt ├── README.md └── tests/
