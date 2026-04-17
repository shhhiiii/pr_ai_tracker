import telebot
import google.generativeai as genai
import feedparser
import sqlite3 # 🆕 Библиотека для работы с базой данных
from datetime import datetime # 🆕 Библиотека для работы со временем
import schedule
import time
import threading

BOT_TOKEN = "8612566639:AAFhgGd3YZlttahYmkI6STuk955g9vF4fZI"
GEMINI_KEY = "AQ.Ab8RN6ITQXqyTQf7ZqDBr3ktX0CkZ-WKyp6UNi-6Hj7GXVHy_w"

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_KEY)
ai_model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# 🆕 НАСТРОЙКА БАЗЫ ДАННЫХ (НАША "EXCEL ТАБЛИЦА")
# ==========================================
# Создаем файл базы данных (он появится в папке с проектом)
conn = sqlite3.connect('pr_database.db', check_same_thread=False)
cursor = conn.cursor()

# Создаем колонки в нашей таблице, если их еще нет: Дата | Бренд | Отчет
cursor.execute('''CREATE TABLE IF NOT EXISTS reports
                  (date TEXT, brand TEXT, report TEXT)''')
conn.commit()
# ==========================================

def get_real_news(brand_name):
    url = f"https://news.google.com/rss/search?q={brand_name}&hl=ru&gl=RU&ceid=RU:ru"
    feed = feedparser.parse(url)
    news_list = []
    for entry in feed.entries[:5]:
        news_list.append(entry.title)
    return news_list

def analyze_news(news_list, brand_name):
    news_text = "\n".join(news_list)
    prompt = f"""
    Ты Senior PR-аналитик. Вот 5 последних новостей о бренде '{brand_name}':
    {news_text}
    
    Сделай краткую сводку:
    1. 📊 Общая тональность (позитив/негатив/нейтрально).
    2. ⚠️ PR-риски.
    3. 💡 Идея для соцсетей.
    """
    response = ai_model.generate_content(prompt)
    return response.text

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я AI-трекер. Напиши бренд, и я его проанализирую.")
@bot.message_handler(commands=['myid'])
def show_id(message):
    bot.reply_to(message, f"Твой Chat ID: {message.chat.id}")
    
@bot.message_handler(func=lambda message: True)
def track_brand(message):
    brand = message.text
    bot.reply_to(message, f"🔍 Собираю данные по запросу '{brand}'...")
    
    try:
        news = get_real_news(brand)
        if not news:
            bot.reply_to(message, f"Нет новостей по '{brand}'.")
            return
            
        bot.send_message(message.chat.id, "🧠 Анализирую...")
        ai_response = analyze_news(news, brand)
        
        # 🆕 СОХРАНЯЕМ ДАННЫЕ В БАЗУ ПЕРЕД ОТПРАВКОЙ
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO reports VALUES (?, ?, ?)", (current_time, brand, ai_response))
        conn.commit() # "Нажимаем кнопку Сохранить"
        
        # Отправляем пользователю (без Markdown, чтобы не было ошибки 400)
        bot.send_message(message.chat.id, f"📰 PR-Отчет: {brand}\n\n{ai_response}")
        
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

print("🤖 Бот с памятью запущен!")

def morning_pr_report():
    my_chat_id = "701001082" # <-- Твои цифры сюда (без кавычек)
    brands = ["Tesla", "Apple"] # Бренды конкурентов
    
    bot.send_message(my_chat_id, "🌅 Доброе утро! Собираю утреннюю PR-сводку...")
    
    for brand in brands:
        news = get_real_news(brand)
        if news:
            report = analyze_news(news, brand)
            bot.send_message(my_chat_id, f"📌 АВТО-ОТЧЕТ: {brand}\n\n{report}")

# 🆕 НАСТРОЙКА БУДИЛЬНИКА
# ВНИМАНИЕ: Для тестов мы настроим его срабатывать каждую 1 минуту!
# Ждать до 09:00 утра на этапе разработки — плохая идея.
schedule.every().day.at("09:00").do(morning_pr_report)

# 🆕 ЗАПУСК ПАРАЛЛЕЛЬНОГО ПРОЦЕССА
# Бот должен одновременно и отвечать на сообщения людей, и следить за часами.
# Поэтому мы запускаем "будильник" в отдельном потоке (фоновом режиме).
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=run_scheduler, daemon=True).start()

bot.infinity_polling()