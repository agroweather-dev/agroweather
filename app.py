import streamlit as st
import requests
import pandas as pd
import json
import os

# === НАСТРОЙКИ ===
NODUL_WEBHOOK_URL = "https://webhook.nodul.ru/28657/prod/3a93f2b4-c2f7-47a1-a808-9d9668975aa9"
LOGO_PATH = "logo.jpg"  # Имя файла с логотипом (положите его рядом с app.py)
# =================

st.set_page_config(page_title="Агрометеорологический агент", layout="wide")

# --- Боковая панель с вводом ---
with st.sidebar:
    # Добавляем логотип в сайдбар
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.warning(f"⚠️ Файл {LOGO_PATH} не найден. Положите его в папку со скриптом.")

    st.header("Координаты")
    lat = st.number_input("Широта (latitude)", value=45.04, format="%.4f")
    lon = st.number_input("Долгота (longitude)", value=38.98, format="%.4f")

    st.divider()
    st.header("Параметры (если нужны вашему пайплайну)")
    # Раскомментируйте и добавьте, если ваш вебхук принимает доп. параметры
    # days = st.slider("Дней прогноза", 1, 10, 10)
    # hist_years = st.slider("Лет истории для сравнения", 1, 5, 3)

    run = st.button("🚀 Запустить анализ", type="primary", use_container_width=True)

# --- Основной интерфейс ---
st.title("🌾 Агрометеорологический бюллетень")
st.caption("Введите координаты — агент запросит прогноз, исторические данные и сформирует отчёт о рисках.")

# --- Основная логика ---
if run:
    payload = {
        "latitude": lat,
        "longitude": lon,
        # "days": days,        # добавьте, если нужно
        # "hist_years": hist_years,
    }

    with st.spinner("Агент анализирует погоду..."):
        try:
            # Заголовок Expect отключён, чтобы избежать ошибки 417
            response = requests.post(
                NODUL_WEBHOOK_URL,
                json=payload,
                timeout=60,
                headers={"Expect": ""}
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.Timeout:
            st.error("⏱️ Nodul не ответил за 60 секунд. Проверьте, что сценарий активен.")
            st.stop()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Ошибка запроса к Nodul: {e}")
            st.stop()
        except json.JSONDecodeError:
            st.error("❌ Nodul вернул не JSON. Проверьте настройки вывода в сценарии.")
            st.stop()

    st.success("Готово!")

    # --- Отображение результата ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📋 Бюллетень")
        bulletin = result.get("bulletin") or result.get("text") or result.get("report")
        if bulletin:
            st.markdown(bulletin)
        else:
            st.warning("В ответе нет поля с текстом бюллетеня. Проверьте ключи JSON ниже.")

    with col2:
        st.subheader("⚠️ Риски")
        risks = result.get("risks") or result.get("warnings") or []
        if risks:
            for r in risks:
                st.warning(str(r))
        else:
            st.info("Рисков не обнаружено (или поле отсутствует в ответе).")

    # --- График прогноза (если Nodul возвращает daily-массивы) ---
    st.subheader("📈 Прогноз на 10 дней")
    daily = result.get("daily") or result.get("forecast")
    if daily:
        try:
            df = pd.DataFrame(daily)
            if "time" in df.columns:
                df["time"] = pd.to_datetime(df["time"])
                df = df.set_index("time")

            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            if numeric_cols:
                st.line_chart(df[numeric_cols])
            else:
                st.dataframe(df)
        except Exception as e:
            st.warning(f"Не удалось построить график автоматически: {e}")
            st.dataframe(daily)
    else:
        st.info("В ответе нет поля `daily`/`forecast` для графика. Можно посмотреть сырой JSON ниже.")

    # --- Сырой JSON (для отладки) ---
    with st.expander("🔍 Сырой ответ от Nodul (для проверки структуры)"):
        st.json(result)

else:
    # Заглушка до первого запуска
    st.info("👈 Задайте координаты в боковой панели и нажмите «Запустить анализ».")
    st.markdown("""
    **Что делает агент:**
    1. Запрашивает прогноз Open-Meteo на 10 дней.
    2. Запрашивает исторические данные для сравнения.
    3. Анализирует заморозки, избыточные осадки и дефицит влаги.
    4. Формирует бюллетень с рекомендациями.
    """)

# --- Футер с копирайтом (выводится всегда, в самом низу) ---
st.divider()
st.caption("Копирайт ГК Юзтех @ 2026")
