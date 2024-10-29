
import requests
import time
import re
from docx import Document
import os
from dotenv import load_dotenv

load_dotenv()
# Ключи API
bannerbear_api_key = os.getenv("BANNERBEAR_API_KEY")
yandex_api_key = os.getenv("YANDEX_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")
bannerbear_template_id = os.getenv("BANNERBEAR_TEMPLATE_ID")
project_id = os.getenv("PROJECT_ID")

# Функция для поиска новостей
def search_google_news(api_key, cse_id, query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": api_key, "cx": cse_id, "q": query, "num": 1, "sort": "date"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json().get("items", [])
        if results:
            return results[0]["snippet"]
    else:
        print("Error:", response.status_code)
    return None

# Функция для создания краткого текста
def get_summary_from_gpt(api_key, prompt_text):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {"Content-Type": "application/json", "Authorization": f"Api-Key {api_key}"}
    prompt = {
        "modelUri": "gpt://b1g3i9dumtvjht2ol0bj/yandexgpt-lite",
        "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": 200},
        "messages": [
            {"role": "system", "text": "Создай краткий, но содержательный текст, подходящий для блога."},
            {"role": "user", "text": prompt_text}
        ]
    }
    response = requests.post(url, headers=headers, json=prompt)
    if response.status_code == 200:
        data = response.json()
        return data["result"]["alternatives"][0]["message"]["text"]
    else:
        print("Error fetching summary:", response.status_code)
    return None

# Функция для извлечения и очистки слогана
def extract_slogan(summary):
    slogan = summary.split('\n')[0].strip()
    cleaned_slogan = re.sub(r'[*#]', '', slogan)
    return cleaned_slogan.strip()

# Функция для создания баннера
def create_banner_with_slogan(slogan):
    url = "https://api.bannerbear.com/v2/images"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {bannerbear_api_key}"}
    data = {
        "template": bannerbear_template_id,
        "project_id": project_id,
        "modifications": [
            {"name": "title", "text": slogan},
            {"name": "avatar", "image_url": "https://www.bannerbear.com/assets/sample_avatar.jpg"}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 202:
        image_uid = response.json()["uid"]
        return check_banner_status(image_uid)
    else:
        print("Error creating banner:", response.status_code, response.json())
    return None

# Функция для проверки статуса баннера
def check_banner_status(image_uid):
    url = f"https://api.bannerbear.com/v2/images/{image_uid}"
    headers = {"Authorization": f"Bearer {bannerbear_api_key}"}
    
    while True:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if response.status_code == 200:
            if "status" in data and data["status"] == "completed":                
                return data["image_url"]
            elif "status" in data and data["status"] == "pending":
                print("Rendering in progress, rechecking in 5 seconds...")
                time.sleep(5)
            else:
                print("Unexpected response data:", data)
                return None
        else:
            print("Error checking status:", response.status_code, data)
            return None

# Функция для сохранения текста блога в .docx
def save_blog_to_docx(summary, filename="blog_text.docx"):
    doc = Document()
    doc.add_paragraph(summary)
    doc.save(filename)
    print(f"Blog text saved to {filename}")

# Функция для сохранения изображения
def save_image(url, filename="banner_image.jpg"):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Image saved to {filename}")
    else:
        print("Error downloading image:", response.status_code)

# Функция для сохранения текста слогана
def save_slogan_to_file(slogan, filename="slogan_text.txt"):
    with open(filename, "w") as f:
        f.write(slogan)
    print(f"Slogan text saved to {filename}")

# Основной процесс
description = search_google_news(google_api_key, google_cse_id, "раннее обучение детей арифметике, скорочтению и их польза")
if description:
    summary = get_summary_from_gpt(yandex_api_key, description)
    if summary:        
        slogan = extract_slogan(summary)       
        
        # Создаем баннер
        banner_url = create_banner_with_slogan(slogan)
        if banner_url:            

            # Сохраняем результаты
            save_blog_to_docx(summary)               # Сохранение текста блога
            save_image(banner_url)                   # Сохранение изображения
            save_slogan_to_file(slogan)              # Сохранение текста слогана
