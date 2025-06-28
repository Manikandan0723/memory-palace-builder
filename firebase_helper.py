import pyrebase
import streamlit as st

def init_firebase():
    config = dict(st.secrets["firebase"])
    firebase = pyrebase.initialize_app(config)
    return firebase
