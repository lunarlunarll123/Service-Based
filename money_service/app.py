from flask import Flask, jsonify, request
from redis import Redis
import socket

app = Flask(__name__)

# Shared database
db = Redis(host="shop_db", port=6379, decode_responses=True)

# Balance key
balance_key = "balance"


def seed_money_if_needed():
    if db.exists(balance_key) == 0:
        db.set(balance_key, 10000)

def _get_balance():
    return int(db.get(balance_key))

@app.route("/")
def get_balance():
    seed_money_if_needed()

    balance = _get_balance()


    return jsonify({
        "service": "Money Service",
        "bounded_context": "Financial",
        "handled_by_instance": socket.gethostname(),
        "database": "shop_db (Shared Redis)",
        "data": {balance_key: balance}
    })


@app.route("/reduce_balance", methods=["POST"])
def reduce_balance():
    seed_money_if_needed()

    data = request.get_json()
    amount = data.get("amount")

    if not amount:
        return jsonify({"success": False, "message": "Amount is required"}), 400

    current_balance = _get_balance()
    result = current_balance - amount

    if amount <= 0:
        return jsonify({"success": False, "message": "Amount must be greater than zero"}), 400
    elif result < 0:
        return jsonify({"success": False, "message": "Insufficient funds"}), 400
    else:
        db.set(balance_key, result)
        return jsonify({
            "success": True,
            "new_balance": result,
        })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
