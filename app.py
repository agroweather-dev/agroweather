import streamlit as st
import requests
import os
from PIL import Image

st.set_page_config(page_title="Агрометеорологический агент", page_icon="🌾", layout="wide")

# --- ЛОГОТИП (светлая тема) ---
logo_path = "usetech-logo-green-dark.png"
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    st.image(logo, width=200)

st.title("Агрометеорологический агент")
st.markdown("Заполните данные слева, чтобы получить бюллетень.")

# --- РАЗДЕЛЕНИЕ НА ДВЕ КОЛОНКИ ---
col_input, col_result = st.columns([1, 2])

# ================= ЛЕВАЯ КОЛОНКА (ВВОД ДАННЫХ) =================
with col_input:
    st.subheader("Данные для прогноза")
    
    lat = st.number_input("Широта (lat)", value=55.75, format="%.4f")
    lon = st.number_input("Долгота (lon)", value=37.62, format="%.4f")
    farm_name = st.text_input("Название хозяйства", "СПК Рассвет")
    crop = st.text_input("Культура", "Озимая пшеница")
    
    # Кнопка запуска
    if st.button("Получить бюллетень", use_container_width=True):
        st.session_state['run_analysis'] = True

# ================= ПРАВАЯ КОЛОНКА (РЕЗУЛЬТАТ) =================
with col_result:
    if st.session_state.get('run_analysis', False):
        with st.spinner("Запрашиваем данные..."):
            url = f"https://webhook.nodul.ru/28657/prod/3a93f2b4-c2f7-47a1-a808-9d9668975aa9?lat={lat}&lon={lon}&farm_name={farm_name}&crop={crop}&stage=Кущение"
            
            try:
                response = requests.get(url, headers={"Expect": ""})
                if response.status_code == 200:
                    data = response.json()
                    st.success("Данные успешно получены!")
                    
                    # --- БЮЛЛЕТЕНЬ ---
                    st.subheader("📝 Бюллетень")
                    st.info(data.get("bulletin_text", "Текст не найден"))
                    
                    # --- РИСКИ (ПОНЯТНОЕ ОФОРМЛЕНИЕ) ---
                    st.subheader("⚠️ Выявленные риски")
                    risks = data.get("risks", [])
                    
                    if risks:
                        for risk in risks:
                            # Определяем цвет для уровня опасности
                            severity = risk.get("severity", "unknown")
                            if severity == "critical":
                                bg_color = "#ff4b4b" # Красный
                                icon = "🔴"
                            elif severity == "high":
                                bg_color = "#ffa500" # Оранжевый
                                icon = "🟠"
                            else:
                                bg_color = "#ffd700" # Желтый
                                icon = "🟡"
                                
                            # Карточка риска
                            with st.container():
                                st.markdown(f"""
                                <div style="border: 2px solid {bg_color}; padding: 15px; border-radius: 10px; margin-bottom: 15px; background-color: #f9f9f9;">
                                    <h4 style="margin-top: 0; color: {bg_color};">{icon} {risk.get('name', 'Неизвестный риск')}</h4>
                                    <p><b>Уровень опасности:</b> <span style="color: {bg_color}; font-weight: bold;">{severity.upper()}</span></p>
                                    <p><b>Когда:</b> {', '.join(risk.get('dates', ['Нет данных']))}</p>
                                    <p><b>Последствия:</b> {risk.get('agro_impact', 'Нет данных')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.success("Рисков не обнаружено. Погода стабильна.")
                        
                else:
                    st.error(f"Ошибка сервера: {response.status_code}")
            except Exception as e:
                st.error(f"Ошибка подключения: {e}")
    else:
        st.info("Здесь появится ваш бюллетень.")

# --- КОПИРАЙТ ВНИЗУ ---
st.markdown("---")
st.caption("ГК Юзтех © 2026")