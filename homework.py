import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('HOMEWORK_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAMM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
old_message = ""


def send_message(bot, message):
    """Отправка сообщения в Телегу."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Успешная отправка сообщения.')
    except Exception as error:
        raise SystemError(f"Не отправляются сообщения, {error}")


def get_api_answer(current_timestamp):
    """запрос статуса домашней работы."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework_statuses.status_code == 200:
        logger.info("успешное получение Эндпоинта")
        return homework_statuses.json()
    elif homework_statuses.status_code == 500:
        raise SystemError(f"Ошибка код {homework_statuses.status_code}")
    elif homework_statuses.status_code == 408:
        raise SystemError(f"Ошибка код {homework_statuses.status_code}")
    # не понимаю зачем проверять отдельно 408 и 500, если всё попадёт в else
    else:
        raise SystemError(
            f"Недоступен Эндпоинт, код {homework_statuses.status_code}")


def check_response(response):
    """проверка ответа на корректность."""
    if type(response) == dict:
        # проверка доступности ключа 'current_date'
        response['current_date']
        homeworks = response['homeworks']
        if type(homeworks) == list:
            return homeworks
        else:
            raise SystemError("Тип ключа homeworks не list")
    else:
        raise TypeError("Ответ от Домашки не словарь")


def parse_status(homework):
    """Парсинг информации о домашке."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_name is not None and homework_status is not None:
        if homework_status in HOMEWORK_STATUSES:
            verdict = HOMEWORK_STATUSES.get(homework_status)
            return ('Изменился статус проверки '
                    + f'работы "{homework_name}". {verdict}')
        else:
            raise SystemError("неизвестный статус")
    else:
        raise KeyError("нет нужных ключей в словаре")


def check_tokens():
    """Проверка доступности необходимых токенов."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.critical("Ошибка импорта токенов Telegramm.")
        return False
    elif not PRACTICUM_TOKEN:
        raise SystemError("Ошибка импорта токенов Домашки.")
    else:
        return True


def main():
    """Бот для отслеживания статуса домашки на Яндекс.Домашка."""
    global old_message
    if not check_tokens():
        raise SystemExit('Я вышел')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - RETRY_TIME

    while True:
        try:
            response = get_api_answer(current_timestamp)
            response = check_response(response)

            if len(response) > 0:
                homework_status = parse_status(response[0])
                if homework_status is not None:
                    send_message(bot, homework_status)
            else:
                logger.debug('нет новых статусов')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != old_message:
                bot.send_message(TELEGRAM_CHAT_ID, message)
                old_message = message
        else:
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
