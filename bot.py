# ========== ТЕСТ СЕТИ (ДОБАВИТЬ В НАЧАЛО) ==========
import socket
import requests

def test_network():
    print("\n" + "="*50)
    print("🌐 ТЕСТ СЕТИ")
    print("="*50)
    
    # 1. Проверка DNS
    try:
        ip = socket.gethostbyname('panel.incloudgame.ru')
        print(f"✅ DNS: panel.incloudgame.ru -> {ip}")
    except Exception as e:
        print(f"❌ DNS ошибка: {e}")
    
    # 2. Проверка порта 443
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('panel.incloudgame.ru', 443))
        sock.close()
        if result == 0:
            print("✅ Порт 443 открыт")
        else:
            print(f"❌ Порт 443 закрыт (код: {result})")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # 3. Проверка HTTP запроса
    try:
        response = requests.get(
            'https://panel.incloudgame.ru',
            timeout=10,
            verify=False
        )
        print(f"✅ HTTP статус: {response.status_code}")
    except Exception as e:
        print(f"❌ HTTP ошибка: {e}")
    
    print("="*50)

# Запускаем тест при старте
test_network()