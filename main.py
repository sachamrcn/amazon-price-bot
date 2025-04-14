
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

BASE_URL = "https://www.amazon.fr"

def get_categories():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "fr-FR,fr;q=0.9"
    }
    response = requests.get(BASE_URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    nav = soup.select("div.nav-template.nav-flyout-content a.nav_a")
    
    categories = []
    for link in nav:
        name = link.get_text(strip=True)
        href = link.get("href")
        if name and href and "/s?" in href:
            full_url = BASE_URL + href
            categories.append((name, full_url))
        if len(categories) >= 10:
            break
    return categories

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
            url_product = BASE_URL + product.h2.a["href"]

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

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if chat_id != TELEGRAM_USER_ID:
        return

    if content_type == "text":
        if msg["text"].lower() == "/categories":
            cat_list = get_categories()
            if not cat_list:
                bot.sendMessage(chat_id, "Impossible de récupérer les catégories.")
                return

            buttons = [[InlineKeyboardButton(text=name, callback_data=url)] for name, url in cat_list]
            markup = InlineKeyboardMarkup(inline_keyboard=buttons)
            bot.sendMessage(chat_id, "Choisis une catégorie :", reply_markup=markup)

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
