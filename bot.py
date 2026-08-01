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
import subprocess
import sys
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

# ========== ФУНКЦИЯ ЗАПУСКА СКРИПТА ==========

def run_start_script():
    """Запускает run.py как отдельный процесс для запуска сервера"""
    
    try:
        # Получаем путь к текущему скрипту
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, 'run.py')
        
        # Проверяем, существует ли файл
        if not os.path.exists(script_path):
            return False, "❌ Файл run.py не найден!"
        
        # Запускаем run.py как отдельный процесс
        # Используем тот же интерпретатор Python
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, f"✅ Скрипт выполнен успешно!\n```\n{result.stdout[:500]}\n```"
        else:
            return False, f"❌ Ошибка выполнения:\n```\n{result.stderr[:500]}\n```"
            
    except subprocess.TimeoutExpired:
        return False, "⏰ Скрипт выполнялся слишком долго (таймаут 30 сек)"
    except Exception as e:
        return False, f"❌ Ошибка: {str(e)}"

# ==================== КОМАНДЫ БОТА ====================

@bot.event
async def on_ready():
    print(f'✅ Бот запущен!')
    print(f'📌 Имя: {bot.user.name}')
    print(f'🆔 ID: {bot.user.id}')
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

@bot.tree.command(name="run", description="Запустить сервер (выполнить run.py)")
async def run(interaction: discord.Interaction):
    """Запускает run.py для старта сервера"""
    
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="🔄 Запуск скрипта run.py",
        description="Пожалуйста, подождите...",
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    await interaction.followup.send(embed=embed, ephemeral=True)
    
    # Запускаем скрипт
    success, message = run_start_script()
    
    embed = discord.Embed(
        title="✅ Запуск выполнен" if success else "❌ Ошибка",
        description=message,
        color=discord.Color.green() if success else discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.set_footer(
        text=f"Запросил: {interaction.user.display_name}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )
    
    await interaction.edit_original_response(embed=embed)

@bot.tree.command(name="stop", description="Остановить сервер")
async def stop(interaction: discord.Interaction):
    """Останавливает сервер через WebSocket"""
    
    await interaction.response.defer(ephemeral=True)
    
    # Тут ваш код остановки через WebSocket
    success, message = True, "✅ Команда остановки отправлена!"
    
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

@bot.tree.command(name="info", description="Информация о боте")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Информация о боте",
        color=discord.Color.purple(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="📝 Команды",
        value="`/run` - Запустить сервер (выполняет run.py)\n"
              "`/stop` - Остановить сервер\n"
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
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Ошибка: {e}")