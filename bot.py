import discord
from discord import app_commands
from discord.ext import commands
import os
import sys
from datetime import datetime
import asyncio

from config import DISCORD_TOKEN, COOKIES, LOG_CHANNEL_ID
from payment import create_payment
from database import get_user, update_balance, get_history, init_db, reset_balance
from keep_alive import keep_alive

# Инициализация БД
init_db()

# Настройка бота
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Время запуска для uptime
start_time = datetime.now()

# ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================

@bot.event
async def on_ready():
    print(f'✅ Бот запущен!')
    print(f'📌 Имя: {bot.user.name}')
    print(f'🆔 ID: {bot.user.id}')
    print(f'👥 На серверах: {len(bot.guilds)}')
    print(f'⏰ Время: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    # Синхронизация слэш-команд
    try:
        synced = await bot.tree.sync()
        print(f'✅ Синхронизировано {len(synced)} слэш-команд')
    except Exception as e:
        print(f'❌ Ошибка синхронизации: {e}')

    # Устанавливаем статус
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"/pay | {len(bot.guilds)} серверов"
        )
    )

@bot.event
async def on_guild_join(guild):
    """При добавлении на сервер"""
    print(f'✅ Бот добавлен на сервер: {guild.name} ({guild.id})')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"/pay | {len(bot.guilds)} серверов"
        )
    )

@bot.event
async def on_command_error(ctx, error):
    """Обработка ошибок команд"""
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(f'❌ Ошибка: {str(error)}')

# ==================== КОМАНДЫ СЛЭШ ====================

@bot.tree.command(name="pay", description="Пополнить баланс")
@app_commands.describe(amount="Сумма пополнения в рублях")
async def pay(interaction: discord.Interaction, amount: int):
    """Команда для пополнения баланса"""

    # Проверка суммы
    if amount <= 0:
        await interaction.response.send_message(
            "❌ Сумма должна быть больше 0!",
            ephemeral=True
        )
        return

    if amount > 100000:
        await interaction.response.send_message(
            "❌ Максимальная сумма: 100 000 ₽",
            ephemeral=True
        )
        return

    # Отправляем "печатает..."
    await interaction.response.defer(ephemeral=True)

    try:
        # Создаем платеж
        payment_url, error = create_payment(amount)

        if error:
            await interaction.followup.send(
                f"❌ Ошибка: {error}\n"
                f"Попробуйте позже или обратитесь к администратору.",
                ephemeral=True
            )
            return

        # Формируем красивое сообщение
        embed = discord.Embed(
            title="💳 Пополнение баланса",
            description=f"На сумму **{amount} ₽**",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )

        embed.add_field(
            name="🔗 Ссылка для оплаты",
            value=f"[Оплатить через ЮMoney]({payment_url})",
            inline=False
        )

        embed.add_field(
            name="📌 Инструкция",
            value="1️⃣ Перейдите по ссылке\n"
                  "2️⃣ Оплатите через ЮMoney\n"
                  "3️⃣ После оплаты баланс пополнится автоматически",
            inline=False
        )

        embed.add_field(
            name="⚠️ Важно",
            value="Ссылка действительна **24 часа**\n"
                  "Если оплата не прошла - обратитесь в поддержку",
            inline=False
        )

        embed.set_footer(
            text=f"Запрос от {interaction.user.display_name}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )

        # Лог в канал (если настроен)
        if LOG_CHANNEL_ID:
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(
                    f"💰 **{interaction.user.display_name}** (`{interaction.user.id}`) "
                    f"запросил пополнение на **{amount} ₽**\n"
                    f"🔗 {payment_url}"
                )

    except Exception as e:
        await interaction.followup.send(
            f"❌ Произошла ошибка: {str(e)}\n"
            f"Пожалуйста, сообщите администратору.",
            ephemeral=True
        )

@bot.tree.command(name="balance", description="Проверить баланс")
async def balance(interaction: discord.Interaction):
    """Показывает текущий баланс"""

    await interaction.response.defer(ephemeral=True)

    user_data = get_user(interaction.user.id)
    balance = user_data['balance']
    total_paid = user_data['total_paid']

    embed = discord.Embed(
        title="💰 Ваш баланс",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )

    embed.add_field(
        name="Текущий баланс",
        value=f"**{balance} ₽**",
        inline=False
    )

    embed.add_field(
        name="Всего пополнено",
        value=f"{total_paid} ₽",
        inline=True
    )

    embed.add_field(
        name="Количество пополнений",
        value=f"{len(user_data['history'])}",
        inline=True
    )

    embed.set_footer(
        text=interaction.user.display_name,
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )

    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="history", description="История пополнений")
@app_commands.describe(limit="Количество записей (по умолчанию 5)")
async def history(interaction: discord.Interaction, limit: int = 5):
    """Показывает историю пополнений"""

    if limit < 1 or limit > 20:
        await interaction.response.send_message(
            "❌ Укажите число от 1 до 20",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    history_data = get_history(interaction.user.id, limit)

    if not history_data:
        embed = discord.Embed(
            title="📋 История пополнений",
            description="У вас пока нет пополнений",
            color=discord.Color.grey(),
            timestamp=datetime.now()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    embed = discord.Embed(
        title="📋 История пополнений",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )

    description = ""
    total = 0
    for item in history_data:
        date = datetime.fromisoformat(item['date']).strftime("%d.%m.%Y %H:%M")
        amount = item['amount']
        total += amount
        description += f"`{date}` **+{amount} ₽**\n"

    embed.description = description
    embed.add_field(
        name="📊 Итого за период",
        value=f"{total} ₽",
        inline=False
    )

    embed.set_footer(
        text=f"Показано {len(history_data)} записей",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )

    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="info", description="Информация о боте")
async def info(interaction: discord.Interaction):
    """Информация о боте"""

    embed = discord.Embed(
        title="🤖 Информация о боте",
        description="Бот для пополнения баланса через ЮMoney",
        color=discord.Color.purple(),
        timestamp=datetime.now()
    )

    embed.add_field(
        name="📝 Доступные команды",
        value="`/pay` - Пополнить баланс\n"
              "`/balance` - Проверить баланс\n"
              "`/history` - История пополнений\n"
              "`/info` - Информация о боте",
        inline=False
    )

    embed.add_field(
        name="🔗 Сайт",
        value="[incloudgame.ru](https://incloudgame.ru)",
        inline=True
    )

    embed.add_field(
        name="💳 Платежная система",
        value="ЮMoney (YooKassa)",
        inline=True
    )

    embed.add_field(
        name="👥 Серверов",
        value=str(len(bot.guilds)),
        inline=True
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="uptime", description="Время работы бота")
async def uptime(interaction: discord.Interaction):
    """Показывает время работы бота"""

    uptime_seconds = int((datetime.now() - start_time).total_seconds())
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60

    await interaction.response.send_message(
        f"🕐 Бот работает: **{days}д {hours}ч {minutes}м {seconds}с**",
        ephemeral=True
    )

# ==================== КОМАНДЫ ДЛЯ АДМИНИСТРАТОРА ====================

@bot.tree.command(name="admin_reset", description="Сброс баланса пользователя (Админ)")
@app_commands.describe(user="Пользователь", amount="Сумма для сброса")
@app_commands.default_permissions(administrator=True)
async def admin_reset(interaction: discord.Interaction, user: discord.User, amount: int = 0):
    """Сброс или установка баланса (только для администраторов)"""

    if amount < 0:
        await interaction.response.send_message(
            "❌ Сумма не может быть отрицательной",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    old_balance = get_user(user.id)['balance']
    new_balance = update_balance(user.id, amount - old_balance)

    embed = discord.Embed(
        title="👑 Изменение баланса (Админ)",
        color=discord.Color.red(),
        timestamp=datetime.now()
    )

    embed.add_field(
        name="Пользователь",
        value=f"{user.mention} (`{user.id}`)",
        inline=False
    )

    embed.add_field(
        name="Старый баланс",
        value=f"{old_balance} ₽",
        inline=True
    )

    embed.add_field(
        name="Новый баланс",
        value=f"{new_balance} ₽",
        inline=True
    )

    embed.set_footer(
        text=f"Изменено: {interaction.user.display_name}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )

    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="admin_stats", description="Статистика бота (Админ)")
@app_commands.default_permissions(administrator=True)
async def admin_stats(interaction: discord.Interaction):
    """Статистика бота (только для администраторов)"""

    await interaction.response.defer(ephemeral=True)

    from database import load_db
    db = load_db()

    total_users = len(db)
    total_balance = sum(user['balance'] for user in db.values())
    total_paid = sum(user['total_paid'] for user in db.values())
    total_transactions = sum(len(user['history']) for user in db.values())

    embed = discord.Embed(
        title="📊 Статистика бота",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )

    embed.add_field(
        name="👥 Всего пользователей",
        value=str(total_users),
        inline=True
    )

    embed.add_field(
        name="💰 Общий баланс",
        value=f"{total_balance} ₽",
        inline=True
    )

    embed.add_field(
        name="💳 Всего пополнено",
        value=f"{total_paid} ₽",
        inline=True
    )

    embed.add_field(
        name="📝 Всего транзакций",
        value=str(total_transactions),
        inline=True
    )

    embed.add_field(
        name="🖥️ Серверов",
        value=str(len(bot.guilds)),
        inline=True
    )

    embed.add_field(
        name="⏰ uptime",
        value=f"{(datetime.now() - start_time).seconds // 3600}ч",
        inline=True
    )

    await interaction.followup.send(embed=embed, ephemeral=True)

# ==================== КОМАНДЫ ПРЕФИКС (для тестов) ====================

@bot.command(name='ping')
async def ping(ctx):
    """Проверка работы бота"""
    latency = round(bot.latency * 1000)
    if latency < 100:
        color = discord.Color.green()
        status = "🟢 Отлично"
    elif latency < 300:
        color = discord.Color.yellow()
        status = "🟡 Нормально"
    else:
        color = discord.Color.red()
        status = "🔴 Плохо"

    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Задержка: **{latency}ms**\nСтатус: {status}",
        color=color
    )
    await ctx.send(embed=embed)

@bot.command(name='servers')
async def servers(ctx):
    """Показывает список серверов (только для админа)"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Только для администраторов!")
        return

    guilds = bot.guilds
    embed = discord.Embed(
        title="🖥️ Список серверов",
        description=f"Всего: {len(guilds)}",
        color=discord.Color.blue()
    )

    for guild in guilds[:10]:  # Показываем первые 10
        embed.add_field(
            name=guild.name,
            value=f"ID: `{guild.id}`\n👥 {guild.member_count} участников",
            inline=False
        )

    await ctx.send(embed=embed)

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ Токен не найден! Проверьте .env файл")
        print("📌 Создайте файл .env с содержимым: DISCORD_TOKEN=ваш_токен")
        sys.exit(1)

    print("🚀 Запуск бота...")
    print(f"📁 Директория: {os.getcwd()}")

    # Запускаем Flask сервер для keep-alive
    keep_alive()

    # Запускаем бота
    try:
        bot.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        print("❌ Неверный токен! Проверьте .env файл")
    except Exception as e:
        print(f"❌ Ошибка: {e}")