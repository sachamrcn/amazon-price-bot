
import os
import requests
from bs4 import BeautifulSoup
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import time

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = int(os.getenv("TELEGRAM_USER_ID"))
bot = telepot.Bot(TELEGRAM_BOT_TOKEN)

# Catégories fixes avec URLs officielles Amazon
CATEGORIES = {
    "Électronique": "https://www.amazon.fr/s?i=electronics&rh=n%3A13921051",
    "Maison & Cuisine": "https://www.amazon.fr/s?i=kitchen&rh=n%3A57004031",
    "Jouets & Jeux": "https://www.amazon.fr/s?i=toys&rh=n%3A322086011",
    "Beauté": "https://www.amazon.fr/s?i=beauty&rh=n%3A197858031",
    "Mode": "https://www.amazon.fr/s?i=fashion&rh=n%3A1571263031",
    "Bricolage": "https://www.amazon.fr/s?i=diy&rh=n%3A590748031",
    "Jeux Vidéo": "https://www.amazon.fr/s?i=videogames&rh=n%3A53049031",
    "Informatique": "https://www.amazon.fr/s?i=computers&rh=n%3A340858031",
    "Sports & Loisirs": "https://www.amazon.fr/s?i=sports&rh=n%3A325614031",
    "Auto & Moto": "https://www.amazon.fr/s?i=automotive&rh=n%3A1571267031"
}

def scan_category(url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "fr-FR,fr;q=0.9"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    products = soup.find_all("div", {"data-component-type": "s-search-result"})

    for product in products:
        try:
            title = product.h2.get_text(strip=True)
            url_product = "https://www.amazon.fr" + product.h2.a["href"]

            price_whole = product.select_one("span.a-price-whole")
            price_fraction = product.select_one("span.a-price-fraction")
            price_old = product.select_one("span.a-text-price span.a-offscreen")

            if price_whole and price_fraction and price_old:
                price_current = float((price_whole.get_text() + "." + price_fraction.get_text()).replace(",", ".").replace("€", ""))
                price_old_value = float(price_old.get_text().replace(",", ".").replace("€", "").strip())

                if price_old_value > price_current:
                    reduction = round((price_old_value - price_current) / price_old_value * 100)

                    if reduction >= 50:
                        results.append(f"**{title}**\nAncien prix: {price_old_value} €\nPrix actuel: {price_current} €\nRéduction: -{reduction}%\n{url_product}")

        except Exception as e:
            print("Erreur sur un produit:", e)

    return results

def send_category_menu(chat_id):
    buttons = [[InlineKeyboardButton(text=name, callback_data=url)] for name, url in CATEGORIES.items()]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    bot.sendMessage(chat_id, "Choisis une catégorie à scanner :", reply_markup=markup)

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if chat_id != TELEGRAM_USER_ID:
        return

    if content_type == "text":
        if msg["text"].lower() == "/start":
            bot.sendMessage(chat_id, "Bienvenue dans le bot Amazon Promo !\n\nCommandes disponibles :\n/start - Voir le menu\n/categories - Scanner une catégorie")
            send_category_menu(chat_id)
        elif msg["text"].lower() == "/categories":
            send_category_menu(chat_id)
        elif msg["text"].lower() == "/help":
            bot.sendMessage(chat_id, "/start - Menu général\n/categories - Choisir une catégorie\n/help - Aide")

def on_callback(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor="callback_query")
    bot.answerCallbackQuery(query_id, text="Scan en cours...")
    promos = scan_category(query_data)
    if promos:
        for promo in promos:
            bot.sendMessage(from_id, promo, parse_mode="Markdown")
    else:
        bot.sendMessage(from_id, "Aucune promo à -50% ou plus trouvée dans cette catégorie.")

MessageLoop(bot, {'chat': handle, 'callback_query': on_callback}).run_as_thread()

while True:
    time.sleep(10)
