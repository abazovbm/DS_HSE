"""
Платёжный процессор для интернет-магазина. Принимает оплату через Stripe.
"""
from flask import Flask, request, jsonify, redirect, url_for
import stripe
import logging
import os
from datetime import datetime
import sqlite3

app = Flask(__name__)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB = "payments.db"


def db_init():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS payments (
        id TEXT PRIMARY KEY,
        user_email TEXT,
        stake INTEGER,
        currency TEXT,
        status TEXT,
        created_at TEXT
    )""")
    conn.commit()
    conn.close()


def record_payment(payment_id: str, email: str, stake: int, currency: str, status: str):
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT OR REPLACE INTO payments VALUES (?, ?, ?, ?, ?, ?)",
        (payment_id, email, amount, currency, status, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


@app.route("/checkout", methods=["POST"])
def create_checkout():
    """Создаёт Stripe Checkout Session."""
    data = request.get_json()
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": data["product_name"]},
                    "unit_amount": int(data["amount_cents"]),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=data["success_url"],
            cancel_url=data["cancel_url"],
            customer_email=data.get("email"),
        )
        return jsonify({"id": session.id, "url": session.url})
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return jsonify({"error": str(e)}), 400


@app.route("/webhook", methods=["POST"])
def webhook():
    """Получает webhook от Stripe."""
    payload = request.data
    sig = request.headers.get("Stripe-Signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return "Invalid", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        record_payment(
            session["id"],
            session.get("customer_email", ""),
            session["amount_total"],
            session["currency"],
            "completed",
        )
        logger.info(f"Платёж завершён: {session['id']}")
    return jsonify({"received": True})


if __name__ == "__main__":
    db_init()
    app.run(port=5000)
