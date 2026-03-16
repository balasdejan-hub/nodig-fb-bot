import os
import json
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langdetect import detect, DetectorFactory
from apscheduler.schedulers.background import BackgroundScheduler

DetectorFactory.seed = 0

# ----------------------------
# CONFIG — env variables
# ----------------------------

PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
GRAPH_API_BASE    = "https://graph.facebook.com/v19.0"

SMTP_HOST     = "smtp.office365.com"
SMTP_PORT     = 587
SMTP_USER     = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
REPORT_TO     = os.getenv("REPORT_EMAIL", "orders@nodig.hr")

DEFAULT_LANG  = "en"

# ----------------------------
# IN-MEMORY LOG
# ----------------------------

_daily_log = []


# ----------------------------
# PROFANITY FILTER
# ----------------------------

PROFANITY = {
    "hr": ["jebem", "jebiga", "kurva", "pička", "pizda", "govno", "kurac",
           "šupak", "kreten", "idiot", "glupan", "debil"],
    "sr": ["jebem", "jebiga", "kurva", "picka", "pizda", "govno", "kurac",
           "šupak", "kreten", "idiot", "debil"],
    "bs": ["jebem", "jebiga", "kurva", "picka", "pizda", "govno", "kurac",
           "kreten", "idiot", "debil"],
    "en": ["fuck", "shit", "bitch", "asshole", "cunt", "dick", "bastard",
           "idiot", "moron", "stupid"],
    "de": ["scheiße", "scheisse", "arsch", "ficken", "hurensohn", "idiot",
           "wichser", "blödmann", "depp"],
    "es": ["mierda", "puta", "coño", "joder", "hostia", "imbécil",
           "idiota", "gilipollas", "cabron"],
    "it": ["cazzo", "vaffanculo", "stronzo", "puttana", "idiota",
           "deficiente", "scemo", "minchia"],
    "fr": ["merde", "putain", "connard", "salaud", "idiot", "imbécile",
           "con", "enculé", "batard"],
    "sl": ["jebem", "kurac", "pizda", "govno", "idiot", "kreten",
           "bedak", "butec"],
}

ALL_PROFANITY = set()
for words in PROFANITY.values():
    ALL_PROFANITY.update(words)


def is_offensive(text):
    t = (text or "").lower()
    return any(word in t for word in ALL_PROFANITY)


# ----------------------------
# LANGUAGE DETECTION
# ----------------------------

SUPPORTED_LANGS = {"en", "de", "es", "it", "fr", "sl", "hr", "sr", "bs"}


def detect_language(text):
    t = (text or "").lower().strip()
    if not t:
        return DEFAULT_LANG

    de_kw = ["preis", "händler", "haendler", "kaufen", "guten tag", "hallo", "deutsch"]
    es_kw = ["precio", "comprar", "distribuidor", "hola", "dónde", "donde", "españa"]
    it_kw = ["prezzo", "comprare", "distributore", "ciao", "dove", "italia"]
    fr_kw = ["prix", "acheter", "distributeur", "bonjour", "où", "france"]
    sl_kw = ["živjo", "zivjo", "slovenija", "kje"]
    hr_kw = ["cijena", "gdje", "pozdrav", "bok", "hrvatska"]
    sr_kw = ["cena", "gde", "srbija", "beograd"]
    bs_kw = ["cijenu", "ovdje", "bosna", "sarajevo"]
    en_kw = ["price", "catalog", "dealer", "buy", "hello", "hi", "hey",
             "where", "how much", "distributor", "product", "thanks", "great"]

    if any(x in t for x in de_kw): return "de"
    if any(x in t for x in es_kw): return "es"
    if any(x in t for x in it_kw): return "it"
    if any(x in t for x in fr_kw): return "fr"
    if any(x in t for x in sl_kw): return "sl"
    if any(x in t for x in hr_kw): return "hr"
    if any(x in t for x in sr_kw): return "sr"
    if any(x in t for x in bs_kw): return "bs"
    if any(x in t for x in en_kw): return "en"

    if len(t.split()) >= 4:
        try:
            detected = detect(t)
            if detected in SUPPORTED_LANGS:
                return detected
        except Exception as e:
            print(f"[LANGDETECT ERROR] {str(e)}")

    return DEFAULT_LANG


# ----------------------------
# INTENT DETECTION
# ----------------------------

def detect_intent(text):
    t = (text or "").lower().strip()

    greeting_words = [
        "hello", "hi", "hey", "hallo", "hola", "ciao", "bonjour",
        "pozdrav", "bok", "zdravo", "živjo", "zivjo", "good morning",
        "guten tag", "buenos días", "buongiorno", "salut"
    ]
    price_words = [
        "price", "cost", "quote", "pricing", "how much",
        "cijena", "cena", "preis", "prix", "precio", "prezzo", "koliko"
    ]
    where_to_buy_words = [
        "where to buy", "where can i buy", "dealer", "distributor", "buy",
        "purchase", "reseller", "gdje kupiti", "gde kupiti", "nabaviti",
        "kupiti", "händler", "haendler", "distributeur", "distribuidor",
        "distributore", "kje kupiti", "où acheter"
    ]
    catalog_words = [
        "catalog", "catalogue", "brochure", "katalog", "catálogo",
        "catalogo", "prospekt", "leaflet", "products", "proizvodi"
    ]

    if any(word in t for word in greeting_words):     return "greeting"
    if any(word in t for word in price_words):        return "price"
    if any(word in t for word in where_to_buy_words): return "where_to_buy"
    if any(word in t for word in catalog_words):      return "catalog"
    return "fallback"


# ----------------------------
# LOCALIZED COMMENT REPLIES
# ----------------------------

COMMENT_REPLIES = {
    "greeting": {
        "en": "Hello! Thanks for your interest in NoDig. Feel free to send us a message for more details. 🔧",
        "de": "Hallo! Danke für Ihr Interesse an NoDig. Schreiben Sie uns gerne eine Nachricht. 🔧",
        "es": "¡Hola! Gracias por su interés en NoDig. No dude en enviarnos un mensaje. 🔧",
        "it": "Ciao! Grazie per il tuo interesse in NoDig. Scrivici un messaggio per maggiori dettagli. 🔧",
        "fr": "Bonjour ! Merci pour votre intérêt pour NoDig. N'hésitez pas à nous envoyer un message. 🔧",
        "sl": "Pozdravljeni! Hvala za vaše zanimanje za NoDig. Pošljite nam sporočilo za več informacij. 🔧",
        "hr": "Pozdrav! Hvala na interesu za NoDig. Slobodno nam pošaljite poruku za više detalja. 🔧",
        "sr": "Zdravo! Hvala na interesovanju za NoDig. Slobodno nam pošaljite poruku. 🔧",
        "bs": "Zdravo! Hvala na interesovanju za NoDig. Slobodno nam pošaljite poruku. 🔧",
    },
    "catalog": {
        "en": "Thanks for your comment! Browse our full catalog here: https://nodig.hr/catalog_en.html 📋",
        "de": "Danke für Ihren Kommentar! Unseren Katalog finden Sie hier: https://nodig-shop.de 📋",
        "es": "¡Gracias por su comentario! Vea nuestro catálogo aquí: https://nodig.es 📋",
        "it": "Grazie per il tuo commento! Puoi vedere il nostro catalogo qui: https://nodig.es 📋",
        "fr": "Merci pour votre commentaire ! Consultez notre catalogue ici : https://nodig.fr 📋",
        "sl": "Hvala za komentar! Naš katalog si oglejte tukaj: https://nodig.si 📋",
        "hr": "Hvala na komentaru! Naš katalog pregledajte ovdje: https://nodig.hr/catalog.html 📋",
        "sr": "Hvala na komentaru! Naš katalog pogledajte ovde: https://nodig.rs 📋",
        "bs": "Hvala na komentaru! Naš katalog pogledajte ovdje: https://nodig.rs 📋",
    },
    "price": {
        "en": "Thanks for your comment! For pricing information please contact us here: https://nodig.hr/contact_en.html 💬",
        "de": "Danke für Ihren Kommentar! Für Preisinformationen kontaktieren Sie uns hier: https://nodig-shop.de 💬",
        "es": "¡Gracias por su comentario! Para información de precios contáctenos aquí: https://nodig.es 💬",
        "it": "Grazie per il tuo commento! Per informazioni sui prezzi contattateci qui: https://nodig.es 💬",
        "fr": "Merci pour votre commentaire ! Pour les tarifs contactez-nous ici : https://nodig.fr 💬",
        "sl": "Hvala za komentar! Za informacije o cenah nas kontaktirajte tukaj: https://nodig.si 💬",
        "hr": "Hvala na komentaru! Za informacije o cijenama kontaktirajte nas ovdje: https://nodig.hr/contact.html 💬",
        "sr": "Hvala na komentaru! Za informacije o cenama kontaktirajte nas ovde: https://nodig.rs 💬",
        "bs": "Hvala na komentaru! Za informacije o cijenama kontaktirajte nas ovdje: https://nodig.rs 💬",
    },
    "where_to_buy": {
        "en": "Thanks for your comment! Find our dealers and distributors here: https://nodig.hr/index_en.html 📍",
        "de": "Danke für Ihren Kommentar! Unsere Händler finden Sie hier: https://nodig-shop.de 📍",
        "es": "¡Gracias por su comentario! Encuentre nuestros distribuidores aquí: https://nodig.es 📍",
        "it": "Grazie per il tuo commento! Trova i nostri distributori qui: https://nodig.es 📍",
        "fr": "Merci pour votre commentaire ! Trouvez nos distributeurs ici : https://nodig.fr 📍",
        "sl": "Hvala za komentar! Naše distributerje najdete tukaj: https://nodig.si 📍",
        "hr": "Hvala na komentaru! Naše distributerje pronađite ovdje: https://nodig.hr 📍",
        "sr": "Hvala na komentaru! Naše distributere pronađite ovde: https://nodig.rs 📍",
        "bs": "Hvala na komentaru! Naše distributere pronađite ovdje: https://nodig.rs 📍",
    },
    "fallback": {
        "en": "Thank you for your comment! For more information feel free to send us a message. 🔧",
        "de": "Danke für Ihren Kommentar! Für weitere Infos senden Sie uns bitte eine Nachricht. 🔧",
        "es": "¡Gracias por su comentario! Para más información envíenos un mensaje. 🔧",
        "it": "Grazie per il tuo commento! Per ulteriori informazioni inviaci un messaggio. 🔧",
        "fr": "Merci pour votre commentaire ! Pour plus d'infos envoyez-nous un message. 🔧",
        "sl": "Hvala za komentar! Za več informacij nam pošljite sporočilo. 🔧",
        "hr": "Hvala na komentaru! Za više informacija slobodno nam pošaljite poruku. 🔧",
        "sr": "Hvala na komentaru! Za više informacija slobodno nam pošaljite poruku. 🔧",
        "bs": "Hvala na komentaru! Za više informacija slobodno nam pošaljite poruku. 🔧",
    },
}


def get_reply_text(lang, intent):
    intent_replies = COMMENT_REPLIES.get(intent, COMMENT_REPLIES["fallback"])
    return intent_replies.get(lang, intent_replies.get("en", ""))


# ----------------------------
# GRAPH API HELPERS
# ----------------------------

def graph_post(url, payload=None):
    if not PAGE_ACCESS_TOKEN:
        print("[COMMENTS ERROR] PAGE_ACCESS_TOKEN nije postavljen.")
        return None
    params = {"access_token": PAGE_ACCESS_TOKEN}
    try:
        response = requests.post(url, params=params, json=payload or {}, timeout=20)
        print(f"[GRAPH] {url} → {response.status_code} {response.text}")
        return response
    except Exception as e:
        print(f"[GRAPH ERROR] {str(e)}")
        return None


def hide_comment(comment_id):
    url = f"{GRAPH_API_BASE}/{comment_id}"
    return graph_post(url, {"is_hidden": True})


def reply_to_comment(comment_id, message):
    url = f"{GRAPH_API_BASE}/{comment_id}/comments"
    return graph_post(url, {"message": message})


# ----------------------------
# MAIN COMMENT HANDLER
# ----------------------------

def handle_comment(change):
    value = change.get("value", {})

    if value.get("item") != "comment":
        return
    if value.get("verb") != "add":
        return

    comment_id = value.get("comment_id") or value.get("id")
    message    = value.get("message", "").strip()
    user       = value.get("from", {})
    user_name  = user.get("name", "Unknown")
    post_id    = value.get("post_id", "")

    if not comment_id or not message:
        print("[COMMENTS] Komentar bez ID-a ili teksta, preskačem.")
        return

    print(f"[COMMENTS] Novi komentar od {user_name!r}: {message!r}")

    lang      = detect_language(message)
    intent    = detect_intent(message)
    offensive = is_offensive(message)

    print(f"[COMMENTS] lang={lang} intent={intent} offensive={offensive}")

    if offensive:
        print(f"[COMMENTS] Uvredljiv — skrivam. comment_id={comment_id}")
        hide_comment(comment_id)
        _log_event(user_name, message, "hidden", lang, post_id)
    else:
        reply_text = get_reply_text(lang, intent)
        print(f"[COMMENTS] Reply ({lang}/{intent}): {reply_text!r}")
        reply_to_comment(comment_id, reply_text)
        _log_event(user_name, message, f"replied:{intent}", lang, post_id)


# ----------------------------
# DAILY LOG
# ----------------------------

def _log_event(user_name, message, action, lang, post_id=""):
    _daily_log.append({
        "time":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user":    user_name,
        "lang":    lang,
        "message": message,
        "action":  action,
        "post_id": post_id,
    })


# ----------------------------
# EMAIL REPORT
# ----------------------------

def send_daily_report():
    print("[REPORT] Slanje dnevnog reporta...")

    now     = datetime.now().strftime("%Y-%m-%d")
    hidden  = [e for e in _daily_log if e["action"] == "hidden"]
    replied = [e for e in _daily_log if e["action"].startswith("replied")]

    def rows(events):
        if not events:
            return "<tr><td colspan='5' style='color:#999;padding:8px'>Nema događaja</td></tr>"
        out = ""
        for e in events:
            color = "#ffe0e0" if e["action"] == "hidden" else "#e8f5e9"
            out += f"""
            <tr style='background:{color}'>
                <td style='padding:6px 10px'>{e['time']}</td>
                <td style='padding:6px 10px'>{e['user']}</td>
                <td style='padding:6px 10px'>{e['lang'].upper()}</td>
                <td style='padding:6px 10px'>{e['message'][:100]}</td>
                <td style='padding:6px 10px'><b>{e['action']}</b></td>
            </tr>"""
        return out

    table_style = "border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:13px"
    th_style    = "background:#003580;color:#fff;padding:8px 10px;text-align:left"

    html = f"""
    <html><body style='font-family:Arial,sans-serif;color:#222;padding:20px'>
    <h2 style='color:#003580'>NoDig Facebook Bot — Dnevni Report</h2>
    <p>Datum: <b>{now}</b></p>

    <h3 style='color:#c00'>🚫 Skriveni komentari ({len(hidden)})</h3>
    <table style='{table_style}'>
        <tr>
            <th style='{th_style}'>Vrijeme</th>
            <th style='{th_style}'>Korisnik</th>
            <th style='{th_style}'>Jezik</th>
            <th style='{th_style}'>Komentar</th>
            <th style='{th_style}'>Akcija</th>
        </tr>
        {rows(hidden)}
    </table>

    <br>

    <h3 style='color:#2e7d32'>✅ Auto-reply komentari ({len(replied)})</h3>
    <table style='{table_style}'>
        <tr>
            <th style='{th_style}'>Vrijeme</th>
            <th style='{th_style}'>Korisnik</th>
            <th style='{th_style}'>Jezik</th>
            <th style='{th_style}'>Komentar</th>
            <th style='{th_style}'>Akcija</th>
        </tr>
        {rows(replied)}
    </table>

    <br>
    <p style='color:#999;font-size:11px'>NoDig FB Bot — automatski report | {now}</p>
    </body></html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"NoDig FB Bot — Dnevni report {now}"
        msg["From"]    = SMTP_USER
        msg["To"]      = REPORT_TO
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, REPORT_TO, msg.as_string())

        print(f"[REPORT] Email poslan na {REPORT_TO}")
        _daily_log.clear()

    except Exception as e:
        print(f"[REPORT ERROR] {str(e)}")


# ----------------------------
# TOKEN AUTO-REFRESH
# ----------------------------

RENDER_API_KEY    = os.getenv("RENDER_API_KEY")
RENDER_SERVICE_ID = "srv-d6qin1c50q8c73bj62bg"
FB_APP_ID         = os.getenv("FB_APP_ID")
FB_APP_SECRET     = os.getenv("FB_APP_SECRET")


def refresh_page_token():
    """
    Refresha Facebook Page Access Token i ažurira Render env varijablu.
    Pokreće se svakih 45 dana.
    """
    print("[TOKEN REFRESH] Pokrećem refresh tokena...")

    current_token = os.getenv("PAGE_ACCESS_TOKEN")
    if not current_token:
        print("[TOKEN REFRESH ERROR] PAGE_ACCESS_TOKEN nije postavljen.")
        return

    if not all([FB_APP_ID, FB_APP_SECRET, RENDER_API_KEY]):
        print("[TOKEN REFRESH ERROR] Nedostaju env varijable: FB_APP_ID, FB_APP_SECRET ili RENDER_API_KEY.")
        return

    # Korak 1 — exchange za novi long-lived token
    try:
        resp = requests.get(
            "https://graph.facebook.com/oauth/access_token",
            params={
                "grant_type":        "fb_exchange_token",
                "client_id":         FB_APP_ID,
                "client_secret":     FB_APP_SECRET,
                "fb_exchange_token": current_token,
            },
            timeout=20
        )
        data = resp.json()
        new_token = data.get("access_token")

        if not new_token:
            print(f"[TOKEN REFRESH ERROR] Exchange nije vratio token: {data}")
            return

        print("[TOKEN REFRESH] Novi token dobiven.")

    except Exception as e:
        print(f"[TOKEN REFRESH ERROR] Exchange request: {str(e)}")
        return

    # Korak 2 — ažuriraj Render env varijablu
    try:
        render_resp = requests.put(
            f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/env-vars",
            headers={
                "Authorization": f"Bearer {RENDER_API_KEY}",
                "Content-Type":  "application/json",
            },
            json=[{"key": "PAGE_ACCESS_TOKEN", "value": new_token}],
            timeout=20
        )

        if render_resp.status_code == 200:
            print("[TOKEN REFRESH] Render env varijabla ažurirana. Redeploy u tijeku...")
        else:
            print(f"[TOKEN REFRESH ERROR] Render API: {render_resp.status_code} {render_resp.text}")

    except Exception as e:
        print(f"[TOKEN REFRESH ERROR] Render API request: {str(e)}")


# ----------------------------
# SCHEDULER — svaki dan u 08:00 + token refresh svakih 45 dana
# ----------------------------

def init_scheduler():
    scheduler = BackgroundScheduler(timezone="Europe/Zagreb")

    # Dnevni email report
    scheduler.add_job(
        send_daily_report,
        trigger="cron",
        hour=8,
        minute=0,
        id="daily_report"
    )

    # Token refresh svakih 45 dana
    scheduler.add_job(
        refresh_page_token,
        trigger="interval",
        days=45,
        id="token_refresh"
    )

    scheduler.start()
    print("[SCHEDULER] Scheduler pokrenut — dnevni report 08:00, token refresh svakih 45 dana.")
    return scheduler
