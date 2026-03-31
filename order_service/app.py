from flask import Flask, request, render_template_string
from redis import Redis
import socket
import requests

app = Flask(__name__)

# Shared database
db = Redis(host="shop_db", port=6379, decode_responses=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Microservice Shop</title>
    <style>
        body { font-family: sans-serif; padding: 40px; background: #f4f7f6; }
        .container { background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: auto; }
        h1 { color: #333; }
        .info { font-size: 0.9em; color: #666; margin-bottom: 20px; }
        select, button { padding: 10px; font-size: 16px; margin-top: 10px; }
        button { background-color: #28a745; color: white; border: none; cursor: pointer; }
        button:hover { background-color: #218838; }
        ul { background: #eee; padding: 20px; border-radius: 5px; list-style-type: none; }
        li { border-bottom: 1px solid #ddd; padding: 5px 0; }
        .link { margin-top: 20px; display: block; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Checkout Service</h1>
        <div class="info">
            Service Instance: <b>{{ container_id }}</b><br/>
            Database: <b>shop_db (Shared Redis)</b>
        </div>

        <form method="POST" action="/order/submit">
            <h3>Select a Product:</h3>
            <table>
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Stock</th>
                    <th>Price</th>
                </tr>
            </thead>
            <tbody>
            {% for key in ["sku:001", "sku:002", "sku:003"] %}
            <tr>
            <td>
            <td><input type="checkbox" name="sku" value="{{ key }}"></td>
                <td>{{ db.hget(key, "name") }}</td>
                <td>{{ db.hget(key, "stock") }}</td>
                <td>${{ db.hget(key, "price") }}</td>
            {% endfor %}
            </tbody>
            </table>
            </select>
            <br/><br/>
            <button type="submit" style="width: 100%;">Buy Now (Place Order)</button>
        </form>

        <h3>Order History</h3>
        <ul>
            {% for log in logs %}
                <li>{{ log }}</li>
            {% else %}
                <li>No orders yet.</li>
            {% endfor %}
        </ul>

        <a class="link" href="/product/" target="_blank">View Inventory (Product Service)</a>
    </div>
</body>
</html>
"""



# Update Order Service to support phone price.
# • Create a new Money Service for:
# o initializing the balance
# o checking the current balance
# o deducting money after an order
# • Update Order Service so that a successful order reduces the balance.
# • Update docker-compose.yml to include the new service.
# • Update Nginx routing if needed.
# • Update the front-end page to show:
# o phone prices
# o current balance

@app.route("/")
def index():
    logs = db.lrange("order_history", 0, 4)
    container_id = socket.gethostname()
    return render_template_string(HTML_TEMPLATE, logs=logs, container_id=container_id)


@app.route("/submit", methods=["POST"])
def submit_order():
    sku = request.form["sku"]

    try:
        response = requests.post("http://product_app:5000/reduce_stock", json={"sku": sku})
        data = response.json()

        if response.status_code == 200 and data["success"]:
            order_id = db.incr("order_id_counter")
            log_message = f"Order #{order_id}: {data['product_name']} (Stock left: {data['new_stock']}, Balance after purchase: {data['new_balance']})"
            db.lpush("order_history", log_message)
            return f"<h2>Order Successful!</h2><p>{log_message}</p><a href='/order/'>Back</a>"
        else:
            reason = data.get("message", "Unknown Error")
            return f"<h2>Order Failed</h2><p>Reason: {reason}</p><a href='/order/'>Back</a>"

    except Exception as e:
        return f"<h2>System Error</h2><p>Could not connect to Product Service.<br/>Error: {str(e)}</p><a href='/order/'>Back</a>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
