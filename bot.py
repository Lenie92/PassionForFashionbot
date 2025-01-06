from telegram import Bot
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater
import requests
from bs4 import BeautifulSoup

# Вставте ваш токен і ID каналу
TOKEN = "7978500466:AAFc3SRL6NpBjLK8i6KeGftjGvpK6V2vOos"
CHANNEL_ID = "@passion_for_fashion_ukraine"

# Курс валют
USD_TO_UAH = 43  # Вставте актуальний курс

def start(update, context):
    update.message.reply_text("Привіт! Надішліть мені посилання на товар.")

def calculate_price(price_usd):
    """Прорахунок ціни з націнкою"""
    markup = 0.18 if price_usd < 50 else 0.15
    price_uah = (price_usd + (price_usd * markup)) * USD_TO_UAH
    return round(price_uah, 2)

def parse_michael_kors(url):
    """Парсинг сайту Michael Kors"""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Назва товару
    name = soup.find("h1", {"class": "product-name"}).text.strip()
    
    # Ціна товару
    price_text = soup.find("span", {"class": "price"}).text.strip()
    price_usd = float(price_text.replace("$", "").replace(",", ""))
    
    # Фото товару
    image_url = soup.find("img", {"class": "product-gallery__image"})['src']
    
    return {
        "name": name,
        "price_usd": price_usd,
        "image": image_url,
        "description": "Опис товару відсутній",  # Опис можна додати, якщо знайдете
    }

def post_to_channel(update, context):
    """Отримання посилання та публікація товару в канал"""
    url = update.message.text
    try:
        # Визначаємо, з якого сайту парсити
        if "michaelkors.com" in url:
            product_info = parse_michael_kors(url)
        else:
            update.message.reply_text("На жаль, цей сайт поки не підтримується.")
            return

        # Розрахунок ціни
        price_uah = calculate_price(product_info['price_usd'])

        # Формуємо повідомлення
        message = f"{product_info['name']}\nЦіна: {price_uah} грн\n{product_info['description']}"
        
        # Публікація в канал
        context.bot.send_photo(chat_id=CHANNEL_ID, photo=product_info['image'], caption=message)
        update.message.reply_text("Товар успішно опубліковано!")
    except Exception as e:
        update.message.reply_text(f"Помилка: {e}")

# Запускаємо бота
if __name__ == "__main__":
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, post_to_channel))

    updater.start_polling()
    updater.idle()
