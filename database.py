import json
import os
from datetime import datetime

DB_FILE = 'data.json'

def init_db():
    """Создает файл БД если его нет"""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

def load_db():
    """Загружает данные из БД"""
    init_db()
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_db(data):
    """Сохраняет данные в БД"""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    """Получает данные пользователя"""
    db = load_db()
    user_id = str(user_id)
    if user_id not in db:
        db[user_id] = {
            'balance': 0,
            'history': [],
            'total_paid': 0
        }
        save_db(db)
    return db[user_id]

def update_balance(user_id, amount, order_id=None):
    """Обновляет баланс пользователя"""
    db = load_db()
    user_id = str(user_id)

    if user_id not in db:
        db[user_id] = {'balance': 0, 'history': [], 'total_paid': 0}

    db[user_id]['balance'] += amount
    db[user_id]['total_paid'] += amount

    db[user_id]['history'].append({
        'amount': amount,
        'date': datetime.now().isoformat(),
        'order_id': order_id,
        'type': 'payment'
    })

    save_db(db)
    return db[user_id]['balance']

def get_history(user_id, limit=10):
    """Получает историю транзакций"""
    user = get_user(user_id)
    return user['history'][-limit:][::-1]

def reset_balance(user_id):
    """Сброс баланса (для администратора)"""
    db = load_db()
    user_id = str(user_id)
    if user_id in db:
        db[user_id]['balance'] = 0
        save_db(db)
        return True
    return False