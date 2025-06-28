import pyrebase
import json
import os
import streamlit as st

def init_firebase():
    # Get the config JSON string from secrets and parse it
    config = json.loads(st.secrets["FIREBASE_CONFIG"])
    firebase = pyrebase.initialize_app(config)
    return firebase
