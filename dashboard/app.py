import streamlit as st
import requests

st.title("MLOps Dashboard")

token = st.text_input("Token", "get from /token")
name = st.selectbox("Model", ["forest", "logreg"])
features = st.text_input("Features", "[5.1, 3.5, 1.4, 0.2]")

if st.button("Predict"):
    try:
        r = requests.post(
            f"http://127.0.0.1:8000/predict/{name}",
            json=eval(features),
            headers={"Authorization": f"Bearer {token}"}
        )
        st.success(f"Prediction: {r.json()['pred']}")
    except Exception as e:
        st.error(f"Error: {e}")
