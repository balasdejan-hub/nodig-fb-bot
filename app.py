import os
import requests
from flask import Flask, request
from langdetect import detect, DetectorFactory

app = Flask(__name__)

DetectorFactory.seed = 0

VERIFY_TOKEN = "DEKA_TEST_555"
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

GRAPH_API_URL = "https://graph.facebook.com/v19.0/me/messages"


# ----------------------------
# LANGUAGE / DOMAIN SETTINGS
# ----------------------------

LANG_DOMAIN_MAP = {
    "en": "https://nodig.hr/index_en.html",
    "de": "https://nodig-shop.de",
    "es": "https://nodig.es",
    "it": "https://nodig.es",
    "sl": "https://nodig.si",
    "fr": "https://nodig.fr",
    "sr": "https://nodig.rs",
    "bs": "https://nodig.rs",
    "hr": "https://nodig.hr/index_en.html",  # po tvojoj sadašnjoj logici fallback na EN
}

CATALOG_URL_MAP = {
    "en": "https://nodig.hr/catalog_en.html",
    "de": "https://nodig-shop.de",
    "es": "https://nodig.es",
    "it": "https://nodig.es",
    "sl": "https://nodig.si",
    "fr": "https://nodig.fr",
    "sr": "https://nodig.rs",
    "bs": "https://nodig.rs",
    "hr": "https://nodig.hr/catalog_en.html",
}

CONTACT_URL_MAP = {
    "en": "https://nodig.hr/contact_en.html",
    "de": "https://nodig-shop.de",
    "es": "https://nodig.es",
    "it": "https://nodig.es",
    "sl": "https://nodig.si",
    "fr": "https://nodig.fr",
    "sr": "https://nodig.rs",
    "bs": "https://nodig.rs",
    "hr": "https://nodig.hr/contact_en.html",
}

DEFAULT_LANG = "en"
DEFAULT_HOME_URL = "https://nodig.hr/index_en.html"
DEFAULT_CATALOG_URL = "https://nodig.hr/catalog_en.html"
DEFAULT_CONTACT_URL = "https://nodig.hr/contact_en.html"

# Zamijeni ove image URL-ove ako želiš bolje cover slike po jeziku/domeni
CARD_IMAGE_MAP = {
    "en": "https://nodig.hr/images/logo.png",
    "de": "https://nodig.hr/images/logo.png",
    "es": "https://nodig.hr/images/logo.png",
    "it": "https://nodig.hr/images/logo.png",
    "sl": "https://nodig.hr/images/logo.png",
    "fr": "https://nodig.hr/images/logo.png",
    "sr": "https://nodig.hr/images/logo.png",
    "bs": "https://nodig.hr/images/logo.png",
    "hr": "https://nodig.hr/images/logo.png",
}


# ----------------------------
# SEND HELPERS
# ----------------------------

def graph_post(payload):
    params = {"access_token": PAGE_ACCESS_TOKEN}
    response = requests.post(GRAPH_API_URL, params=params, json=payload, timeout=20)
    print("SEND API RESPONSE:", response.status_code, response.text)
    return response


def send_text_message(recipient_id, message_text):
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    return graph_post(payload)


def send_generic_card(recipient_id, title, subtitle, image_url, button_title, button_url):
    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        {
                            "title": title[:80],
                            "image_url": image_url,
                            "subtitle": subtitle[:80],
                            "buttons": [
                                {
                                    "type": "web_url",
                                    "url": button_url,
                                    "title": button_title[:20]
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
    return graph_post(payload)


# ----------------------------
# LANGUAGE DETECTION
# ----------------------------

def detect_language(text):
    t = (text or "").lower().strip()

    if not t:
        return DEFAULT_LANG

    # strong keyword hints first
    if any(x in t for x in ["preis", "händler", "kaufen", "katalog", "guten tag", "hallo"]):
        return "de"

    if any(x in t for x in ["precio", "comprar", "distribuidor", "catálogo", "hola", "dónde"]):
        return "es"

    if any(x in t for x in ["prezzo", "comprare", "distributore", "catalogo", "ciao", "dove"]):
        return "it"

    if any(x in t for x in ["prix", "acheter", "distributeur", "catalogue", "bonjour", "où"]):
        return "fr"

    if any(x in t for x in ["cena", "kupiti", "distributer", "zdravo", "gde", "gdje", "katalog"]):
        # namjerno guramo na sr ako je u tom balkanskom setu
        return "sr"

    if any(x in t for x in ["cijena", "nabaviti", "pozdrav", "bok", "zdravo"]):
        return "hr"

    if any(x in t for x in ["cena", "kupiti", "pozdrav", "zdravo", "katalog"]):
        return "sr"

    if any(x in t for x in ["cena", "kupiti", "pozdrav", "zdravo"]):
        return "bs"

    if any(x in t for x in ["cena", "kupiti", "pozdrav", "zdravo"]):
        return "sr"

    if any(x in t for x in ["cena", "kupiti", "pozdrav", "zdravo"]):
        return "bs"

    if any(x in t for x in ["cena", "kupiti", "pozdrav", "zdravo"]):
        return "sr"

    if any(x in t for x in ["cena", "kupiti", "pozdrav", "zdravo"]):
        return "bs"

    if any(x in t for x in ["cena", "kupiti", "pozdrav", "zdravo"]):
        return "sr"

    if any(x in t for x in ["cena", "kupiti", "pozdrav", "zdravo"]):
        return "bs"

    if any(x in t for x in ["cena", "kupiti", "pozdrav", "zdravo"]):
        return "sr"

    if any(x in t for x in ["cena", "kupiti", "pozdrav", "zdravo"]):
        return "bs"

    if any(x in t for x in ["cena", "kupiti", "pozdrav", "zdravo"]):
        return "sr"

    if any(x in t for x in ["cena", "kupiti", "pozdrav", "zdravo"]):
        return "bs"

    if any(x in t for x in ["cena", "kupiti", "pozdrav", "zdravo"]):
        return "sr"

    if any(x in t for x in ["živjo", "zivjo", "cena", "kupiti", "distributer", "katalog"]):
        return "sl"

    # fallback detector
    try:
        detected = detect(t)
        if detected in LANG_DOMAIN_MAP:
            return detected
    except Exception:
        pass

    return DEFAULT_LANG


# ----------------------------
# INTENT DETECTION
# ----------------------------

def detect_intent(text):
    t = (text or "").lower().strip()

    greeting_words = [
        "hello", "hi", "hey", "hallo", "hola", "ciao", "bonjour",
        "pozdrav", "bok", "zdravo", "živjo", "zivjo"
    ]

    price_words = [
        "price", "cost", "quote", "pricing",
        "cijena", "cena", "preis", "prix", "precio", "prezzo"
    ]

    where_to_buy_words = [
        "where to buy", "where can i buy", "dealer", "distributor", "buy", "purchase",
        "gdje kupiti", "gde kupiti", "nabaviti", "kupiti",
        "händler", "haendler", "distributeur", "distribuidor", "distributore"
    ]

    catalog_words = [
        "catalog", "catalogue", "brochure", "katalog", "catálogo", "catalogo"
    ]

    if any(word in t for word in greeting_words):
        return "greeting"

    if any(word in t for word in price_words):
        return "price"

    if any(word in t for word in where_to_buy_words):
        return "where_to_buy"

    if any(word in t for word in catalog_words):
        return "catalog"

    return "fallback"


# ----------------------------
# LOCALIZED TEXTS
# ----------------------------

def get_localized_text(lang, key):
    texts = {
        "en": {
            "greeting": "Hello. Thanks for contacting NoDig. You can ask about price, dealer information, catalog or product details.",
            "fallback": "Thanks for your message. Please ask about price, dealer information, catalog or product details.",
            "catalog_title": "NoDig Catalog",
            "catalog_subtitle": "Browse our trenchless equipment and solutions.",
            "catalog_button": "Open Catalog",
            "price_title": "Pricing & Sales",
            "price_subtitle": "Contact us for pricing and sales information.",
            "price_button": "Contact Sales",
            "buy_title": "Where to Buy",
            "buy_subtitle": "Find contact and distributor information here.",
            "buy_button": "Open Page",
        },
        "de": {
            "greeting": "Hallo. Danke für Ihre Nachricht an NoDig. Sie können nach Preis, Händler, Katalog oder Produktdetails fragen.",
            "fallback": "Danke für Ihre Nachricht. Bitte fragen Sie nach Preis, Händler, Katalog oder Produktdetails.",
            "catalog_title": "NoDig Katalog",
            "catalog_subtitle": "Entdecken Sie unsere Geräte und Lösungen.",
            "catalog_button": "Katalog öffnen",
            "price_title": "Preis & Verkauf",
            "price_subtitle": "Kontaktieren Sie uns für Preise und Verkauf.",
            "price_button": "Kontakt",
            "buy_title": "Wo kaufen",
            "buy_subtitle": "Händler- und Kontaktinformationen finden Sie hier.",
            "buy_button": "Seite öffnen",
        },
        "es": {
            "greeting": "Hola. Gracias por contactar con NoDig. Puede preguntar por precio, distribuidor, catálogo o detalles del producto.",
            "fallback": "Gracias por su mensaje. Puede preguntar por precio, distribuidor, catálogo o detalles del producto.",
            "catalog_title": "Catálogo NoDig",
            "catalog_subtitle": "Descubra nuestros equipos y soluciones.",
            "catalog_button": "Abrir catálogo",
            "price_title": "Precio y ventas",
            "price_subtitle": "Contáctenos para precio e información comercial.",
            "price_button": "Contacto",
            "buy_title": "Dónde comprar",
            "buy_subtitle": "Aquí encontrará información comercial y de distribuidores.",
            "buy_button": "Abrir página",
        },
        "it": {
            "greeting": "Ciao. Grazie per aver contattato NoDig. Puoi chiedere prezzo, distributore, catalogo o dettagli del prodotto.",
            "fallback": "Grazie per il tuo messaggio. Puoi chiedere prezzo, distributore, catalogo o dettagli del prodotto.",
            "catalog_title": "Catalogo NoDig",
            "catalog_subtitle": "Scopri le nostre macchine e soluzioni.",
            "catalog_button": "Apri catalogo",
            "price_title": "Prezzi e vendite",
            "price_subtitle": "Contattaci per prezzi e informazioni commerciali.",
            "price_button": "Contatto",
            "buy_title": "Dove acquistare",
            "buy_subtitle": "Qui trovi informazioni commerciali e distributori.",
            "buy_button": "Apri pagina",
        },
        "fr": {
            "greeting": "Bonjour. Merci d’avoir contacté NoDig. Vous pouvez demander le prix, le distributeur, le catalogue ou des détails produit.",
            "fallback": "Merci pour votre message. Vous pouvez demander le prix, le distributeur, le catalogue ou des détails produit.",
            "catalog_title": "Catalogue NoDig",
            "catalog_subtitle": "Découvrez nos équipements et solutions.",
            "catalog_button": "Ouvrir",
            "price_title": "Prix et ventes",
            "price_subtitle": "Contactez-nous pour les prix et les ventes.",
            "price_button": "Contact",
            "buy_title": "Où acheter",
            "buy_subtitle": "Informations commerciales et distributeurs ici.",
            "buy_button": "Ouvrir",
        },
        "sl": {
            "greeting": "Pozdravljeni. Hvala za sporočilo. Vprašate lahko za ceno, distributerja, katalog ali podrobnosti izdelka.",
            "fallback": "Hvala za vaše sporočilo. Vprašate lahko za ceno, distributerja, katalog ali podrobnosti izdelka.",
            "catalog_title": "NoDig katalog",
            "catalog_subtitle": "Oglejte si naše stroje in rešitve.",
            "catalog_button": "Odpri katalog",
            "price_title": "Cena in prodaja",
            "price_subtitle": "Za cene in prodajo nas kontaktirajte.",
            "price_button": "Kontakt",
            "buy_title": "Kje kupiti",
            "buy_subtitle": "Tukaj najdete prodajne in distributerske informacije.",
            "buy_button": "Odpri stran",
        },
        "sr": {
            "greeting": "Zdravo. Hvala što ste kontaktirali NoDig. Možete pitati za cenu, distributera, katalog ili detalje proizvoda.",
            "fallback": "Hvala na poruci. Možete pitati za cenu, distributera, katalog ili detalje proizvoda.",
            "catalog_title": "NoDig katalog",
            "catalog_subtitle": "Pogledajte naše mašine i rešenja.",
            "catalog_button": "Otvori katalog",
            "price_title": "Cena i prodaja",
            "price_subtitle": "Kontaktirajte nas za cenu i prodajne informacije.",
            "price_button": "Kontakt",
            "buy_title": "Gde kupiti",
            "buy_subtitle": "Ovde možete pronaći prodajne i distributerske informacije.",
            "buy_button": "Otvori stranu",
        },
        "bs": {
            "greeting": "Zdravo. Hvala što ste kontaktirali NoDig. Možete pitati za cijenu, distributera, katalog ili detalje proizvoda.",
            "fallback": "Hvala na poruci. Možete pitati za cijenu, distributera, katalog ili detalje proizvoda.",
            "catalog_title": "NoDig katalog",
            "catalog_subtitle": "Pogledajte naše mašine i rješenja.",
            "catalog_button": "Otvori katalog",
            "price_title": "Cijena i prodaja",
            "price_subtitle": "Kontaktirajte nas za cijene i prodajne informacije.",
            "price_button": "Kontakt",
            "buy_title": "Gdje kupiti",
            "buy_subtitle": "Ovdje možete pronaći prodajne i distributerske informacije.",
            "buy_button": "Otvori stranicu",
        },
        "hr": {
            "greeting": "Pozdrav. Hvala što ste kontaktirali NoDig. Možete pitati za cijenu, distributera, katalog ili detalje proizvoda.",
            "fallback": "Hvala na poruci. Možete pitati za cijenu, distributera, katalog ili detalje proizvoda.",
            "catalog_title": "NoDig katalog",
            "catalog_subtitle": "Pogledajte naše strojeve i rješenja.",
            "catalog_button": "Otvori katalog",
            "price_title": "Cijena i prodaja",
            "price_subtitle": "Kontaktirajte nas za cijene i prodajne informacije.",
            "price_button": "Kontakt",
            "buy_title": "Gdje kupiti",
            "buy_subtitle": "Ovdje možete pronaći prodajne i distributerske informacije.",
            "buy_button": "Otvori stranicu",
        },
    }

    lang_texts = texts.get(lang, texts["en"])
    return lang_texts.get(key, texts["en"][key])


# ----------------------------
# ROUTING HELPERS
# ----------------------------

def get_home_url(lang):
    return LANG_DOMAIN_MAP.get(lang, DEFAULT_HOME_URL)


def get_catalog_url(lang):
    return CATALOG_URL_MAP.get(lang, DEFAULT_CATALOG_URL)


def get_contact_url(lang):
    return CONTACT_URL_MAP.get(lang, DEFAULT_CONTACT_URL)


def get_card_image(lang):
    return CARD_IMAGE_MAP.get(lang, CARD_IMAGE_MAP["en"])


# ----------------------------
# MAIN BOT LOGIC
# ----------------------------

def handle_message(sender_id, user_text):
    lang = detect_language(user_text)
    intent = detect_intent(user_text)

    print("DETECTED LANG:", lang)
    print("DETECTED INTENT:", intent)

    if intent == "greeting":
        return send_text_message(sender_id, get_localized_text(lang, "greeting"))

    if intent == "catalog":
        return send_generic_card(
            recipient_id=sender_id,
            title=get_localized_text(lang, "catalog_title"),
            subtitle=get_localized_text(lang, "catalog_subtitle"),
            image_url=get_card_image(lang),
            button_title=get_localized_text(lang, "catalog_button"),
            button_url=get_catalog_url(lang),
        )

    if intent == "price":
        return send_generic_card(
            recipient_id=sender_id,
            title=get_localized_text(lang, "price_title"),
            subtitle=get_localized_text(lang, "price_subtitle"),
            image_url=get_card_image(lang),
            button_title=get_localized_text(lang, "price_button"),
            button_url=get_contact_url(lang),
        )

    if intent == "where_to_buy":
        return send_generic_card(
            recipient_id=sender_id,
            title=get_localized_text(lang, "buy_title"),
            subtitle=get_localized_text(lang, "buy_subtitle"),
            image_url=get_card_image(lang),
            button_title=get_localized_text(lang, "buy_button"),
            button_url=get_home_url(lang),
        )

    return send_text_message(sender_id, get_localized_text(lang, "fallback"))


# ----------------------------
# ROUTES
# ----------------------------

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
                    user_text = messaging_event["message"].get("text", "").strip()
                    print("USER MESSAGE:", user_text)
                    handle_message(sender_id, user_text)

    return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    app.run()
