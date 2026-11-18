"""
Flask Web Application for Retail Customer Segmentation & Churn Intelligence.
Provides REST APIs and serves the interactive dashboard UI.
"""

import os
from io import StringIO
from flask import Flask, render_template, jsonify, request, send_file, Response, make_response
import pandas as pd
from data_generator import generate_retail_dataset
from analytics_engine import RetailIntelligenceEngine

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "sample_transactions.csv")

# Global in-memory engine state
current_engine = None


def load_or_init_data():
    global current_engine
    if not os.path.exists(DATA_FILE):
        df = generate_retail_dataset()
        df.to_csv(DATA_FILE, index=False)
    else:
        df = pd.read_csv(DATA_FILE)
    
    current_engine = RetailIntelligenceEngine(df).process()
    return current_engine


@app.route("/")
@app.route("/simple")
def index_simple():
    resp = make_response(render_template("index_simple.html"))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@app.route("/modern")
def index_modern():
    resp = make_response(render_template("index_modern.html"))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@app.route("/api/data", methods=["GET"])
def get_data():
    global current_engine
    if current_engine is None:
        load_or_init_data()
    return jsonify(current_engine.get_summary_payload())


@app.route("/api/reset", methods=["POST"])
def reset_demo_data():
    global current_engine
    # Generate fresh dataset with new random seed
    import random
    new_seed = random.randint(100, 9999)
    df = generate_retail_dataset(seed=new_seed)
    df.to_csv(DATA_FILE, index=False)
    current_engine = RetailIntelligenceEngine(df).process()
    return jsonify({"status": "success", "message": "Fresh demo dataset generated successfully."})


@app.route("/api/upload", methods=["POST"])
def upload_csv():
    global current_engine
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded."}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "No file selected."}), 400

    try:
        df = pd.read_csv(file)
        # Check required columns
        required_cols = ["customer_id", "timestamp", "amount"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return jsonify({
                "status": "error",
                "message": f"CSV is missing required columns: {', '.join(missing)}. Required: customer_id, timestamp, amount."
            }), 400

        # Save uploaded file
        df.to_csv(DATA_FILE, index=False)
        current_engine = RetailIntelligenceEngine(df).process()
        return jsonify({"status": "success", "message": f"Successfully loaded {len(df)} transactions!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/add-customer", methods=["POST"])
def add_customer():
    global current_engine
    import random
    from datetime import datetime, timedelta

    data = request.get_json() or {}
    name = data.get("name", "").strip() or "Demo Customer"
    phone = data.get("phone", "").strip() or "+91 98765 43210"
    email = data.get("email", "").strip() or f"{name.lower().replace(' ', '.')}@example.com"
    category = data.get("category", "").strip() or "Apparel & Fashion"
    amount = float(data.get("amount", 2500.0))
    visit_timing = data.get("visit_timing", "recent")  # 'recent', 'slipping', 'at_risk'
    history_type = data.get("history_type", "single")   # 'single', 'repeat'

    # Determine recency in days
    if visit_timing == "recent":
        recency_days = random.randint(1, 7)
    elif visit_timing == "slipping":
        recency_days = random.randint(35, 55)
    else:  # at_risk / churn danger
        recency_days = random.randint(80, 130)

    # Reference base date
    base_date = datetime(2026, 11, 9, 10, 0, 0)
    last_tx_date = base_date - timedelta(days=recency_days, hours=random.randint(1, 8))

    # Read current data
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = generate_retail_dataset()

    cid = data.get("customer_id", "").strip()
    if not cid:
        cid = f"CUST-{random.randint(3000, 9999)}"

    num_txns = random.randint(4, 7) if history_type == "repeat" else 1
    new_rows = []
    curr_date = last_tx_date

    for i in range(num_txns):
        tx_amount = amount if i == 0 else round(amount * random.uniform(0.7, 1.3), 2)
        new_rows.append({
            "transaction_id": f"TXN-{random.randint(20000, 99999)}",
            "customer_id": cid,
            "customer_name": name,
            "customer_phone": phone,
            "customer_email": email,
            "timestamp": curr_date.strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "items_count": random.randint(1, 3),
            "amount": tx_amount,
            "payment_method": data.get("payment_method", "Credit Card")
        })
        curr_date = curr_date - timedelta(days=random.randint(14, 25), hours=random.randint(1, 6))

    df_new = pd.DataFrame(new_rows)
    df = pd.concat([df, df_new], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    
    current_engine = RetailIntelligenceEngine(df).process()
    
    # Retrieve the new customer profile
    cust_profile = current_engine.customer_profiles[current_engine.customer_profiles["customer_id"] == cid].to_dict(orient="records")[0]
    
    return jsonify({
        "status": "success",
        "message": f"Successfully added {name} ({cid}) with {num_txns} transaction(s)!",
        "customer": cust_profile
    })


@app.route("/api/export-offers", methods=["GET"])
def export_offers():
    global current_engine
    if current_engine is None:
        load_or_init_data()

    df = current_engine.customer_profiles[[
        "customer_id", "name", "phone", "email", "segment", 
        "churn_status", "churn_probability", "suggested_offer_title", 
        "suggested_discount", "suggested_promo_code", "suggested_sms_message"
    ]]

    csv_data = df.to_csv(index=False)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=retail_retention_offers.csv"}
    )


if __name__ == "__main__":
    load_or_init_data()
    print("=" * 60)
    print("Retail Customer Intelligence Dashboard Running!")
    print("Access URL: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=False)
