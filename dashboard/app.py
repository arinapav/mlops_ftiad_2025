import streamlit as st
import requests
import json

st.set_page_config(page_title="MLOps HW2 Dashboard", layout="wide")
st.title("MLOps Homework 2 — Dashboard")

# ============================
# Авторизация
# ============================
st.markdown("### Авторизация")
col_token1, col_token2 = st.columns([1, 3])
with col_token1:
    if st.button("Получить токен", type="primary"):
        try:
            r = requests.post("http://127.0.0.1:8000/token")
            r.raise_for_status()
            token_data = r.json()
            st.session_state.token = token_data["access_token"]
            st.success("Токен получен!")
        except Exception as e:
            st.error(f"Ошибка: {e}")
with col_token2:
    token = st.text_input(
        "Токен доступа",
        value=st.session_state.get("token", ""),
        type="password",
        help="Токен нужен для всех защищённых операций"
    )

headers = {"Authorization": f"Bearer {token}"} if token else {}

st.markdown("---")

# ============================
# 1. Загрузка и версионирование датасета (DVC)
# ============================
st.markdown("### Загрузка и версионирование датасета через DVC")
col_up1, col_up2 = st.columns([3, 1])
with col_up1:
    uploaded_file = st.file_uploader(
        "Выберите CSV-файл с данными (обязательно колонка `target` в конце)",
        type=["csv"],
        help="После загрузки датасет будет сохранён и заверсионирован в DVC → Minio"
    )
with col_up2:
    dataset_name = st.text_input("Имя версии датасета", value="data", help="Без расширения .csv")

if st.button("Загрузить и закоммитить датасет в DVC", type="secondary"):
    if not token:
        st.error("Сначала получите токен!")
    elif not uploaded_file:
        st.warning("Выберите файл для загрузки")
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
            st.error(f"Ошибка загрузки: {e}")

st.markdown("---")

# ============================
# 2. Обучение модели (с выбором датасета)
# ============================
st.markdown("### Обучение новой модели")
col_model, col_dataset = st.columns(2)
with col_model:
    train_model_type = st.selectbox("Тип модели", ["forest", "logreg"], key="train_type")
with col_dataset:
    train_dataset_name = st.text_input("Имя датасета из DVC", value="data", help="Будет сделан dvc pull перед обучением")

col_params1, col_params2 = st.columns(2)

with col_params1:
    if train_model_type == "forest":
        n_estimators = st.number_input("n_estimators", value=100, min_value=1, step=10)
        max_depth_input = st.number_input("max_depth (оставь пустым = None)", value=None, min_value=1, step=1, placeholder="None")
        max_depth = None if max_depth_input is None else int(max_depth_input)
    else:  # logreg
        max_iter = st.number_input("max_iter", value=100, min_value=1, step=50)

with col_params2:
    if train_model_type == "logreg":
        C = st.number_input("C (регуляризация)", value=1.0, min_value=0.0001, step=0.1, format="%.6f")

if st.button("Обучить модель", type="primary"):
    if not token:
        st.error("Нужен токен!")
    else:
        try:
            if train_model_type == "forest":
                params = {"n_estimators": int(n_estimators)}
                if max_depth is not None:
                    params["max_depth"] = int(max_depth)
            else:  # logreg
                params = {
                    "max_iter": int(max_iter),
                    "C": float(C)}
