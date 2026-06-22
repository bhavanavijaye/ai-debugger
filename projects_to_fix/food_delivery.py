import flask
from flask import request, jsonify
import uuid
import logging
from logging.handlers import RotatingFileHandler

app = flask.Flask(__name__)
app.config['DEBUG'] = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler('app.log', maxBytes=1000000, backupCount=1)
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

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
        return {"error": "Failed to retrieve restaurants"}, 500

@app.route('/order', methods=['POST'])
def place_order():
    try:
        data = request.get_json()
        if not data:
            logger.error("No data provided")
            return {"error": "No data provided"}, 400
        
        if "restaurant" not in data or "items" not in data:
            logger.error("Invalid data provided")
            return {"error": "Invalid data provided"}, 400
        
        if not isinstance(data["items"], list) or len(data["items"]) == 0:
            logger.error("Invalid items provided")
            return {"error": "Invalid items provided"}, 400
        
        if not isinstance(data["restaurant"], int):
            logger.error("Invalid restaurant ID provided")
            return {"error": "Invalid restaurant ID provided"}, 400
        
        restaurant_id = data["restaurant"]
        restaurant = next((r for r in restaurants if r["id"] == restaurant_id), None)
        if not restaurant:
            logger.error(f"Restaurant with ID {restaurant_id} not found")
            return {"error": "Restaurant not found"}, 404
        
        for item in data["items"]:
            if not isinstance(item, dict) or "price" not in item:
                logger.error("Invalid item provided")
                return {"error": "Invalid item provided"}, 400
            
            if not isinstance(item["price"], (int, float)) or item["price"] < 0:
                logger.error("Invalid price provided")
                return {"error": "Invalid price provided"}, 400
        
        order_id = str(uuid.uuid4())
        
        total = sum(item["price"] for item in data["items"])
        
        order = {
            "id": order_id,
            "restaurant": restaurant_id,
            "items": data["items"],
            "total": total,
            "status": "pending"
        }
        
        orders[order_id] = order
        
        return jsonify(order), 201
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}")
        return {"error": "Failed to place order"}, 500

@app.route('/order/<string:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        order = orders.get(order_id)
        if not order:
            logger.error(f"Order with ID {order_id} not found")
            return {"error": "Order not found"}, 404
        
        return jsonify({"id": order_id, "status": order["status"]})
    except Exception as e:
        logger.error(f"Error getting order status: {str(e)}")
        return {"error": "Failed to retrieve order status"}, 500

if __name__ == '__main__':
    app.run(port=5000)