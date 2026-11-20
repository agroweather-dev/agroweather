import streamlit as st
import requests
from urllib.parse import quote
from PIL import Image
import os

# Настройка страницы
st.set_page_config(page_title="Бюллетень хозяйства", page_icon="🌾", layout="centered")

# Логотип вверху
if os.path.exists("logo.jpg"):
    logo = Image.open("logo.jpg")
    st.image(logo, width=200)
else:
    st.warning("Файл logo.jpg не найден в директории приложения")

st.title("🌾 Получение бюллетеня")
st.markdown("Заполните поля и нажмите кнопку, чтобы получить бюллетень.")

# Форма ввода
with st.form("bulletin_form"):
    col1, col2 = st.columns(2)
    with col1:
        lat = st.text_input("Широта (lat)", value="55.7558")
    with col2:
        lon = st.text_input("Долгота (lon)", value="37.6173")

    farm_name = st.text_input("Название хозяйства", value="")
    crop = st.text_input("Культура", value="")

    submitted = st.form_submit_button("Получить бюллетень")

# Обработка отправки
if submitted:
    if not all([lat, lon, farm_name, crop]):
        st.error("Пожалуйста, заполните все поля.")
    else:
        base_url = "https://webhook.nodul.ru/28657/prod/3a93f2b4-c2f7-47a1-a808-9d9668975aa9"
        params = {
            "lat": lat,
            "lon": lon,
            "farm_name": farm_name,
            "crop": crop,
            "stage": "Кущение",
        }
        # Собираем URL с URL-кодированием параметров
        query = "&".join(f"{k}={quote(str(v), safe='')}" for k, v in params.items())
        url = f"{base_url}?{query}"

        headers = {"Expect": ""}  # Обход ошибки 417

        try:
            with st.spinner("Отправка запроса..."):
                response = requests.get(url, headers=headers, timeout=60)

            st.success(f"Статус ответа: {response.status_code}")

            # Пытаемся распарсить JSON
            try:
                data = response.json()
                st.subheader("Ответ сервера (JSON):")
                st.json(data)
            except ValueError:
                st.warning("Ответ не является валидным JSON. Показан текст:")
                st.code(response.text)

        except requests.exceptions.RequestException as e:
            st.error(f"Ошибка при выполнении запроса: {e}")

# Копирайт внизу
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>ГК Юзтех © 2026</div>",
    unsafe_allow_html=True,
)
