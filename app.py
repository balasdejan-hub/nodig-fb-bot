import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "DEKA_TEST_555"
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")


def send_message(recipient_id, message_text):
    url = "https://graph.facebook.com/v19.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}

    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }

    response = requests.post(url, params=params, json=payload)
    print("SEND API RESPONSE:", response.status_code, response.text)


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

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):

                sender_id = messaging_event.get("sender", {}).get("id")

                if "message" in messaging_event and sender_id:
                    user_text = messaging_event["message"].get("text", "")

                    print("USER MESSAGE:", user_text)

                    send_message(
                        sender_id,
                        f"Primio sam poruku: {user_text}"
                    )

    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    app.run()
