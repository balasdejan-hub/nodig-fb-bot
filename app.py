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


def get_reply(user_text):
    text = user_text.lower().strip()

    if any(word in text for word in ["hello", "hi", "hey", "pozdrav", "bok", "zdravo"]):
        return (
            "Hello. Thanks for contacting NoDig.\n\n"
            "You can ask about:\n"
            "- price\n"
            "- where to buy\n"
            "- catalog"
        )

    if any(word in text for word in ["price", "cijena", "preis", "prix", "precio"]):
        return (
            "For pricing and sales information please contact us here:\n"
            "https://nodig.hr/contact_en.html"
        )

    if any(word in text for word in ["where", "buy", "dealer", "nabaviti", "kupiti", "distributor"]):
        return (
            "You can find sales and distributor information here:\n"
            "https://nodig.hr/contact_en.html"
        )

    if any(word in text for word in ["catalog", "brochure", "katalog", "catalogue"]):
        return (
            "You can browse our catalog here:\n"
            "https://nodig.hr/catalog_en.html"
        )

    return (
        "Thanks for your message.\n"
        "Please ask about price, dealer information, catalog or product details."
    )


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

                    reply_text = get_reply(user_text)
                    send_message(sender_id, reply_text)

    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    app.run()
