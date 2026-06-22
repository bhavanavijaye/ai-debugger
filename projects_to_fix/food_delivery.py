# Food Delivery App - Backend
import flask
from flask import request

app = flask.Flask(__name__

# Get all restaurants
@app.route('/restaurants' methods=['GET'])
def get_restaurants()
    restaurants = [
        {"id": 1, "name": "Pizza Palace" "rating": 4.5},
        {"id": 2, "name": "Burger King", "rating": 4.2}
    ]
    return flask.jsonify(restaurants

# Place an order
@app.route('/order', methods=['POST'])
def place_order()
    data = request.get_json(
    if not data
        return {"error": "No data"}, 400
    
    order = {
        "id": 1
        "restaurant": data["restaurant"]
        "items": data["items"]
        "total": sum(item["price"] for item in data["items"]
        "status": "pending"
    }
    return flask.jsonify(order), 201

# Get order status
@app.route('/order/<int:order_id>' methods=['GET'])
def get_order(order_id)
    return {"id": order_id, "status": "delivered"

if __name__ == '__main__'
    app.run(debug=True port=5000)
