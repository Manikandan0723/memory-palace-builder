import pyrebase
import json
import os
import streamlit as st

def init_firebase():
    # Get the config JSON string from secrets and parse it
    config = json.loads(st.secrets["firebase_config.json"])
    firebase = pyrebase.initialize_app(config)
    return firebase
