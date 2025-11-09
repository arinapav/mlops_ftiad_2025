import streamlit as st
import requests
import json

st.title("MLOps Dashboard")

st.markdown("### Авторизация")
if st.button("Получить токен"):
    try:
        r = requests.post("http://127.0.0.1:8000/token")
        token_data = r.json()
        st.session_state.token = token_data["access_token"]
        st.success("Токен получен!")
    except Exception as e:
        st.error(f"Ошибка получения токена: {e}")

token = st.text_input("Токен доступа", value=st.session_state.get("token", ""))

st.markdown("---")
st.markdown("### Обучение модели")

col1, col2 = st.columns(2)
with col1:
    train_model_type = st.selectbox("Тип модели для обучения", ["forest", "logreg"])
with col2:
    if train_model_type == "forest":
        n_estimators = st.number_input("n_estimators", value=100, min_value=1)
        max_depth = st.number_input("max_depth", value=5, min_value=1)
    else:  # logreg
        max_iter = st.number_input("max_iter", value=100, min_value=1)
        C = st.number_input("C (regularization)", value=1.0, min_value=0.01)

X_train = st.text_area(
    "Данные X (JSON формат)", 
    '[[5.1,3.5,1.4,0.2],[4.9,3.0,1.4,0.2],[4.7,3.2,1.3,0.2],[7.0,3.2,4.7,1.4],[6.4,3.2,4.5,1.5],[6.9,3.1,4.9,1.5]]'
)
y_train = st.text_input("Метки y (JSON формат)", '[0,0,0,1,1,1]')

if st.button("Обучить модель"):
    if not token:
        st.error("Сначала получите токен!")
    else:
        try:
            # Формируем правильные параметры для каждой модели
            if train_model_type == "forest":
                params = {
                    "n_estimators": int(n_estimators),
                    "max_depth": int(max_depth)
                }
            else:  # logreg
                params = {
                    "max_iter": int(max_iter),
                    "C": float(C)
                }
            
            payload = {
                "model_type": train_model_type,
                "params": params,
                "data": {
                    "X": json.loads(X_train),
                    "y": json.loads(y_train)
                }
            }
            
            r = requests.post(
                "http://127.0.0.1:8000/train/",
                json=payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            if r.status_code == 200:
                st.success(f"Модель обучена: {r.json()}")
            else:
                st.error(f"Ошибка: {r.text}")
        except Exception as e:
            st.error(f"Ошибка: {e}")

st.markdown("---")
st.markdown("### Список доступных моделей")

if st.button("Показать доступные модели"):
    if not token:
        st.error("Сначала получите токен!")
    else:
        try:
            r = requests.get(
                "http://127.0.0.1:8000/models/",
                headers={"Authorization": f"Bearer {token}"}
            )
            if r.status_code == 200:
                st.json(r.json())
            else:
                st.error(f"Ошибка: {r.text}")
        except Exception as e:
            st.error(f"Ошибка: {e}")

st.markdown("---")
st.markdown("### Предсказание")

predict_model = st.selectbox("Модель для предсказания", ["forest", "logreg"], key="predict")
features = st.text_input("Признаки (JSON формат)", "[5.1, 3.5, 1.4, 0.2]")

if st.button("Предсказать"):
    if not token:
        st.error("Сначала получите токен!")
    else:
        try:
            payload = {"features": json.loads(features)}
            r = requests.post(
                f"http://127.0.0.1:8000/predict/{predict_model}",
                json=payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            if r.status_code == 200:
                st.success(f"Предсказание: {r.json()['prediction']}")
            else:
                st.error(f"Ошибка: {r.text}")
        except Exception as e:
            st.error(f"Ошибка: {e}")

st.markdown("---")
st.markdown("### Управление моделями")

delete_model = st.selectbox("Модель для удаления", ["forest", "logreg"], key="delete")

if st.button("Удалить модель"):
    if not token:
        st.error("Сначала получите токен!")
    else:
        try:
            r = requests.delete(
                f"http://127.0.0.1:8000/delete/{delete_model}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if r.status_code == 200:
                st.success(f"Модель удалена: {r.json()}")
            else:
                st.error(f"Ошибка: {r.text}")
        except Exception as e:
            st.error(f"Ошибка: {e}")

st.markdown("---")
st.markdown("### Переобучение модели")

retrain_model = st.selectbox("Модель для переобучения", ["forest", "logreg"], key="retrain")

if retrain_model == "forest":
    retrain_n_estimators = st.number_input("n_estimators для переобучения", value=150, min_value=1)
    retrain_max_depth = st.number_input("max_depth для переобучения", value=10, min_value=1)
else:
    retrain_max_iter = st.number_input("max_iter для переобучения", value=200, min_value=1)
    retrain_C = st.number_input("C для переобучения", value=0.5, min_value=0.01)

X_retrain = st.text_area("Новые данные X", '[[7.0, 3.2, 4.7, 1.4], [6.4, 3.2, 4.5, 1.5]]', key="retrain_X")
y_retrain = st.text_input("Новые метки y", '[1, 1]', key="retrain_y")

if st.button("Переобучить модель"):
    if not token:
        st.error("Сначала получите токен!")
    else:
        try:
            if retrain_model == "forest":
                params = {
                    "n_estimators": int(retrain_n_estimators),
                    "max_depth": int(retrain_max_depth)
                }
            else:
                params = {
                    "max_iter": int(retrain_max_iter),
                    "C": float(retrain_C)
                }
            
            payload = {
                "model_type": retrain_model,
                "params": params,
                "data": {
                    "X": json.loads(X_retrain),
                    "y": json.loads(y_retrain)
                }
            }
            
            r = requests.post(
                f"http://127.0.0.1:8000/retrain/{retrain_model}",
                json=payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            if r.status_code == 200:
                st.success(f"Модель переобучена: {r.json()}")
            else:
                st.error(f"Ошибка: {r.text}")
        except Exception as e:
            st.error(f"Ошибка: {e}")

st.markdown("---")
st.markdown("### Статус сервиса")

if st.button("Проверить статус"):
    try:
        r = requests.get("http://127.0.0.1:8000/health")
        if r.status_code == 200:
            st.success(f"Сервис работает: {r.json()}")
        else:
            st.error(f"Ошибка: {r.text}")
    except Exception as e:
        st.error(f"Сервис недоступен: {e}")
