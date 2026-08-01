import requests
import websocket
import json
import urllib3
import time
import sys

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== КУКИ ==========
COOKIES = {
    '__ddg1_': '9XPjSXZG9a6WDFAprBid',
    '_ym_uid': '1783955517502440301',
    '_ym_d': '1783955517',
    '_ym_isad': '2',
    '__ddg8_': 'gQl3ekHFWy5Eq7po',
    '__ddg9_': '104.28.165.101',
    '__ddg10_': '1785591321',
    '_ym_visorc': 'w',
    'XSRF-TOKEN': 'eyJpdiI6IjNybC9tNWNKdU4yVTZpL1BBbVhLRHc9PSIsInZhbHVlIjoiZ3VGMWpVNmFsVEpJMTV2azJSRGxlaHh5NHBKejIwRzVMMHMwc1NNeUZnS3NRTVZTOE9qME1DVks5bVBCRDBVOTd3T21oOTFPQS9qWWVXUXlZWmh0T0RoZnlyRXA5dzJmWHlRRlIzQUJvZUxKNm1wNURRRUJLTG1TUkQ3a0NCQTUiLCJtYWMiOiIyNmI1Mzc1NzFlMjM4MTlmYWQ4MmQ0ZmU5NTZjODk1YTgxMTg1NmJhODlmNWZhOWZkN2YzNzc0MmM2ZDk5ODZmIiwidGFnIjoiIn0%3D',
    'pterodactyl_session': 'eyJpdiI6IjhYbzRBRUlBcEE2N1hZN0toVnZlakE9PSIsInZhbHVlIjoidzBlTk1wQnJ2RVZzT0Vxc1gwcUhMRnJJTXdSbVlkbWJMeS80UCsrRStEN1BtNHhOUEpZSDZidE9FUjVZd2k0OE1Ea2k3YkdLNlQ4LzFaQXIzSWxndUgzek1hQVN2T1hFNHVoZlZ2eWhZSm1ldmxrTzR4VUJlbFllaDc2SUplOGoiLCJtYWMiOiJmMmE3MTVlMjgyMWVhODI3Y2UwZWZjZDU1YjE2MDgwNDU0ZGU5Y2FkMmVkZjc3NWQ2NjU4MGFjZDk2NmM0NmU5IiwidGFnIjoiIn0%3D',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'Content-Type': 'application/json',
    'Origin': 'https://panel.incloudgame.ru',
    'Connection': 'keep-alive',
    'Referer': 'https://panel.incloudgame.ru/',
}

SERVER_ID = "6952da89-092d-410b-be22-d2e4efd713f0"

def get_websocket_token():
    """Получает WebSocket токен"""
    
    session = requests.Session()
    session.cookies.update(COOKIES)
    
    headers = HEADERS.copy()
    headers['X-CSRF-TOKEN'] = COOKIES.get('XSRF-TOKEN', '')
    
    url = f"https://panel.incloudgame.ru/api/client/servers/{SERVER_ID}/websocket"
    
    try:
        response = session.get(url, headers=headers, timeout=10, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('data', {}).get('token')
            socket_url = data.get('data', {}).get('socket')
            session.cookies.update(COOKIES)
            return token, socket_url, session.cookies
        else:
            return None, None, None
    except Exception as e:
        return None, None, None

def start_server():
    """Запускает сервер через WebSocket"""
    
    print("🚀 Запуск сервера...")
    
    try:
        ws_token, ws_url, cookies = get_websocket_token()
        
        if not ws_token:
            print("❌ Не удалось получить токен")
            return False
        
        cookie_string = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        headers = [
            f"User-Agent: {HEADERS['User-Agent']}",
            "Origin: https://panel.incloudgame.ru",
            f"Cookie: {cookie_string}",
            "X-CSRF-TOKEN: " + COOKIES.get('XSRF-TOKEN', ''),
        ]
        
        ws = websocket.create_connection(
            ws_url,
            header=headers,
            timeout=15,
            sslopt={"cert_reqs": 0},
            origin="https://panel.incloudgame.ru"
        )
        
        ws.send(json.dumps({"event": "auth", "args": [ws_token]}))
        time.sleep(1)
        
        try:
            response = ws.recv()
            if "auth success" not in response:
                ws.close()
                print("❌ Ошибка аутентификации")
                return False
        except:
            ws.close()
            print("❌ Нет ответа от сервера")
            return False
        
        ws.send(json.dumps({
            "event": "set state",
            "args": ["start"]
        }))
        
        time.sleep(2)
        ws.close()
        
        print("✅ Сервер запущен!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("🚀 ЗАПУСК СЕРВЕРА")
    print("="*50)
    start_server()