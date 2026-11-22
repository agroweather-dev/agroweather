import telebot
import requests
import re
from telebot.types import Message

load_dotenv()

# Теперь токен берется из скрытого файла .env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

NODUL_WEBHOOK_URL = "https://webhook.nodul.ru/28657/prod/3a93f2b4-c2f7-47a1-a808-9d9668975aa9"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Хранилище данных и последних сообщений для защиты от дублей
user_data = {}
last_message_text = {}

@bot.message_handler(commands=['start'])
def send_welcome(message: Message):
    chat_id = message.chat.id
    if chat_id in user_data:
        del user_data[chat_id]
    if chat_id in last_message_text:
        del last_message_text[chat_id]
    
    welcome_text = (
        "Привет! Я агрометеорологический агент. 🌾\n\n"
        "Шаг 1. Отправь мне координаты в формате: Широта, Долгота\n"
        "Например: 55.75, 37.62"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['text'])
def handle_messages(message: Message):
    chat_id = message.chat.id
    text = message.text.strip()

    if text.startswith('/'):
        return

    # ЗАЩИТА ОТ ДУБЛЕЙ: Если это сообщение идентично предыдущему, игнорируем его
    if last_message_text.get(chat_id) == text:
        return
    last_message_text[chat_id] = text

    # Инициализация словаря для пользователя, если его нет
    if chat_id not in user_data:
        user_data[chat_id] = {}

    # ШАГ 1: Ждем координаты
    if 'lat' not in user_data[chat_id]:
        try:
            # Ищем два числа в тексте
            numbers = re.findall(r'-?\d+\.?\d*', text)
            
            if len(numbers) != 2:
                raise ValueError
            
            lat = float(numbers[0])
            lon = float(numbers[1])
            
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise ValueError
            
            user_data[chat_id]['lat'] = lat
            user_data[chat_id]['lon'] = lon
            bot.reply_to(message, "📍 Координаты приняты.\n\nШаг 2. Напишите, какая культура вас интересует? (например, Картофель, Пшеница)")
            
        except ValueError:
            bot.reply_to(message, "❌ Ошибка! Отправьте два числа через запятую или пробел.\nПример: 55.75 37.62")
    
    # ШАГ 2: Ждем культуру
    elif 'crop' not in user_data[chat_id]:
        
        # Проверка на цифры и длину
        if any(char.isdigit() for char in text) or len(text) < 3:
            bot.reply_to(message, "❌ Это не похоже на название культуры. Напишите текстом (например: Картофель).")
            return

        user_data[chat_id]['crop'] = text
        bot.reply_to(message, "🌱 Культура принята.\n\nШаг 3. Напишите название вашего агрохозяйства.")

    # ШАГ 3: Ждем название хозяйства и отправляем в Nodul
    elif 'farm_name' not in user_data[chat_id]:
        
        # Проверка на цифры (название не должно состоять только из цифр)
        if text.isdigit() or len(text) < 2:
            bot.reply_to(message, "❌ Название хозяйства слишком короткое или состоит из цифр. Напишите текстом.")
            return

        user_data[chat_id]['farm_name'] = text
        msg = bot.reply_to(message, "⏳ Запрашиваю прогноз и анализирую риски...")
        
        # Формируем запрос к Nodul со ВСЕМИ параметрами
        payload = {
            "latitude": user_data[chat_id]['lat'], 
            "longitude": user_data[chat_id]['lon'],
            "crop": user_data[chat_id]['crop'],
            "farm_name": user_data[chat_id]['farm_name'] # Передаем название!
        }
        
        try:
            response = requests.post(
                NODUL_WEBHOOK_URL, 
                json=payload, 
                timeout=120,
                headers={"Expect": ""}
            )
            response.raise_for_status()
            result = response.json()
            
            bulletin = result.get("bulletin_text", "Текст отчета не найден.")
            alert_level = result.get("alert_level", "NONE")
            alert_msg = result.get("alert_message", "")
            
            # Убираем звездочки Markdown
            bulletin = bulletin.replace("**", "")

            if alert_level == "CRITICAL":
                header = f"🚨 ВНИМАНИЕ! УРОВЕНЬ УГРОЗЫ: КРИТИЧЕСКИЙ\n{alert_msg}\n"
            elif alert_level in ["WARNING", "ALERT"]:
                header = f"⚠️ ПРЕДУПРЕЖДЕНИЕ: {alert_msg}\n"
            else:
                header = "✅ Угроз не выявлено. Условия в норме.\n"

            final_text = (
                f"{header}\n"
                f"🏢 Хозяйство: {user_data[chat_id]['farm_name']}\n"
                f"📍 Координаты: {user_data[chat_id]['lat']}, {user_data[chat_id]['lon']}\n"
                f"🌱 Культура: {result.get('crop', user_data[chat_id]['crop']).capitalize()}\n"
                f"----------------------------------------\n\n"
                f"{bulletin}"
            )

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg.message_id,
                text=final_text
            )
            
        except requests.exceptions.Timeout:
            bot.edit_message_text("⏱️ Nodul не ответил вовремя. Попробуйте позже.", chat_id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ Ошибка: {e}", chat_id, msg.message_id)
        
        # Очищаем данные после завершения
        if chat_id in user_data:
            del user_data[chat_id]

if __name__ == '__main__':
    print("Бот запущен...")
    bot.remove_webhook()
    bot.polling(none_stop=True)