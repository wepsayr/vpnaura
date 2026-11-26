import os
import threading
import requests
import uuid
import logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "ТВОЙ_ТОКЕН_ОТ_BOTFATHER")
XUI_API_TOKEN = os.environ.get("XUI_API_TOKEN", "9fJfkDIc4zI34ay0yuDqx6HNmXwVkiQ60En6UYovkBaeaDHc")
XUI_URL = "https://94.177.13.36:55443/panel-80a0df3e/" 
INBOUND_ID = 1

# Данные из твоей рабочей ссылки
SERVER_IP = "94.177.13.36"
PORT = "443"
PBK = "tHcgXkmm2TS9d2XwuDgEIy6sFC4oeVJFqxaAa9q_2WI"
SNI = "auravpn.localhost.cc"
SID = "6eae7daf5dc071ac"
SPX = "%2Fed20a331e6890e1"

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# --- API 3X-UI ---
def create_vpn_client(user_id):
    client_uuid = str(uuid.uuid4())
    email = f"tg_{user_id}"
    url = f"{XUI_URL}panel/api/inbounds/addClient"
    headers = {"Authorization": f"Bearer {XUI_API_TOKEN}", "Content-Type": "application/json"}
    settings_json = {
        "clients": [{
            "id": client_uuid, "flow": "xtls-rprx-vision", "email": email,
            "limitIp": 1, "totalGB": 0, "expiryTime": 0, "enable": True
        }]
    }
    payload = {"id": INBOUND_ID, "settings": str(settings_json).replace("'", '"')}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200 and response.json().get("success"):
            link = f"vless://{client_uuid}@{SERVER_IP}:{PORT}/?type=tcp&encryption=none&security=reality&pbk={PBK}&fp=firefox&sni={SNI}&sid={SID}&spx={SPX}&flow=xtls-rprx-vision#AuraVPN-{user_id}"
            return link
        else:
            logging.error(f"Ошибка API: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Ошибка запроса: {e}")
        return None

# --- Telegram Бот ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💳 Купить 1 месяц (150₽)", callback_data="buy_1m")]]
    await update.message.reply_text(
        "Привет! 🌿 Это бот быстрого и безопасного VPN AuraVPN.\n\nНажми кнопку ниже, чтобы получить доступ.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "buy_1m":
        user_id = query.from_user.id
        await query.edit_message_text("⏳ Генерирую твой ключ, подожди пару секунд...")
        link = create_vpn_client(user_id)
        if link:
            await query.message.reply_text(
                "✅ Твой доступ готов!\n\n1. Скачай приложение **Happ** или **v2rayTun**.\n2. Скопируй ссылку ниже и добавь её в приложение.\n\n"
                f"`{link}`\n\nНажми на ссылку, чтобы скопировать.",
                parse_mode="Markdown"
            )
        else:
            await query.message.reply_text("❌ Ошибка при создании ключа. Напиши в поддержку.")

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    logging.info("Бот запущен в фоновом потоке...")
    application.run_polling()

# --- Flask для Render ---
@app.route('/')
def index():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    # Запускаем Flask-сервер (Render требует, чтобы он слушал порт)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
