import json
import logging
import random
import asyncio
import os
import requests
from telegram import Bot, InputFile
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv
from git import Repo

# Загрузите переменные окружения
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHANNEL_ID')
IMAGE_API_URL = os.getenv('IMAGE_API_URL')
IMAGE_API_KEY = os.getenv('IMAGE_API_KEY')
RECIPES_REPO_URL = os.getenv('RECIPES_REPO_URL')
RECIPES_FILE_PATH = os.getenv('RECIPES_FILE_PATH')

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
    response = requests.post(IMAGE_API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        image_url = result.get('output', [])[0]
        return image_url
    else:
        logging.error(f"Ошибка при генерации изображения: {response.status_code}, {response.text}")
        return None

# Загрузка рецептов из внешнего репозитория
def load_recipes():
    repo = Repo.clone_from(RECIPES_REPO_URL, '/tmp/recipes_repo')
    file_path = f'/tmp/recipes_repo/{RECIPES_FILE_PATH}'
    with open(file_path, 'r', encoding='utf-8') as file:
        recipes = json.load(file)
        logging.info(f"Рецепты загружены: {len(recipes)} рецептов")
        return recipes

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

async def periodic_task(bot, chat_id, interval_hours=8):
    while True:
        try:
            recipes = load_recipes()
            if not recipes:
                logging.info("Рецепты не найдены.")
                await asyncio.sleep(interval_hours * 3600)
                continue

            recipe = random.choice(recipes)
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

            logging.info("Запуск периодической задачи.")
            task = asyncio.create_task(periodic_task(application.bot, CHAT_ID))

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
