import json
import logging
import random
import asyncio
import os
from telegram import Bot, InputFile
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv
import requests

# Загрузите переменные окружения
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHANNEL_ID')
IMAGE_API_URL = os.getenv('IMAGE_API_URL')
IMAGE_API_KEY = os.getenv('IMAGE_API_KEY')

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# Функция генерации изображения
def generate_image(prompt):
    headers = {
        'Authorization': f'Bearer {IMAGE_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'prompt': prompt,
        'width': 512,
        'height': 512,
        'samples': 1
    }
    try:
        response = requests.post(IMAGE_API_URL, headers=headers, json=data)
        response.raise_for_status()  # Проверка на успешный статус код
        result = response.json()
        image_url = result.get('output', [])[0]
        return image_url
    except requests.RequestException as e:
        logging.error(f"Ошибка при генерации изображения: {e}")
        return None

# Форматирование текста рецепта
def format_recipe(recipe):
    formatted = recipe.get('title', 'Без названия') + '\n\n'
    formatted += '\n'.join(f"{item['ingredient']} - {item['amount']}" for item in recipe.get('ingredients', [])) + '\n\n'
    formatted += '\n'.join(recipe.get('instructions', []))
    return formatted

# Асинхронная отправка сообщения и изображения в канал
async def send_recipe_with_image(bot, chat_id, recipe):
    formatted_text = format_recipe(recipe)
    image_url = generate_image(recipe.get('title', 'Recipe'))
    
    try:
        if image_url:
            await bot.send_photo(chat_id=chat_id, photo=image_url, caption=formatted_text)
        else:
            await bot.send_message(chat_id=chat_id, text=formatted_text)
        logging.info("Сообщение и изображение успешно отправлены.")
    except TelegramError as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")

# Асинхронная функция для выполнения задач в заданное время
async def periodic_task(bot, chat_id, recipes, interval_hours=8):
    while True:
        try:
            if not recipes:
                logging.info("Рецепты закончились. Перезагружаем список...")
                recipes.extend(load_recipes())

            recipe = random.choice(recipes)
            recipes.remove(recipe)
            await send_recipe_with_image(bot, chat_id, recipe)

            logging.info(f"Следующее сообщение будет отправлено через {interval_hours} часов.")
            await asyncio.sleep(interval_hours * 3600)
        except Exception as e:
            logging.error(f"Произошла ошибка в периодической задаче: {e}")
            await asyncio.sleep(60)

async def main():
    while True:
        try:
            application = ApplicationBuilder().token(TOKEN).build()
            recipes = load_recipes()

            logging.info("Запуск периодической задачи.")
            task = asyncio.create_task(periodic_task(application.bot, CHAT_ID, recipes))

            await application.start()
            await task
        except Exception as e:
            logging.error(f"Произошла ошибка в основном цикле: {e}")
            await asyncio.sleep(60)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Произошла ошибка при запуске основного цикла: {e}")
