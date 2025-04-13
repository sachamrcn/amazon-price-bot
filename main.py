
import os
import time
import requests
from bs4 import BeautifulSoup
import telepot

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = int(os.getenv("TELEGRAM_USER_ID"))
bot = telepot.Bot(TELEGRAM_BOT_TOKEN)

def check_price():
    product_url = "https://www.amazon.fr/dp/B093BZCZR4"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9"
    }

    try:
        response = requests.get(product_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find(id="productTitle").get_text(strip=True) if soup.find(id="productTitle") else "Titre non trouvé"
        price_block = soup.find("span", class_="a-price-whole")
        price_fraction = soup.find("span", class_="a-price-fraction")
        price_current = f"{price_block.get_text(strip=True)}.{price_fraction.get_text(strip=True)}" if price_block and price_fraction else None
        price_old_span = soup.find("span", class_="a-text-strike")
        price_old_text = price_old_span.get_text(strip=True).replace("€", "").replace(",", ".") if price_old_span else None

        price_current_float = float(price_current.replace("€", "").replace(",", ".")) if price_current else None
        price_old_float = float(price_old_text) if price_old_text else None

        if price_current_float and price_old_float and price_old_float > price_current_float:
            reduction = round((price_old_float - price_current_float) / price_old_float * 100)
        else:
            reduction = 0

        if reduction >= 70:
            message = (
                "[ALERTE AMAZON -70%+]\n\n"
                f"Nom : {title}\n"
                f"Ancien prix : {price_old_float} €\n"
                f"Prix actuel : {price_current_float} €\n"
                f"Réduction : -{reduction}%\n\n"
                f"Lien : {product_url}"
            )
            bot.sendMessage(TELEGRAM_USER_ID, message)
        else:
            print(f"Aucune promo >70% trouvée : {title} - {reduction}%")

    except Exception as e:
        print(f"Erreur dans le scraping : {e}")

# Boucle infinie toutes les 10 minutes
if __name__ == "__main__":
    while True:
        check_price()
        time.sleep(600)
