import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import requests
from bs4 import BeautifulSoup

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Вставте ваш токен і ID каналу
TOKEN = "7978500466:AAFc3SRL6NpBjLK8i6KeGftjGvpK6V2vOos"
CHANNEL_ID = "@passion_for_fashion_ukraine"

# Курс валют
USD_TO_UAH = 43  # Вставте актуальний курс

async def start(update, context):
    """Обробник команди /start"""
    logger.info("Отримана команда /start")
    await update.message.reply_text("Привіт! Надішліть мені посилання на товар.")

def calculate_price(price_usd):
    """Прорахунок ціни з націнкою"""
    logger.info(f"Розрахунок ціни для {price_usd} USD")
    markup = 0.18 if price_usd < 50 else 0.15
    price_uah = (price_usd + (price_usd * markup)) * USD_TO_UAH
    return round(price_uah, 2)
    
def parse_coach_outlet(url):
    """Парсинг сайту Coach Outlet"""
    logger.info(f"Парсинг URL: {url}")
    try:
        # Завантаження сторінки
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logger.error(f"Помилка завантаження сторінки: {response.status_code}")
            raise Exception(f"Не вдалося завантажити сторінку. Код статусу: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        logger.info(soup.prettify())  # Виводимо HTML-структуру

        # Назва товару
        name_tag = soup.find("span", {"data-qa": "pdp_txt_pdt_title"})
        if not name_tag:
            logger.error("Назва товару не знайдена.")
            raise Exception("Не вдалося знайти назву товару.")
        name = name_tag.text.strip()
        logger.info(f"Знайдено назву: {name}")

        # Ціна товару
        price_tag = soup.find("span", {"data-qa": "cm_txt_pdt_price"})
        if not price_tag:
            logger.error("Ціна товару не знайдена.")
            raise Exception("Не вдалося знайти ціну товару.")
        price_text = price_tag.text.strip()
        price_usd = float(price_text.replace("$", "").replace(",", ""))
        logger.info(f"Знайдено ціну: {price_usd} USD")

        # Фото товару
        image_tag = soup.find("img", {"class": "product-thumbnails-slider"})
        if not image_tag or not image_tag.get('src'):
            logger.error("Зображення товару не знайдено.")
            raise Exception("Не вдалося знайти зображення товару.")
        image_url = image_tag['src']
        logger.info(f"Знайдено зображення: {image_url}")

        logger.info(f"Парсинг завершено: {name}, {price_usd} USD")
        return {
            "name": name,
            "price_usd": price_usd,
            "image": image_url,
            "description": "Опис товару відсутній",  # За бажанням можна доповнити
        }

    except requests.exceptions.Timeout:
        logger.error("Тайм-аут під час завантаження сторінки.")
        raise Exception("Сервер не відповідає. Спробуйте пізніше.")
    except Exception as e:
        logger.error(f"Помилка парсингу: {e}")
        raise


    

def parse_michael_kors(url):
    """Парсинг сайту Michael Kors"""
    logger.info(f"Парсинг URL: {url}")

    response = requests.get(url, timeout=10)
   


    if response.status_code != 200:
        logger.error(f"Помилка завантаження сторінки: {response.status_code}")
        raise Exception("Не вдалося завантажити сторінку")

    soup = BeautifulSoup(response.content, 'html.parser')

    # Назва товару
    name = soup.find("h1", {"class": "product-name"}).text.strip()

    # Ціна товару
    price_text = soup.find("span", {"class": "price"}).text.strip()
    price_usd = float(price_text.replace("$", "").replace(",", ""))

    # Фото товару
    image_url = soup.find("img", {"class": "product-gallery__image"})['src']

    logger.info(f"Парсинг завершено: {name}, {price_usd} USD")
    return {
        "name": name,
        "price_usd": price_usd,
        "image": image_url,
        "description": "Опис товару відсутній",  # Опис можна додати, якщо знайдете
    }

async def post_to_channel(update, context):
    """Отримання посилання та публікація товару в канал"""
    url = update.message.text
    logger.info(f"Отримано посилання: {url}")
    try:
        # Визначаємо, з якого сайту парсити
        if "michaelkors.com" in url:
            product_info = parse_michael_kors(url)
        elif "coachoutlet.com" in url:
            product_info = parse_coach_outlet(url)    
        else:
            await update.message.reply_text("На жаль, цей сайт поки не підтримується.")
            return

        # Розрахунок ціни
        price_uah = calculate_price(product_info['price_usd'])

        # Формуємо повідомлення
        message = f"{product_info['name']}\nЦіна: {price_uah} грн\n{product_info['description']}"
        
        # Публікація в канал
        await context.bot.send_photo(chat_id=CHANNEL_ID, photo=product_info['image'], caption=message)
        await update.message.reply_text("Товар успішно опубліковано!")
    except Exception as e:
        logger.error(f"Помилка обробки: {e}")
        await update.message.reply_text(f"Помилка: {e}")

# Запускаємо бота
def main():
    logger.info("Запуск бота")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, post_to_channel))

    app.run_polling()

if __name__ == "__main__":
    main()
