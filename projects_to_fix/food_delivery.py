import flask
from flask import request
import logging
import uuid
import json
import socket

app = flask.Flask(__name__)
app.config['DEBUG'] = False

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.INFO)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a formatter and set the formatter for the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# In-memory data store for orders and restaurants
orders = {}
restaurants = [
    {"id": 1, "name": "Pizza Palace", "rating": 4.5},
    {"id": 2, "name": "Burger King", "rating": 4.2}
]

# Get all restaurants
@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    try:
        return flask.jsonify(restaurants)
    except Exception as e:
        logger.error(f"Error getting restaurants: {str(e)}")
        return {"error": str(e)}, 500

# Place an order
@app.route('/order', methods=['POST'])
def place_order():
    try:
        data = request.get_json()
        if not data:
            logger.error("No data provided")
            return {"error": "No data"}, 400
        
        if "restaurant" not in data or "items" not in data:
            logger.error("Invalid data")
            return {"error": "Invalid data"}, 400
        
        if not isinstance(data["items"], list):
            logger.error("Invalid items")
            return {"error": "Invalid items"}, 400
        
        # Validate restaurant ID
        restaurant_id = data["restaurant"]
        if not any(restaurant["id"] == restaurant_id for restaurant in restaurants):
            logger.error(f"Invalid restaurant ID: {restaurant_id}")
            return {"error": "Invalid restaurant ID"}, 400
        
        # Validate items
        for item in data["items"]:
            if "price" not in item:
                logger.error("Item is missing price")
                return {"error": "Item is missing price"}, 400
        
        # Generate unique order ID
        order_id = str(uuid.uuid4())
        
        # Calculate total
        total = sum(item["price"] for item in data["items"])
        
        # Create order
        order = {
            "id": order_id,
            "restaurant": data["restaurant"],
            "items": data["items"],
            "total": total,
            "status": "pending"
        }
        
        # Store order
        orders[order_id] = order
        
        return flask.jsonify(order), 201
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}")
        return {"error": str(e)}, 500

# Get order status
@app.route('/order/<string:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        if order_id not in orders:
            logger.error(f"Order not found: {order_id}")
            return {"error": "Order not found"}, 404
        
        order = orders[order_id]
        return flask.jsonify({"id": order_id, "status": order["status"]})
    except Exception as e:
        logger.error(f"Error getting order: {str(e)}")
        return {"error": str(e)}, 500

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if __name__ == '__main__':
    port = 5000
    while is_port_in_use(port):
        logger.error(f"Port {port} is in use. Trying port {port + 1}.")
        port += 1
    app.run(port=port)