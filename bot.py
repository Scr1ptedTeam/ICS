import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import requests
import urllib3
import websocket
import time
from datetime import datetime

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

# ========== КУКИ ИЗ FIDDLER ==========
COOKIES = {
    '__ddg1_': '9XPjSXZG9a6WDFAprBid',
    '_ym_uid': '1783955517502440301',
    '__ddg8_': 'i7Qar9csNELvyxyQ',
    '__ddg9_': '104.28.165.101',
    '__ddg10_': '1785587520',
    'XSRF-TOKEN': 'eyJpdiI6IlJUcEZ2bDNpdnh1NzJkamllM2NObEE9PSIsInZhbHVlIjoiQ3BMZVdxazE0REsxZ2kvdEFIamhNQzkzK3I1b3o2S29PV1JBemQxTWIyK1c5ZktuZFEvbU54c0x5N2JtS0ZFT2NPWnFkZzFGd1ZMc21VdWQyN3Qzb3ZTeEhNd2dNN0ZjcVRyWXVsZ2ZGRlVsRktRMkhrNkdTT1B2KzZvdmdMNlQiLCJtYWMiOiIwMDNhYThjYTc2MjExNDNlN2ExZmQzZmIxZDI2MWY0ZDZhZmJhM2JiYWIzZDkzYzhhOTU4MzdjZmVlZmFhNmNhIiwidGFnIjoiIn0%3D',
    'pterodactyl_session': 'eyJpdiI6Ik9sQWU1RUhBNmlPVTBqSnNqNUpwYUE9PSIsInZhbHVlIjoiblNqdFdUdHJEakNpbnlGVEExZ2hTN0NLWjFaK0srWWRSaEcxcHFlVFM1Q1FlRG9uZEwrL00vdWhmV1VPMnkzOE9tYWMyQ0lUc1N3dEw3emY3eVFFMU5ERlBnZlVoaWhUeTZaT0VQVkFnZDNER1dDMWc5T1diRFVodnNJc2wvVE4iLCJtYWMiOiIyN2Q4NWZiOTUwYTVjNzYyZjQ1OTNlOTcxOTFiZDczNWM0MTJlMDhjZmZhMmNiYWQyMjAwMTY1YWRlMGJmOWRkIiwidGFnIjoiIn0%3D',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'Content-Type': 'application/json',
    'Origin': 'https://incloudgame.ru',
    'Connection': 'keep-alive',
    'Referer': 'https://incloudgame.ru/',
}

# ========== ID СЕРВЕРА ==========
SERVER_ID = "6952da89-092d-410b-be22-d2e4efd713f0"

def get_websocket_token():
    """Получает свежий WebSocket токен"""
    
    session = requests.Session()
    session.cookies.update(COOKIES)
    
    headers = HEADERS.copy()
    headers['X-CSRF-TOKEN'] = COOKIES.get('XSRF-TOKEN')
    
    url = f"https://panel.incloudgame.ru/api/client/servers/{SERVER_ID}/websocket"
    
    try:
        response = session.get(url, headers=headers, timeout=10, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {}).get('token'), data.get('data', {}).get('socket')
        else:
            return None, None
    except Exception as e:
        print(f"❌ Ошибка получения токена: {e}")
        return None, None

def start_server_via_websocket():
    """Запускает сервер через WebSocket"""
    
    try:
        # Получаем свежий токен
        ws_token, ws_url = get_websocket_token()
        
        if not ws_token:
            return False, "❌ Не удалось получить WebSocket токен"
        
        print(f"✅ Токен получен: {ws_token[:30]}...")
        print(f"🔗 WebSocket URL: {ws_url}")
        
        # Заголовки для WebSocket
        headers = [
            "Pragma: no-cache",
            "Cache-Control: no-cache",
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0",
            "Origin: https://panel.incloudgame.ru",
            "Accept-Language: ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            f"Authorization: Bearer {ws_token}",
        ]
        
        print("🔄 Подключение к WebSocket...")
        
        # Создаем WebSocket соединение
        ws = websocket.create_connection(
            ws_url,
            header=headers,
            timeout=15,
            sslopt={"cert_reqs": 0}
        )
        
        print("✅ WebSocket подключен!")
        
        # Пробуем разные форматы сообщений для запуска
        messages = [
            # Формат 1: Pterodactyl стандарт
            json.dumps({"event": "send", "args": ["start"]}),
            
            # Формат 2: просто команда
            json.dumps({"command": "start"}),
            
            # Формат 3: сигнал
            json.dumps({"signal": "start"}),
            
            # Формат 4: действие
            json.dumps({"action": "power", "data": {"signal": "start"}}),
            
            # Формат 5: событие
            json.dumps({"event": "power:start"}),
        ]
        
        for msg in messages:
            try:
                print(f"📤 Отправка: {msg}")
                ws.send(msg)
                time.sleep(1)
                
                # Получаем ответ
                response = ws.recv()
                print(f"📥 Ответ: {response}")
                
                # Проверяем ответ
                response_lower = response.lower()
                if "success" in response_lower or "started" in response_lower or "running" in response_lower:
                    ws.close()
                    return True, "✅ Сервер запущен!"
                    
                # Если в ответе ошибка - пробуем дальше
                if "error" in response_lower:
                    continue
                    
            except Exception as e:
                print(f"⚠️ Ошибка с сообщением: {e}")
                continue
        
        ws.close()
        return False, "❌ Сервер не запустился. Проверьте логи."
        
    except Exception as e:
        return False, f"❌ Ошибка: {str(e)}"

# ==================== КОМАНДЫ БОТА ====================

@bot.tree.command(name="run", description="Запустить сервер")
async def run(interaction: discord.Interaction):
    """Запускает сервер"""
    
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="🔄 Запуск сервера",
        description="Пожалуйста, подождите...",
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    
    await interaction.followup.send(embed=embed, ephemeral=True)
    
    # Запускаем сервер
    success, message = start_server_via_websocket()
    
    embed = discord.Embed(
        title="🖥️ Запуск сервера",
        description=message,
        color=discord.Color.green() if success else discord.Color.red(),
        timestamp=datetime.now()
    )
    
    embed.set_footer(
        text=f"Запросил: {interaction.user.display_name}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )
    
    await interaction.edit_original_response(embed=embed)

@bot.tree.command(name="info", description="Информация о боте")
async def info(interaction: discord.Interaction):
    """Показывает информацию о боте"""
    
    embed = discord.Embed(
        title="🤖 Информация о боте",
        color=discord.Color.purple(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="📝 Команды",
        value="`/pay` - Пополнить баланс\n"
              "`/run` - Запустить сервер\n"
              "`/info` - Информация о боте",
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
    print(f"📁 Директория: {os.getcwd()}")
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
