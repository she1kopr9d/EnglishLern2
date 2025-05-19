import os
import requests

def translate_word(word):
    # Используем бесплатный API LibreTranslate (или замените на свой)
    url = f'http://translate:8000/translate?sl=en&dl=ru&text={word}'
    try:
        response = requests.get(url, timeout=5)
        if response.ok:
            return response.json().get('destination-text', '')
    except Exception as e:
        print(str(e))
    return '[ошибка перевода]'

def get_next_reminder_time(interval):
    # Интервал увеличивается по экспоненте (1, 2, 4, 8, ... минут)
    return interval * 2
