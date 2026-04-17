import streamlit as st
import sqlite3
import pandas as pd

# 1. Настраиваем заголовок нашего сайта
st.set_page_config(page_title="PR AI Tracker", page_icon="📊")
st.title("📊 Дашборд PR-отдела")
st.write("Здесь хранятся все отчеты, собранные нашим Telegram-ботом.")

# 2. Подключаемся к нашей базе данных
conn = sqlite3.connect('pr_database.db')

# 3. Выгружаем данные с помощью pandas
# SQL-запрос "SELECT * FROM reports" означает "вытащи ВСЁ из таблицы reports"
try:
    df = pd.read_sql_query("SELECT * FROM reports", conn)
    
    # 4. Выводим таблицу на экран
    if df.empty:
        st.warning("База данных пока пуста. Напиши боту название бренда, чтобы появились данные!")
    else:
        st.dataframe(df, width='stretch')

except Exception as e:
    st.error(f"Ошибка при чтении базы данных: Убедитесь, что бот уже создал файл pr_database.db")