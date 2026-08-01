import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import requests
import urllib3
import websocket
import time
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== ТОКЕН ==========
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

if not DISCORD_TOKEN:
    print("❌ ТОКЕН НЕ НАЙДЕН!")
    exit(1)

# ========== НАСТРОЙКА ==========
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

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

# ========== ПРОВЕРКА СЕССИИ ==========

def check_session():
    """Проверяет, жива ли сессия через API запрос"""
    
    try:
        session = requests.Session()
        session.cookies.update(COOKIES)
        
        headers = HEADERS.copy()
        headers['X-CSRF-TOKEN'] = COOKIES.get('XSRF-TOKEN', '')
        
        url = f"https://panel.incloudgame.ru/api/client/servers/{SERVER_ID}"
        
        response = session.get(
            url,
            headers=headers,
            timeout=10,
            verify=False
        )
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Ошибка проверки сессии: {e}")
        return False

# ========== ФУНКЦИЯ ОБНОВЛЕНИЯ КУК ИЗ JSON ==========

def update_cookies_from_json(json_data):
    """Обновляет куки из JSON строки"""
    
    try:
        # Парсим JSON
        if isinstance(json_data, str):
            cookies_data = json.loads(json_data)
        else:
            cookies_data = json_data
        
        # Обновляем куки
        for key, value in cookies_data.items():
            COOKIES[key] = value
        
        print(f"✅ Куки обновлены! ({len(COOKIES)} кук)")
        return True, "✅ Куки успешно обновлены!"
        
    except json.JSONDecodeError as e:
        return False, f"❌ Ошибка парсинга JSON: {e}"
    except Exception as e:
        return False, f"❌ Ошибка: {e}"

# ========== ФУНКЦИИ РАБОТЫ С СЕРВЕРОМ ==========

def get_csrf_token():
    """Получает CSRF-токен"""
    
    session = requests.Session()
    session.cookies.update(COOKIES)
    
    try:
        response = session.get(
            'https://panel.incloudgame.ru',
            headers=HEADERS,
            timeout=10,
            verify=False
        )
        
        soup = BeautifulSoup(response.text, 'html.parser')
        meta = soup.find('meta', {'name': 'csrf-token'})
        
        if meta and meta.get('content'):
            return meta.get('content'), session
            
        csrf_token = session.cookies.get('XSRF-TOKEN')
        if csrf_token:
            return csrf_token, session
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return None, None

def accept_eula():
    """Принимает EULA"""
    
    csrf_token, session = get_csrf_token()
    
    if not csrf_token:
        return False
    
    url = f"https://panel.incloudgame.ru/api/client/servers/{SERVER_ID}/files/write"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://panel.incloudgame.ru',
        'Connection': 'keep-alive',
        'Referer': f'https://panel.incloudgame.ru/server/{SERVER_ID}/files',
        'X-CSRF-TOKEN': csrf_token,
    }
    
    try:
        response = requests.post(
            url,
            params={"file": "eula.txt"},
            data="eula=true",
            headers=headers,
            timeout=10,
            verify=False
        )
        
        return response.status_code in [200, 201, 204]
        
    except Exception as e:
        print(f"❌ Ошибка EULA: {e}")
        return False

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

def send_server_command(command):
    """Отправляет команду на сервер"""
    
    # Проверяем сессию
    if not check_session():
        return False, "🔐 **СЕССИЯ ИСТЕКЛА!**\n\nВыберите способ обновления:\n1️⃣ Войти на сайт: https://incloudgame.ru/auth/login\n2️⃣ Использовать команду `/update_cookies` с JSON куками"
    
    try:
        if command == "start":
            accept_eula()
            time.sleep(1)
        
        ws_token, ws_url, cookies = get_websocket_token()
        
        if not ws_token:
            return False, "❌ Не удалось получить токен"
        
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
                return False, "❌ Ошибка аутентификации"
        except:
            ws.close()
            return False, "❌ Нет ответа от сервера"
        
        ws.send(json.dumps({
            "event": "set state",
            "args": [command]
        }))
        
        time.sleep(2)
        ws.close()
        
        return True, f"✅ Команда '{command}' отправлена!"
        
    except Exception as e:
        return False, f"❌ Ошибка: {str(e)}"

# ==================== КОМАНДЫ БОТА ====================

@bot.event
async def on_ready():
    print(f'✅ Бот запущен!')
    print(f'📌 Имя: {bot.user.name}')
    print(f'👥 На серверах: {len(bot.guilds)}')
    
    try:
        synced = await bot.tree.sync()
        print(f'✅ Синхронизировано {len(synced)} команд')
    except Exception as e:
        print(f'❌ Ошибка синхронизации: {e}')
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="/run | /stop"
        )
    )

@bot.tree.command(name="update_cookies", description="Обновить куки из JSON")
@app_commands.describe(cookies_json="JSON строка с куками из браузера")
async def update_cookies(interaction: discord.Interaction, cookies_json: str):
    """Обновляет куки из JSON строки"""
    
    await interaction.response.defer(ephemeral=True)
    
    success, message = update_cookies_from_json(cookies_json)
    
    embed = discord.Embed(
        title="🍪 Обновление кук" if success else "❌ Ошибка",
        description=message,
        color=discord.Color.green() if success else discord.Color.red(),
        timestamp=datetime.now()
    )
    
    if success:
        embed.add_field(
            name="📋 Текущие куки",
            value=f"Количество: {len(COOKIES)}\n"
                  f"`pterodactyl_session`: {COOKIES.get('pterodactyl_session', 'Нет')[:20]}...\n"
                  f"`XSRF-TOKEN`: {COOKIES.get('XSRF-TOKEN', 'Нет')[:20]}...",
            inline=False
        )
        embed.add_field(
            name="✅ Результат",
            value="Теперь можно использовать команды `/run`, `/stop` и `/restart`",
            inline=False
        )
    
    embed.set_footer(
        text=f"Запросил: {interaction.user.display_name}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="run", description="Запустить сервер")
async def run(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    success, message = send_server_command("start")
    
    embed = discord.Embed(
        title="🟢 Запуск сервера" if success else "⚠️ Ошибка",
        description=message,
        color=discord.Color.green() if success else discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.set_footer(
        text=f"Запросил: {interaction.user.display_name}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="stop", description="Остановить сервер")
async def stop(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    success, message = send_server_command("stop")
    
    embed = discord.Embed(
        title="🔴 Остановка сервера" if success else "⚠️ Ошибка",
        description=message,
        color=discord.Color.red() if success else discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.set_footer(
        text=f"Запросил: {interaction.user.display_name}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="restart", description="Перезапустить сервер")
async def restart(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    success, message = send_server_command("restart")
    
    embed = discord.Embed(
        title="🔄 Перезапуск сервера" if success else "⚠️ Ошибка",
        description=message,
        color=discord.Color.blue() if success else discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.set_footer(
        text=f"Запросил: {interaction.user.display_name}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="info", description="Информация о боте")
async def info(interaction: discord.Interaction):
    # Проверяем статус сессии
    session_status = "✅ Активна" if check_session() else "❌ Истекла"
    
    embed = discord.Embed(
        title="🤖 Информация о боте (V1.5)",
        color=discord.Color.purple(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="📝 Команды",
        value="`/run` - Запустить сервер\n"
              "`/stop` - Остановить сервер\n"
              "`/restart` - Перезапустить сервер\n"
              "`/update_cookies` - Обновить куки (JSON)\n"
              "`/info` - Информация о боте",
        inline=False
    )
    
    embed.add_field(
        name="🔐 Статус сессии",
        value=session_status,
        inline=False
    )
    
    embed.add_field(
        name="🍪 Куки",
        value=f"Количество: {len(COOKIES)}\n"
              f"`pterodactyl_session`: {COOKIES.get('pterodactyl_session', 'Нет')[:20]}...",
        inline=False
    )
    
    embed.add_field(
        name="📊 Статистика",
        value=f"👥 Серверов: {len(bot.guilds)}\n"
              f"⏰ Задержка: {round(bot.latency * 1000)}ms",
        inline=False
    )
    
    embed.set_footer(
        text=f"Запросил: {interaction.user.display_name}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )
    
    await interaction.response.send_message(embed=embed)

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    print("🚀 Запуск бота...")
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
