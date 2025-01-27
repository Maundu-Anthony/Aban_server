from flask import Flask, request, jsonify
import requests
from datetime import datetime
import base64
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Safaricom Daraja API credentials
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
BUSINESS_SHORT_CODE = os.getenv("BUSINESS_SHORT_CODE")
PASSKEY = os.getenv("PASSKEY")
CALLBACK_URL = os.getenv("CALLBACK_URL")

# Generate access token
def generate_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    auth = base64.b64encode(f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode()).decode("utf-8")
    headers = {"Authorization": f"Basic {auth}"}
    response = requests.get(url, headers=headers)
    return response.json().get("access_token")

# Generate Lipa Na M-Pesa password
def generate_password():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode((BUSINESS_SHORT_CODE + PASSKEY + timestamp).encode()).decode("utf-8")
    return password, timestamp

# Initiate STK Push (Lipa Na M-Pesa)
@app.route("/initiate-payment", methods=["POST"])
def initiate_payment():
    data = request.json
    phone_number = data.get("phone_number")
    amount = data.get("amount")
    package_id = data.get("package_id")

    if not phone_number or not amount:
        return jsonify({"error": "Phone number and amount are required"}), 400

    access_token = generate_access_token()
    password, timestamp = generate_password()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "BusinessShortCode": BUSINESS_SHORT_CODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": BUSINESS_SHORT_CODE,
        "PhoneNumber": phone_number,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": f"Package_{package_id}",
        "TransactionDesc": "Wi-Fi Package Payment",
    }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        headers=headers,
        json=payload,
    )

    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({"error": "Payment initiation failed", "details": response.json()}), 500

# Callback URL for M-Pesa confirmation
@app.route("/callback", methods=["POST"])
def callback():
    data = request.json
    print("Payment Callback Data:", data)  # Log the callback data for debugging
    # Process the payment confirmation here (e.g., update database)
    return jsonify({"message": "Callback received"}), 200

if __name__ == "__main__":
    app.run(debug=True)