import requests
from bs4 import BeautifulSoup
import re
import json
import urllib3
import time
from config import COOKIES

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://incloudgame.ru',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def get_csrf_token():
    """Получаем свежий CSRF-токен"""
    session = requests.Session()
    session.cookies.update(COOKIES)

    headers = HEADERS.copy()
    headers['Referer'] = 'https://incloudgame.ru/'

    try:
        response = session.get(
            'https://incloudgame.ru/store',
            headers=headers,
            timeout=10,
            verify=False
        )
    except Exception as e:
        return None, None

    if response.status_code != 200:
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Способ 1: input с name="_token"
    token_input = soup.find('input', {'name': '_token'})
    if token_input and token_input.get('value'):
        return token_input['value'], session

    # Способ 2: meta-тег
    meta_token = soup.find('meta', {'name': 'csrf-token'})
    if meta_token and meta_token.get('content'):
        return meta_token['content'], session

    # Способ 3: регулярное выражение
    match = re.search(r'name="_token"\s+value="([^"]+)"', response.text)
    if match:
        return match.group(1), session

    return None, None

def create_payment(amount):
    """Создает платеж и возвращает ссылку на оплату"""

    # Получаем токен
    csrf_token, session = get_csrf_token()
    if not csrf_token:
        return None, "Не удалось получить CSRF-токен"

    # Шаг 1: Создаем заказ
    data = {
        '_token': csrf_token,
        'full_total': '',
        'plan_discount_percent': '0',
        'total': str(amount),
    }

    headers = HEADERS.copy()
    headers['Referer'] = 'https://incloudgame.ru/store'

    try:
        response = session.post(
            'https://incloudgame.ru/store/add',
            headers=headers,
            data=data,
            allow_redirects=False,
            timeout=10,
            verify=False
        )
    except Exception as e:
        return None, f"Ошибка запроса: {e}"

    if response.status_code != 302:
        return None, f"Ошибка создания заказа: {response.status_code}"

    # Получаем product_id
    location = response.headers.get('Location')
    if not location:
        return None, "Не получен редирект"

    product_id = location.split('/')[-1]

    # Обновляем куки
    new_cookies = session.cookies.get_dict()
    COOKIES.update(new_cookies)

    time.sleep(0.5)

    # Шаг 2: Отправляем запрос на оплату
    checkout_url = f'https://incloudgame.ru/checkout/{product_id}'
    headers = HEADERS.copy()
    headers['Referer'] = 'https://incloudgame.ru/store'

    try:
        response = session.get(checkout_url, headers=headers, timeout=10, verify=False)
    except Exception as e:
        return None, f"Ошибка загрузки чекаута: {e}"

    # Получаем CSRF-токен со страницы чекаута
    soup = BeautifulSoup(response.text, 'html.parser')
    pay_token = None

    token_input = soup.find('input', {'name': '_token'})
    if token_input and token_input.get('value'):
        pay_token = token_input['value']

    if not pay_token:
        return None, "Не найден CSRF-токен на странице чекаута"

    # Данные для оплаты
    data = {
        '_token': pay_token,
        '_method': 'post',
        'payment_method': 'Yookassa',
        'product_id': product_id,
        'payment_method': 'Yookassa',
    }

    headers = HEADERS.copy()
    headers['Referer'] = checkout_url

    try:
        response = session.post(
            'https://incloudgame.ru/payment/pay',
            headers=headers,
            data=data,
            allow_redirects=False,
            timeout=10,
            verify=False
        )
    except Exception as e:
        return None, f"Ошибка оплаты: {e}"

    if response.status_code != 302:
        return None, f"Ошибка оплаты: {response.status_code}"

    yookassa_url = response.headers.get('Location')
    if not yookassa_url:
        return None, "Не получена ссылка на оплату"

    time.sleep(0.5)

    # Шаг 3: Получаем ссылку на ЮMoney
    headers = HEADERS.copy()
    headers['Referer'] = 'https://incloudgame.ru/payment/pay'

    try:
        response = session.get(
            yookassa_url,
            headers=headers,
            allow_redirects=False,
            timeout=10,
            verify=False
        )
    except Exception as e:
        return None, f"Ошибка перехода на ЮKassa: {e}"

    if response.status_code != 302:
        return None, f"Не удалось получить редирект на ЮMoney: {response.status_code}"

    yoomoney_url = response.headers.get('Location')
    if not yoomoney_url:
        return None, "Не получена ссылка на ЮMoney"

    return yoomoney_url, None