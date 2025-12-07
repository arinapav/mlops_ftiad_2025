import streamlit as st
import requests
import json

import streamlit as st
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Логируем переменные окружения
logger.debug(f"MINIO_ENDPOINT: {os.getenv('MINIO_ENDPOINT')}")
logger.debug(f"MINIO_ACCESS_KEY: {os.getenv('MINIO_ACCESS_KEY')}")
logger.debug(f"MINIO_SECRET_KEY: {os.getenv('MINIO_SECRET_KEY')}")

st.set_page_config(page_title="MLOps HW2 — Dashboard", layout="wide")
st.title("MLOps Homework 2 — Dashboard")

# ============================
# Авторизация
# ============================
st.markdown("### Авторизация")
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("Получить токен", type="primary"):
        try:
            r = requests.post("http://127.0.0.1:8000/token")
            r.raise_for_status()
            st.session_state.token = r.json()["access_token"]
            st.success("Токен получен!")
        except Exception as e:
            st.error(f"Ошибка: {e}")

with col2:
    token = st.text_input(
        "Токен",
        value=st.session_state.get("token", ""),
        type="password",
        help="Нужен для всех операций"
    )

headers = {"Authorization": f"Bearer {token}"} if token else {}

st.markdown("---")

# ============================
# 1. Загрузка датасета в DVC
# ============================
st.markdown("### Загрузка и версионирование датасета (DVC → Minio)")

col_up1, col_up2 = st.columns([3, 1])
with col_up1:
    uploaded_file = st.file_uploader("CSV-файл (должен быть столбец `target`)", type="csv")
with col_up2:
    dataset_name = st.text_input("Имя датасета", value="data")

if st.button("Загрузить и закоммитить в DVC", type="secondary"):
    if not token:
        st.error("Сначала получите токен!")
    elif not uploaded_file:
        st.warning("Выберите файл")
    else:
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
            data = {"dataset_name": dataset_name}
            r = requests.post(
                "http://127.0.0.1:8000/upload_dataset/",
                files=files,
                data=data,
                headers=headers
            )
            if r.status_code == 200:
                st.success(f"Датасет `{dataset_name}` успешно заверсионирован в DVC и Minio!")
            else:
                st.error(f"Ошибка: {r.text}")
        except Exception as e:
            st.error(f"Ошибка: {e}")

st.markdown("---")

# ============================
# 2. Обучение модели
# ============================
st.markdown("### Обучение модели")

col_model, col_ds = st.columns(2)
with col_model:
    model_type = st.selectbox("Тип модели", ["forest", "logreg"])
with col_ds:
    dataset_name_train = st.text_input("Имя датасета из DVC", value="data")

col_p1, col_p2 = st.columns(2)
with col_p1:
    if model_type == "forest":
        n_estimators = st.number_input("n_estimators", value=100, min_value=1)
        max_depth = st.number_input("max_depth (None = без ограничения)", value=None, min_value=1)
    else:
        max_iter = st.number_input("max_iter", value=100, min_value=1)

with col_p2:
    if model_type == "logreg":
        C = st.number_input("C (регуляризация)", value=1.0, min_value=0.0001, format="%.6f")

if st.button("Обучить модель", type="primary"):
    if not token:
        st.error("Нужен токен!")
    else:
        try:
            params = {}
            if model_type == "forest":
                params["n_estimators"] = int(n_estimators)
                if max_depth is not None:
                    params["max_depth"] = int(max_depth)
            else:
                params["max_iter"] = int(max_iter)
                params["C"] = float(C)

            payload = {
                "model_type": model_type,
                "params": params,
                "dataset_name": dataset_name_train
            }

            r = requests.post("http://127.0.0.1:8000/train/", json=payload, headers=headers)
            if r.status_code == 200:
                st.success(f"Модель `{model_type}` успешно обучена!")
                st.json(r.json())
                st.info("Эксперимент залогирован в MLflow → http://localhost:5000")
            else:
                st.error(f"Ошибка: {r.text}")
        except Exception as e:
            st.error(f"Ошибка: {e}")

st.markdown("---")

# ============================
# Статус и ссылки
# ============================
st.markdown("### Полезные ссылки")
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown("[API Docs](http://localhost:8000/docs)")
with col_b:
    st.markdown("[Minio Console](http://localhost:9001) (minioadmin/minioadmin)")
with col_c:
    st.markdown("[MLflow UI](http://localhost:5000)")

if st.button("Проверить API"):
    try:
        r = requests.get("http://127.0.0.1:8000/health")
        st.success("Сервис работает!")
    except:
        st.error("Сервис недоступен")
