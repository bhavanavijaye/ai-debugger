import flask
from flask import request
import uuid
import json

app = flask.Flask(__name__)

# In-memory order storage (replace with a database in production)
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
        return {"error": str(e)}, 500

# Place an order
@app.route('/order', methods=['POST'])
def place_order():
    try:
        data = request.get_json()
        if not data:
            return {"error": "No data"}, 400
        
        if "restaurant" not in data or "items" not in data:
            return {"error": "Missing required fields"}, 400
        
        if not isinstance(data["items"], list) or len(data["items"]) == 0:
            return {"error": "Invalid items"}, 400
        
        restaurant_id = data["restaurant"]
        if not any(restaurant["id"] == restaurant_id for restaurant in restaurants):
            return {"error": "Invalid restaurant"}, 400
        
        total = 0
        for item in data["items"]:
            if "price" not in item:
                return {"error": "Invalid item price"}, 400
            if not isinstance(item["price"], (int, float)) or item["price"] < 0:
                return {"error": "Invalid item price"}, 400
            total += item["price"]
        
        order_id = str(uuid.uuid4())
        order = {
            "id": order_id,
            "restaurant": restaurant_id,
            "items": data["items"],
            "total": total,
            "status": "pending"
        }
        orders[order_id] = order
        return flask.jsonify(order), 201
    except Exception as e:
        return {"error": str(e)}, 500

# Get order status
@app.route('/order/<string:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        if order_id not in orders:
            return {"error": "Order not found"}, 404
        order = orders[order_id]
        return {"id": order_id, "status": order["status"]}
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)