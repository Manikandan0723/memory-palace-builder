import pyrebase
import json
import streamlit as st

def init_firebase():
    config = json.loads(st.secrets["FIREBASE_CONFIG"])
    firebase = pyrebase.initialize_app(config)
    return firebase
