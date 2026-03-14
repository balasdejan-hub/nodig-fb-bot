import os
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "fallback_verify_token")


@app.route("/", methods=["GET"])
def home():
    return "Nodig FB bot running"


@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge or ""
    return "Verification token mismatch", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print(data)
    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    app.run()
