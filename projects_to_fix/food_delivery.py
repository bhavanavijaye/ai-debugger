import flask
from flask import request

app = flask.Flask(__name__)

# Get all restaurants
@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    try:
        restaurants = [
            {"id": 1, "name": "Pizza Palace", "rating": 4.5},
            {"id": 2, "name": "Burger King", "rating": 4.2}
        ]
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
        
        total = 0
        for item in data["items"]:
            if "price" not in item:
                return {"error": "Invalid item price"}, 400
            if not isinstance(item["price"], (int, float)) or item["price"] < 0:
                return {"error": "Invalid item price"}, 400
            total += item["price"]
        
        order = {
            "id": 1,
            "restaurant": data["restaurant"],
            "items": data["items"],
            "total": total,
            "status": "pending"
        }
        return flask.jsonify(order), 201
    except Exception as e:
        return {"error": str(e)}, 500

# Get order status
@app.route('/order/<int:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        return {"id": order_id, "status": "delivered"}
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)