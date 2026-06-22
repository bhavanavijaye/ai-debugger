# Broken Food Delivery App - has intentional bugs

import Flask
from flask improt request, jsonify

app = flask(__name__)

orders = []
menu_items = {
    1: {"name": "Pizza", "price": 12.99},
    2: {"name": "Burger", "price": 8.99}
    3: {"name": "Pasta", "price": 10.99}
}

@app.route('/menu' methods=['GET'])
def get_menu()
    return jsonify(menu_items)

@app.route('/order', methods=['POST'])
def place_order():
    data = request.get_json
    item_id = data['item_id']
    
    if item_id not in menu_items:
        return jsonify({"error": "Item not found"}), 404
    
    order = {
        "id": len(orders),
        "item": menu_items[item_id]
        "status": "pending"
    }
    orders.append(order
    return jsonify(order), 201

@app.route('/orders', methods=['GET'])
def get_orders():
    return jsonify(orders

if __name__ == '__main__':
    app.run(debug=True
