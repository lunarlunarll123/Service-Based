from flask import Flask, request, render_template_string, jsonify
from redis import Redis
import socket
import requests

app = Flask(__name__)

# Shared database
db = Redis(host="shop_db", port=6379, decode_responses=True)

SKUS = ["sku:001", "sku:002", "sku:003"]

PRODUCT_ICONS = {
    "sku:001": "📱",
    "sku:002": "💻",
    "sku:003": "🎮",
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TechShop — Microservice Store</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 30px 20px;
        }

        .page { max-width: 860px; margin: 0 auto; }

        /* ── Header ── */
        .header { text-align: center; color: white; margin-bottom: 28px; }
        .header h1 { font-size: 2.4em; font-weight: 800; letter-spacing: -1px; }
        .header p  { opacity: .8; margin-top: 6px; font-size: 1em; }
        .chips { display: flex; justify-content: center; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
        .chip {
            background: rgba(255,255,255,.2);
            color: white;
            padding: 5px 14px;
            border-radius: 20px;
            font-size: .8em;
        }

        /* ── Cards ── */
        .card {
            background: white;
            border-radius: 18px;
            padding: 28px;
            margin-bottom: 22px;
            box-shadow: 0 12px 40px rgba(0,0,0,.14);
        }
        .card-title {
            font-size: 1.1em;
            font-weight: 700;
            color: #333;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* ── Balance Card ── */
        .balance-card {
            background: linear-gradient(135deg, #059669, #34d399);
            border-radius: 18px;
            padding: 28px 32px;
            margin-bottom: 22px;
            box-shadow: 0 12px 40px rgba(0,0,0,.14);
            color: white;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .balance-label { font-size: .8em; text-transform: uppercase; letter-spacing: 1px; opacity: .85; }
        .balance-amount { font-size: 2.8em; font-weight: 800; margin-top: 2px; }
        .balance-sub { font-size: .8em; opacity: .75; margin-top: 4px; }
        .balance-icon { font-size: 3.5em; opacity: .4; }

        /* ── Product Table ── */
        table { width: 100%; border-collapse: collapse; }
        thead th {
            text-align: left;
            padding: 10px 14px;
            background: #f8f9fa;
            color: #777;
            font-size: .75em;
            text-transform: uppercase;
            letter-spacing: .6px;
            border-bottom: 2px solid #eee;
        }
        tbody td { padding: 14px; border-bottom: 1px solid #f2f2f2; vertical-align: middle; }
        tbody tr:last-child td { border-bottom: none; }
        tbody tr { transition: background .15s; }
        tbody tr:hover td { background: #fafafa; }
        tbody tr.selected-row td { background: #f5f3ff; }

        .prod-cell { display: flex; align-items: center; gap: 10px; }
        .prod-icon { font-size: 1.8em; }
        .prod-name { font-weight: 600; color: #222; }

        .badge {
            display: inline-block;
            padding: 3px 11px;
            border-radius: 20px;
            font-size: .78em;
            font-weight: 600;
        }
        .badge-ok    { background: #ecfdf5; color: #065f46; }
        .badge-low   { background: #fff7ed; color: #9a3412; }
        .badge-empty { background: #fef2f2; color: #991b1b; }

        .price { font-weight: 700; color: #7c3aed; font-size: 1.05em; }

        .sel-btn {
            padding: 8px 18px;
            border: 2px solid #e5e7eb;
            border-radius: 9px;
            background: white;
            color: #555;
            font-size: .88em;
            font-weight: 600;
            cursor: pointer;
            transition: all .18s;
        }
        .sel-btn:hover:not(:disabled) { border-color: #7c3aed; color: #7c3aed; }
        .sel-btn.active { background: #7c3aed; border-color: #7c3aed; color: white; }
        .sel-btn:disabled { opacity: .4; cursor: not-allowed; }

        input[type=radio] { display: none; }

        /* ── Buy Button ── */
        .buy-btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #7c3aed, #4f46e5);
            color: white;
            border: none;
            border-radius: 13px;
            font-size: 1.05em;
            font-weight: 700;
            cursor: pointer;
            margin-top: 22px;
            letter-spacing: .4px;
            transition: all .2s;
            box-shadow: 0 4px 14px rgba(124,58,237,.3);
        }
        .buy-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(124,58,237,.45); }
        .buy-btn:active { transform: translateY(0); }

        /* ── Order History ── */
        .order-list { list-style: none; }
        .order-item {
            padding: 11px 16px;
            background: #f8f9fa;
            border-radius: 9px;
            margin-bottom: 8px;
            font-size: .88em;
            color: #444;
            border-left: 3px solid #7c3aed;
        }
        .order-empty { color: #aaa; text-align: center; padding: 24px; font-size: .9em; }

        /* ── AI Chat ── */
        .chat-box {
            border: 1.5px solid #e5e7eb;
            border-radius: 14px;
            height: 240px;
            overflow-y: auto;
            padding: 16px;
            background: #fafafa;
            margin-bottom: 14px;
            scroll-behavior: smooth;
        }
        .msg { margin-bottom: 14px; overflow: hidden; }
        .bubble {
            display: inline-block;
            padding: 9px 14px;
            border-radius: 14px;
            max-width: 80%;
            font-size: .9em;
            line-height: 1.45;
            word-wrap: break-word;
        }
        .msg.user  { text-align: right; }
        .msg.user  .bubble { background: #7c3aed; color: white; border-radius: 14px 14px 3px 14px; }
        .msg.ai    .bubble { background: white; border: 1.5px solid #e5e7eb; color: #333; border-radius: 14px 14px 14px 3px; }
        .typing { color: #aaa; font-style: italic; }

        .chat-row { display: flex; gap: 8px; }
        .chat-input {
            flex: 1;
            padding: 10px 15px;
            border: 1.5px solid #e5e7eb;
            border-radius: 11px;
            font-size: .93em;
            outline: none;
            transition: border-color .15s;
        }
        .chat-input:focus { border-color: #7c3aed; }
        .chat-send {
            padding: 10px 20px;
            background: #7c3aed;
            color: white;
            border: none;
            border-radius: 11px;
            font-weight: 700;
            cursor: pointer;
            font-size: .93em;
            transition: background .15s;
        }
        .chat-send:hover { background: #6d28d9; }

        /* ── Inventory Link ── */
        .inventory-link {
            display: block;
            text-align: center;
            margin-top: 8px;
            color: #7c3aed;
            font-size: .9em;
            font-weight: 600;
            text-decoration: none;
        }
        .inventory-link:hover { text-decoration: underline; }

        @media (max-width: 560px) {
            .balance-amount { font-size: 2em; }
            .balance-icon   { display: none; }
            .header h1      { font-size: 1.7em; }
        }
    </style>
</head>
<body>
<div class="page">

    <!-- Header -->
    <div class="header">
        <h1>🛒 TechShop</h1>
        <p>Microservice-Powered Electronics Store</p>
        <div class="chips">
            <span class="chip">Instance: {{ container_id }}</span>
            <span class="chip">DB: shop_db (Shared Redis)</span>
        </div>
    </div>

    <!-- Balance -->
    <div class="balance-card">
        <div>
            <div class="balance-label">Available Balance</div>
            <div class="balance-amount">${{ balance }}</div>
            <div class="balance-sub">Managed by Money Service</div>
        </div>
        <div class="balance-icon">💰</div>
    </div>

    <!-- Products -->
    <div class="card">
        <div class="card-title">🛍️ Select a Product</div>
        <form method="POST" action="/order/submit" id="orderForm">
            <table>
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Stock</th>
                        <th>Price</th>
                        <th>Select</th>
                    </tr>
                </thead>
                <tbody>
                {% for prod in products %}
                <tr id="row-{{ prod.sku }}" class="">
                    <td>
                        <div class="prod-cell">
                            <span class="prod-icon">{{ prod.icon }}</span>
                            <span class="prod-name">{{ prod.name }}</span>
                        </div>
                    </td>
                    <td>
                        {% if prod.stock == 0 %}
                            <span class="badge badge-empty">Out of Stock</span>
                        {% elif prod.stock <= 3 %}
                            <span class="badge badge-low">{{ prod.stock }} left</span>
                        {% else %}
                            <span class="badge badge-ok">{{ prod.stock }} in stock</span>
                        {% endif %}
                    </td>
                    <td><span class="price">${{ prod.price }}</span></td>
                    <td>
                        <input type="radio" name="sku" value="{{ prod.sku }}" id="r_{{ prod.sku }}"
                               {% if prod.stock == 0 %}disabled{% endif %}>
                        <button type="button"
                                class="sel-btn"
                                id="btn-{{ prod.sku }}"
                                onclick="selectProduct('{{ prod.sku }}')"
                                {% if prod.stock == 0 %}disabled{% endif %}>
                            Select
                        </button>
                    </td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
            <button type="submit" class="buy-btn">🛒 Place Order</button>
        </form>
        <a class="inventory-link" href="/product/" target="_blank">View Raw Inventory (Product Service) →</a>
    </div>

    <!-- Order History -->
    <div class="card">
        <div class="card-title">📋 Recent Orders</div>
        <ul class="order-list">
            {% for log in logs %}
                <li class="order-item">{{ log }}</li>
            {% else %}
                <p class="order-empty">No orders placed yet. Buy something!</p>
            {% endfor %}
        </ul>
    </div>

    <!-- AI Shopping Assistant -->
    <div class="card">
        <div class="card-title" style="color:#7c3aed;">🤖 AI Shopping Assistant</div>
        <div class="chat-box" id="chatBox">
            <div class="msg ai">
                <div class="bubble">
                    Hi! I'm your local AI shopping assistant (Llama 3.2). Ask me anything — product recommendations, budget advice, or comparisons! 🛍️
                </div>
            </div>
        </div>
        <div class="chat-row">
            <input  class="chat-input"
                    id="chatInput"
                    type="text"
                    placeholder="e.g. What should I buy with my budget?"
                    onkeydown="if(event.key==='Enter') sendChat()">
            <button class="chat-send" onclick="sendChat()">Send</button>
        </div>
    </div>

</div>

<script>
    function selectProduct(sku) {
        // Reset all rows/buttons
        document.querySelectorAll('tbody tr').forEach(row => row.classList.remove('selected-row'));
        document.querySelectorAll('.sel-btn').forEach(b => {
            b.classList.remove('active');
            b.textContent = 'Select';
        });

        const radio = document.getElementById('r_' + sku);
        if (!radio || radio.disabled) return;

        radio.checked = true;
        document.getElementById('btn-' + sku).classList.add('active');
        document.getElementById('btn-' + sku).textContent = '✓ Selected';
        document.getElementById('row-' + sku).classList.add('selected-row');
    }

    document.getElementById('orderForm').addEventListener('submit', function(e) {
        if (!document.querySelector('input[name="sku"]:checked')) {
            e.preventDefault();
            alert('Please select a product first!');
        }
    });

    async function sendChat() {
        const input = document.getElementById('chatInput');
        const msg = input.value.trim();
        if (!msg) return;
        input.value = '';

        appendMsg('user', msg);
        const typingEl = appendMsg('ai', '...', true);

        try {
            const res = await fetch('/order/ai_chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg })
            });
            const data = await res.json();
            typingEl.querySelector('.bubble').textContent = data.reply;
            typingEl.querySelector('.bubble').classList.remove('typing');
        } catch (err) {
            typingEl.querySelector('.bubble').textContent = 'Sorry, the AI assistant is unavailable right now.';
            typingEl.querySelector('.bubble').classList.remove('typing');
        }
        scrollChat();
    }

    function appendMsg(role, text, isTyping = false) {
        const box  = document.getElementById('chatBox');
        const div  = document.createElement('div');
        div.className = 'msg ' + role;
        const bub  = document.createElement('div');
        bub.className = 'bubble' + (isTyping ? ' typing' : '');
        bub.textContent = text;
        div.appendChild(bub);
        box.appendChild(div);
        scrollChat();
        return div;
    }

    function scrollChat() {
        const box = document.getElementById('chatBox');
        box.scrollTop = box.scrollHeight;
    }
</script>
</body>
</html>
"""


def get_products_from_db():
    products = []
    for sku in SKUS:
        p = db.hgetall(sku)
        if p:
            products.append({
                "sku": sku,
                "name": p.get("name", sku),
                "stock": int(p.get("stock", 0)),
                "price": p.get("price", "?"),
                "icon": PRODUCT_ICONS.get(sku, "📦"),
            })
    return products


@app.route("/")
def index():
    logs = db.lrange("order_history", 0, 4)
    container_id = socket.gethostname()
    products = get_products_from_db()

    # Read balance directly from shared Redis — same DB, no HTTP round-trip needed
    raw = db.get("balance")
    if raw is None:
        db.set("balance", 10000)
        raw = "10000"
    balance = int(raw)

    return render_template_string(
        HTML_TEMPLATE,
        logs=logs,
        container_id=container_id,
        balance=balance,
        products=products,
    )


@app.route("/submit", methods=["POST"])
def submit_order():
    sku = request.form.get("sku")
    if not sku:
        return _result_page(False, "Please select a product first.")

    try:
        response = requests.post(
            "http://product_app:5000/reduce_stock",
            json={"sku": sku, "quantity": 1}
        )
        data = response.json()

        if response.status_code == 200 and data["success"]:
            order_id = db.incr("order_id_counter")
            log = (
                f"Order #{order_id}: {data['product_name']} — "
                f"${data['price_paid']} paid | "
                f"Stock left: {data['new_stock']} | "
                f"Balance: ${data['new_balance']}"
            )
            db.lpush("order_history", log)
            db.ltrim("order_history", 0, 9)
            return _result_page(True, log)
        else:
            return _result_page(False, data.get("message", "Unknown error"))

    except Exception as e:
        return _result_page(False, f"Could not reach Product Service: {e}")


def _result_page(success, message):
    icon  = "✅" if success else "❌"
    color = "#059669" if success else "#dc2626"
    title = "Order Successful!" if success else "Order Failed"
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .box {{
            background: white;
            padding: 44px 40px;
            border-radius: 18px;
            text-align: center;
            max-width: 420px;
            width: 100%;
            box-shadow: 0 16px 48px rgba(0,0,0,.2);
        }}
        .icon {{ font-size: 3em; margin-bottom: 14px; }}
        h2 {{ color: {color}; margin-bottom: 14px; font-size: 1.4em; }}
        p  {{ color: #555; font-size: .95em; line-height: 1.5; }}
        a  {{
            display: inline-block;
            margin-top: 24px;
            color: white;
            background: #7c3aed;
            padding: 12px 28px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 700;
            transition: background .15s;
        }}
        a:hover {{ background: #6d28d9; }}
    </style>
    </head><body>
    <div class="box">
        <div class="icon">{icon}</div>
        <h2>{title}</h2>
        <p>{message}</p>
        <a href="/order/">← Back to Shop</a>
    </div>
    </body></html>
    """


OLLAMA_CHAT_URL = "http://ollama:11434/api/chat"
OLLAMA_MODEL = "llama3.2:1b"


@app.route("/ai_chat", methods=["POST"])
def ai_chat():
    user_message = request.get_json(force=True).get("message", "")
    if not user_message:
        return jsonify({"reply": "Please send a message."}), 400

    # Build live shop context from shared Redis
    products = get_products_from_db()
    product_lines = "\n".join(
        f"- {p['name']}: ${p['price']}, {p['stock']} in stock"
        for p in products
    )
    raw = db.get("balance")
    balance = int(raw) if raw else 10000

    system_prompt = (
        f"You are a helpful shopping assistant for TechShop. "
        f"Reply in 1-3 sentences. Be direct and friendly. No roleplay or dialogue format.\n\n"
        f"Current inventory:\n{product_lines}\n"
        f"Customer balance: ${balance}"
    )

    try:
        resp = requests.post(
            OLLAMA_CHAT_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message},
                ],
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 150},
            },
            timeout=60,
        )
        if resp.status_code == 404:
            reply = "Model is still downloading — please wait a moment and try again!"
        elif resp.status_code != 200:
            reply = f"Ollama returned status {resp.status_code}."
        else:
            reply = resp.json().get("message", {}).get("content", "").strip()
            if not reply:
                reply = "I'm not sure — try asking again!"
    except requests.exceptions.ConnectionError:
        reply = "AI assistant is still starting up — please try again in a moment!"
    except Exception as e:
        reply = f"AI error: {str(e)[:100]}"

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
