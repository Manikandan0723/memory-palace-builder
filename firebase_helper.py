import streamlit as st
import pyrebase

def init_firebase():
    config = dict(st.secrets["firebase"])
    firebase = pyrebase.initialize_app(config)
    return firebase
