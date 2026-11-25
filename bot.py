import os
import uuid
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- НАСТРОЙКИ (замени на свои) ---
BOT_TOKEN = "ТВОЙ_ТОКЕН_ОТ_BOTFATHER" # <-- ВСТАВЬ ТОКЕН БОТА СЮДА
XUI_API_TOKEN = "9fJfkDIc4zI34ay0yuDqx6HNmXwVkiQ60En6UYovkBaeaDHc" # Твой API токен
XUI_URL = "https://94.177.13.36:55443/panel-80a0df3e/" # URL панели
INBOUND_ID = 1 # ID твоего входящего подключения (обычно 1)

# Данные из твоей рабочей ссылки для сборки конфига
SERVER_IP = "94.177.13.36"
PORT = "443"
PBK = "tHcgXkmm2TS9d2XwuDgEIy6sFC4oeVJFqxaAa9q_2WI"
SNI = "auravpn.localhost.cc"
SID = "6eae7daf5dc071ac"
SPX = "%2Fed20a331e6890e1"

logging.basicConfig(level=logging.INFO)

# --- ФУНКЦИЯ СОЗДАНИЯ КЛИЕНТА В 3X-UI ---
def create_vpn_client(user_id):
    # Генерируем UUID для нового клиента
    client_uuid = str(uuid.uuid4())
    email = f"tg_{user_id}"
    
    # Формируем запрос к API 3x-ui
    url = f"{XUI_URL}panel/api/inbounds/addClient"
    headers = {
        "Authorization": f"Bearer {XUI_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # JSON, который 3x-ui ожидает получить
    settings_json = {
        "clients": [{
            "id": client_uuid,
            "flow": "xtls-rprx-vision",
            "email": email,
            "limitIp": 1,
            "totalGB": 0, # 0 = безлимит
            "expiryTime": 0, # 0 = навсегда (в реальном проекте нужно ставить время)
            "enable": True
        }]
    }
    
    payload = {
        "id": INBOUND_ID,
        "settings": str(settings_json).replace("'", '"') # API требует строку JSON
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200 and response.json().get("success"):
            # Собираем рабочую ссылку
            link = f"vless://{client_uuid}@{SERVER_IP}:{PORT}/?type=tcp&encryption=none&security=reality&pbk={PBK}&fp=firefox&sni={SNI}&sid={SID}&spx={SPX}&flow=xtls-rprx-vision#AuraVPN-{user_id}"
            return link
        else:
            logging.error(f"Ошибка API 3x-ui: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Ошибка при запросе: {e}")
        return None

# --- ОБРАБОТЧИКИ БОТА ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💳 Купить 1 месяц (150₽)", callback_data="buy_1m")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! 🌿 Это бот быстрого и безопасного VPN AuraVPN.\n\n"
        "Нажми кнопку ниже, чтобы получить доступ.",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Убираем "часики" на кнопке
    
    if query.data == "buy_1m":
        user_id = query.from_user.id
        await query.edit_message_text("⏳ Генерирую твой ключ, подожди пару секунд...")
        
        # Здесь в будущем будет проверка оплаты, а сейчас просто выдаем ключ
        link = create_vpn_client(user_id)
        
        if link:
            await query.message.reply_text(
                "✅ Твой доступ готов!\n\n"
                "1. Скачай приложение **Happ** или **v2rayTun**.\n"
                "2. Скопируй ссылку ниже и добавь её в приложение.\n\n"
                f"`{link}`\n\n"
                "Нажми на ссылку, чтобы скопировать.",
                parse_mode="Markdown"
            )
        else:
            await query.message.reply_text(
                "❌ Произошла ошибка при создании ключа. Пожалуйста, напиши в поддержку."
            )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
