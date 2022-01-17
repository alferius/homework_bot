import os

from dotenv import load_dotenv

from homework import get_api_answer

load_dotenv()
PRACTICUM_TOKEN = os.getenv('HOMEWORK_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAMM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')


print(get_api_answer(1639977855))
