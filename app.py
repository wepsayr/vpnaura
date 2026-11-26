import os
import threading
import requests
import uuid
import logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- НАСТРОЙКИ (берутся из Environment на Render) ---
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
XUI_API_TOKEN = os.environ.get("XUI_API_TOKEN")
SERVER_IP = os.environ.get("SERVER_IP", "144.31.56.178")

XUI_URL = os.environ.get("XUI_URL", "https://144.31.56.178:55443/panel-80a0df3e/")
INBOUND_ID = int(os.environ.get("INBOUND_ID", "1"))

# Данные из твоей рабочей ссылки (Reality)
PORT = os.environ.get("PORT_REALITY", "443")
PBK = os.environ.get("PBK", "tHcgXkmm2TS9d2XwuDgEIy6sFC4oeVJFqxaAa9q_2WI")
SNI = os.environ.get("SNI", "auravpn.localhost.cc")
SID = os.environ.get("SID", "6eae7daf5dc071ac")
SPX = os.environ.get("SPX", "%2Fed20a331e6890e1")

# Telegram ID админа (тебя) — чтобы получать уведомления о «продажах»
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)
app = Flask(__name__)


# ---------- Работа с панелью 3x-ui ----------
def create_vpn_client(user_id):
    """Создаёт клиента в 3x-ui и возвращает готовую vless:// ссылку."""
    if not XUI_API_TOKEN:
        log.error("XUI_API_TOKEN не задан")
        return None

    client_uuid = str(uuid.uuid4())
    email = f"tg_{user_id}"

    url = f"{XUI_URL}panel/api/inbounds/addClient"
    headers = {
        "Authorization": f"Bearer {XUI_API_TOKEN}",
        "Content-Type": "application/json",
    }

    settings_dict = {
        "clients": [{
            "id": client_uuid,
            "flow": "xtls-rprx-vision",
            "email": email,
            "limitIp": 1,
            "totalGB": 0,
            "expiryTime": 0,
            "enable": True,
        }]
    }

    payload = {
        "id": INBOUND_ID,
        "settings": str(settings_dict).replace("'", '"'),
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        data = r.json()
        if r.status_code == 200 and data.get("success"):
            link = (
                f"vless://{client_uuid}@{SERVER_IP}:{PORT}/?"
                f"type=tcp&encryption=none&security=reality"
                f"&pbk={PBK}&fp=firefox&sni={SNI}&sid={SID}&spx={SPX}"
                f"&flow=xtls-rprx-vision#AuraVPN-{user_id}"
            )
            log.info(f"Создан клиент {email}, UUID {client_uuid}")
            return link
        else:
            log.error(f"3x-ui ответил: {r.status_code} — {r.text[:300]}")
            return None
    except Exception as e:
        log.error(f"Ошибка запроса к 3x-ui: {e}")
        return None


# ---------- Обработчики бота ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("💳 Купить 1 месяц (150₽)", callback_data="buy_1m")
    ]]
    await update.message.reply_text(
        "Привет! 🌿 Это бот быстрого и безопасного VPN *AuraVPN*.\n\n"
        "Нажми кнопку ниже, чтобы получить доступ.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy_1m":
        user_id = query.from_user.id
        username = query.from_user.username or f"id{user_id}"

        await query.edit_message_text("⏳ Генерирую твой ключ, подожди пару секунд...")

        link = create_vpn_client(user_id)

        if link:
            await query.message.reply_text(
                "✅ Твой доступ готов!\n\n"
                "📱 *Как подключиться:*\n"
                "1. Скачай приложение *Happ* (App Store / Google Play)\n"
                "2. Скопируй ссылку ниже\n"
                "3. В Happ нажми `+` → «Добавить из буфера обмена»\n"
                "4. Подключись\n\n"
                f"`{link}`\n\n"
                "👆 Нажми на ссылку, чтобы скопировать.",
                parse_mode="Markdown",
            )

            # Уведомление админу
            if ADMIN_ID:
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"💰 Новый клиент: @{username} (id: `{user_id}`)",
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    log.warning(f"Не смог уведомить админа: {e}")
        else:
            await query.message.reply_text(
                "❌ Произошла ошибка при создании ключа. Пожалуйста, напиши в поддержку."
            )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌿 *AuraVPN*\n\n"
        "Это личный VPN для быстрого и безопасного интернета.\n\n"
        "• /start — вернуться в меню\n"
        "• /help — эта справка\n\n"
        "По вопросам: напиши мне @твой_телеграм",
        parse_mode="Markdown",
    )


def run_bot():
    if not BOT_TOKEN:
        log.error("TELEGRAM_TOKEN не задан, бот не запустится")
        return
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CallbackQueryHandler(button_handler))
    log.info("Бот запущен (polling)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


# ---------- Flask для Render ----------
@app.route("/")
def index():
    return "AuraVPN Bot is running 🤖"


@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
