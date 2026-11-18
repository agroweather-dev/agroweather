import streamlit as st
import requests

st.set_page_config(page_title="Агрометеорологический агент", page_icon="🌾")

st.title("🌾 Агрометеорологический агент")
st.write("Введите координаты, чтобы получить прогноз и рекомендации.")

lat = st.number_input("Широта (lat)", value=55.75, format="%.4f")
lon = st.number_input("Долгота (lon)", value=37.62, format="%.4f")
farm_name = st.text_input("Название хозяйства", "СПК Рассвет")
crop = st.text_input("Культура", "Озимая пшеница")

if st.button("Получить бюллетень"):
    with st.spinner("Запрашиваем данные..."):
        url = f"https://webhook.nodul.ru/28657/prod/19621674-81e4-45d9-8c67-91548b8695da?lat={lat}&lon={lon}&farm_name={farm_name}&crop={crop}&stage=Кущение"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                st.success("Данные получены!")
                
                st.subheader("📝 Бюллетень")
                st.info(data.get("bulletin_text", "Текст не найден"))
                
                st.subheader("⚠️ Риски")
                st.json(data.get("risks", []))
            else:
                st.error(f"Ошибка: {response.status_code}")
        except Exception as e:
            st.error(f"Ошибка подключения: {e}")
