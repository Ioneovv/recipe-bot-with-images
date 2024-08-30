import os
import requests
from dotenv import load_dotenv

# Загрузите переменные окружения
load_dotenv()

IMAGE_API_URL = os.getenv('IMAGE_API_URL')
IMAGE_API_KEY = os.getenv('IMAGE_API_KEY')

def generate_image(prompt):
    headers = {
        'Authorization': f'Bearer {IMAGE_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'prompt': prompt,
        'negative_prompt': '',  # Необязательный параметр
        'width': 512,
        'height': 512,
        'samples': 1,  # Количество изображений
        'seed': None,  # Необязательный параметр, если нужен фиксированный результат
        'webhook': None,  # Необязательный параметр для получения уведомлений
        'track_id': None  # Необязательный параметр для отслеживания
    }
    response = requests.post(IMAGE_API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        image_url = result.get('output', [])[0]  # Предполагаем, что API возвращает список URL
        return image_url
    else:
        print(f"Ошибка при генерации изображения: {response.status_code}, {response.text}")
        return None

