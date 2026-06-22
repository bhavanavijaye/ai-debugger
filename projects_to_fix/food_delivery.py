import flask
from flask import request, jsonify
import logging
import uuid
from flask.logging import default_handler
import socket

app = flask.Flask(__name__)
app.config['DEBUG'] = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.addHandler(default_handler)

restaurants = [
    {"id": 1, "name": "Pizza Palace", "rating": 4.5},
    {"id": 2, "name": "Burger King", "rating": 4.2}
]

orders = {}

@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    try:
        return jsonify(restaurants)
    except Exception as e:
        logger.error(f"Error getting restaurants: {str(e)}")
        return {"error": str(e)}, 500

@app.route('/order', methods=['POST'])
def place_order():
    try:
        data = request.get_json()
        if not data:
            logger.error("No data provided")
            return {"error": "No data"}, 400
        
        if "restaurant" not in data or "items" not in data:
            logger.error("Missing required fields")
            return {"error": "Missing required fields"}, 400
        
        if not isinstance(data["restaurant"], int):
            logger.error("Invalid restaurant ID")
            return {"error": "Invalid restaurant ID"}, 400
        
        for item in data["items"]:
            if "price" not in item or "id" not in item:
                logger.error("Missing price or id in items")
                return {"error": "Missing price or id in items"}, 400
        
        valid_restaurant = next((r for r in restaurants if r["id"] == data["restaurant"]), None)
        if not valid_restaurant:
            logger.error("Invalid restaurant ID")
            return {"error": "Invalid restaurant ID"}, 400
        
        for item in data["items"]:
            if item["price"] < 0:
                logger.error("Invalid item price")
                return {"error": "Invalid item price"}, 400
        
        if not data["items"]:
            logger.error("No items in the order")
            return {"error": "No items in the order"}, 400
        
        order_id = str(uuid.uuid4().int)
        order = {
            "id": order_id,
            "restaurant": data["restaurant"],
            "items": data["items"],
            "total": sum(item["price"] for item in data["items"]),
            "status": "pending"
        }
        orders[order_id] = order
        logger.info(f"Order placed: {order_id}")
        return jsonify(order), 201
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}")
        return {"error": str(e)}, 500

@app.route('/order/<string:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        order = orders.get(order_id)
        if not order:
            logger.error(f"Order not found: {order_id}")
            return {"error": "Order not found"}, 404
        logger.info(f"Order status retrieved: {order_id}")
        return jsonify(order)
    except Exception as e:
        logger.error(f"Error getting order status: {str(e)}")
        return {"error": str(e)}, 500

def get_available_port():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("", 0))
        port = sock.getsockname()[1]
        sock.close()
        return port
    except Exception as e:
        logger.error(f"Error getting available port: {str(e)}")
        return None

if __name__ == '__main__':
    port = get_available_port()
    if port:
        logger.info(f"Server running on port {port}")
        app.run(port=port)
    else:
        logger.error("Failed to get available port")