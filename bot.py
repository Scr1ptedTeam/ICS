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
import threading
import socket
from datetime import datetime
from bs4 import BeautifulSoup

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== ТОКЕН ==========
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

if not DISCORD_TOKEN:
    print("❌ ТОКЕН НЕ НАЙДЕН!")
    exit(1)

# ========== ТЕСТ СЕТИ ==========
def test_network():
    print("\n" + "="*50)
    print("🌐 ТЕСТ СЕТИ")
    print("="*50)
    
    try:
        ip = socket.gethostbyname('panel.incloudgame.ru')
        print(f"✅ DNS: panel.incloudgame.ru -> {ip}")
    except Exception as e:
        print(f"❌ DNS ошибка: {e}")
    
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

test_network()

# ========== НАСТРОЙКА БОТА ==========
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

# ========== ЛОГ ==========
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ========== EULA ==========

def accept_eula():
    try:
        log("📝 Принимаем EULA...")
        
        session = requests.Session()
        session.cookies.update(COOKIES)
        
        response = session.get('https://panel.incloudgame.ru', headers=HEADERS, timeout=30, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = None
        
        meta = soup.find('meta', {'name': 'csrf-token'})
        if meta and meta.get('content'):
            csrf_token = meta.get('content')
        
        if not csrf_token:
            csrf_token = session.cookies.get('XSRF-TOKEN')
        
        if not csrf_token:
            log("   ❌ Нет CSRF-токена")
            return False
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://panel.incloudgame.ru',
            'X-CSRF-TOKEN': csrf_token,
            'Referer': f'https://panel.incloudgame.ru/server/{SERVER_ID}/files',
        }
        
        response = session.post(
            f'https://panel.incloudgame.ru/api/client/servers/{SERVER_ID}/files/write',
            params={"file": "eula.txt"},
            data="eula=true",
            headers=headers,
            timeout=30,
            verify=False
        )
        
        if response.status_code in [200, 201, 204]:
            log("   ✅ EULA принята")
            return True
        else:
            log(f"   ❌ EULA ошибка: {response.status_code}")
            return False
    except Exception as e:
        log(f"   ❌ EULA ошибка: {e}")
        return False

def get_websocket_token():
    log("🔄 Получение WebSocket токена...")
    
    session = requests.Session()
    session.cookies.update(COOKIES)
    
    headers = HEADERS.copy()
    headers['X-CSRF-TOKEN'] = COOKIES.get('XSRF-TOKEN', '')
    
    try:
        response = session.get(
            f'https://panel.incloudgame.ru/api/client/servers/{SERVER_ID}/websocket',
            headers=headers,
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('data', {}).get('token')
            socket_url = data.get('data', {}).get('socket')
            log(f"   ✅ Токен получен")
            return token, socket_url, session.cookies
        else:
            log(f"   ❌ Ошибка: {response.status_code}")
            return None, None, None
    except Exception as e:
        log(f"   ❌ Ошибка: {e}")
        return None, None, None

def send_server_command(command):
    log(f"🚀 Команда: {command}")
    
    try:
        if command == "start":
            accept_eula()
            time.sleep(2)
        
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
        
        log("🔗 Подключение к WebSocket...")
        
        ws = websocket.create_connection(
            ws_url,
            header=headers,
            timeout=120,
            sslopt={"cert_reqs": 0},
            origin="https://panel.incloudgame.ru"
        )
        log("   ✅ WebSocket подключен!")
        
        log("🔑 Аутентификация...")
        ws.send(json.dumps({"event": "auth", "args": [ws_token]}))
        time.sleep(3)
        
        try:
            response = ws.recv()
            log(f"   📥 Ответ: {response}")
            if "auth success" not in response:
                ws.close()
                return False, "❌ Ошибка аутентификации"
            log("   ✅ Аутентификация успешна!")
        except Exception as e:
            ws.close()
            log(f"   ❌ Ошибка: {e}")
            return False, f"❌ Ошибка: {str(e)}"
        
        log(f"📤 Отправка команды: {command}")
        ws.send(json.dumps({
            "event": "set state",
            "args": [command]
        }))
        
        time.sleep(3)
        ws.close()
        log("✅ Соединение закрыто")
        
        return True, f"✅ Команда '{command}' отправлена!"
        
    except websocket.WebSocketTimeoutException:
        log("❌ ТАЙМАУТ WebSocket!")
        return False, "❌ Таймаут подключения (120 сек). Попробуйте ещё раз."
    except Exception as e:
        log(f"❌ Ошибка: {e}")
        return False, f"❌ Ошибка: {str(e)}"

# ==================== КОМАНДЫ БОТА ====================

@bot.event
async def on_ready():
    log("="*50)
    log("✅ БОТ ЗАПУЩЕН!")
    log(f"📌 Имя: {bot.user.name}")
    log(f"🆔 ID: {bot.user.id}")
    log(f"👥 На серверах: {len(bot.guilds)}")
    log("="*50)
    
    # ========== ПРИНУДИТЕЛЬНАЯ СИНХРОНИЗАЦИЯ КОМАНД ==========
    try:
        synced = await bot.tree.sync()
        log(f"✅ Синхронизировано {len(synced)} команд:")
        for cmd in synced:
            log(f"   /{cmd.name}")
    except Exception as e:
        log(f"❌ Ошибка синхронизации: {e}")
    
    # ========== СТАТУС ==========
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="/run | /stop"
        )
    )

def run_sync(command):
    return send_server_command(command)

@bot.tree.command(name="run", description="Запустить сервер")
async def run(interaction: discord.Interaction):
    log(f"📩 /run от {interaction.user.name}")
    
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="🔄 Запуск сервера",
        description="Пожалуйста, подождите... (до 120 сек)",
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)
    
    loop = asyncio.get_event_loop()
    success, message = await loop.run_in_executor(None, run_sync, "start")
    
    embed = discord.Embed(
        title="🟢 Запуск сервера" if success else "⚠️ Ошибка",
        description=message,
        color=discord.Color.green() if success else discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.set_footer(text=f"Запросил: {interaction.user.display_name}")
    
    await interaction.edit_original_response(embed=embed)
    log(f"✅ /run завершена для {interaction.user.name}")

@bot.tree.command(name="stop", description="Остановить сервер")
async def stop(interaction: discord.Interaction):
    log(f"📩 /stop от {interaction.user.name}")
    
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="🔄 Остановка сервера",
        description="Пожалуйста, подождите...",
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)
    
    loop = asyncio.get_event_loop()
    success, message = await loop.run_in_executor(None, run_sync, "stop")
    
    embed = discord.Embed(
        title="🔴 Остановка сервера" if success else "⚠️ Ошибка",
        description=message,
        color=discord.Color.red() if success else discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.set_footer(text=f"Запросил: {interaction.user.display_name}")
    
    await interaction.edit_original_response(embed=embed)
    log(f"✅ /stop завершена для {interaction.user.name}")

@bot.tree.command(name="restart", description="Перезапустить сервер")
async def restart(interaction: discord.Interaction):
    log(f"📩 /restart от {interaction.user.name}")
    
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="🔄 Перезапуск сервера",
        description="Пожалуйста, подождите...",
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)
    
    loop = asyncio.get_event_loop()
    success, message = await loop.run_in_executor(None, run_sync, "restart")
    
    embed = discord.Embed(
        title="🔄 Перезапуск сервера" if success else "⚠️ Ошибка",
        description=message,
        color=discord.Color.blue() if success else discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.set_footer(text=f"Запросил: {interaction.user.display_name}")
    
    await interaction.edit_original_response(embed=embed)
    log(f"✅ /restart завершена для {interaction.user.name}")

@bot.tree.command(name="info", description="Информация о боте")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Информация о боте",
        color=discord.Color.purple(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="📝 Команды",
        value="`/run` - Запустить сервер\n"
              "`/stop` - Остановить сервер\n"
              "`/restart` - Перезапустить сервер\n"
              "`/info` - Информация о боте",
        inline=False
    )
    
    embed.add_field(
        name="📊 Статистика",
        value=f"👥 Серверов: {len(bot.guilds)}\n"
              f"⏰ Задержка: {round(bot.latency * 1000)}ms",
        inline=False
    )
    
    embed.set_footer(text=f"Запросил: {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    log("🚀 ЗАПУСК БОТА")
    log("="*50)
    
    # Проверяем токен
    if not DISCORD_TOKEN:
        log("❌ НЕТ ТОКЕНА!")
        exit(1)
    
    log(f"📌 Токен: {DISCORD_TOKEN[:20]}...")
    log(f"📌 SERVER_ID: {SERVER_ID}")
    log("="*50)
    
    try:
        bot.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        log("❌ НЕВЕРНЫЙ ТОКЕН!")
    except Exception as e:
        log(f"❌ Ошибка: {e}")