import requests
import time
import json
import os

# --- CONFIGURATION ---
BRANDS = [
    "Gérard Darel 24h",
    "Chloé Paddington"
]
MAX_PRICE = 120
ITEM_STATE = "very_good"  # possible: new, very_good, good, satisfactory, poor
CHECK_INTERVAL = 600  # 10 minutes = 600s

# --- TELEGRAM CONFIG ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- SAUVEGARDE DES ANNONCES DÉJÀ VUES ---
SEEN_FILE = "seen_items.json"
if os.path.exists(SEEN_FILE):
    try:
        with open(SEEN_FILE, "r") as f:
            seen_items = json.load(f)
    except Exception:
        seen_items = []
else:
    seen_items = []

def send_telegram_message(text):
    """Envoie un message sur Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Erreur : TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID non défini.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if not resp.ok:
            print(f"Erreur lors de l'envoi du message Telegram : {resp.text}")
    except Exception as e:
        print(f"Exception lors de l'envoi du message Telegram : {e}")

def search_vinted(query):
    """Effectue une recherche sur Vinted via l'API publique."""
    url = "https://www.vinted.fr/api/v2/catalog/items"
    params = {
        "search_text": query,
        "price_to": MAX_PRICE,
        "status_ids": "2",  # Très bon état
        "order": "newest_first",
        "per_page": 10,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("items", [])
    except Exception as e:
        print(f"Erreur lors de la recherche Vinted : {e}")
        return []

def check_new_items():
    """Cherche les nouvelles annonces et envoie des alertes."""
    global seen_items
    for brand in BRANDS:
        items = search_vinted(brand)
        for item in items:
            item_id = str(item.get("id"))
            if item_id not in seen_items:
                seen_items.append(item_id)
                link = f'https://www.vinted.fr/items/{item_id}'
                price = item.get("price", "?")
                title = item.get("title", "Sans titre")
                msg = f"👜 Nouvelle annonce trouvée !\n\n{title}\nPrix : {price} €\n{link}"
                send_telegram_message(msg)
    # Sauvegarde la liste
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump(seen_items, f)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du fichier {SEEN_FILE} : {e}")

def main():
    send_telegram_message("🤖 Vinted Finder démarré !")
    try:
        while True:
            check_new_items()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("Arrêt demandé par l'utilisateur.")
    except Exception as e:
        print(f"Erreur inattendue : {e}")

if __name__ == "__main__":
    main()
