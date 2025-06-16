import streamlit as st
from supabase import create_client, Client
import json
import os

SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()
CRED_FILE = ".usercreds.json"

def signup_or_login(username, password):
    """Create user if new; otherwise validate password."""
    row = supabase.table("user_plans").select("password").eq("user_id", username).execute()
    if not row.data:                         # sign-up path
        supabase.table("user_plans").insert({
            "user_id":   username,
            "password":  password,
            "raw_text":  "",
            "months":    json.dumps({}),
            "weeks":     json.dumps({}),
            "all_weeks": json.dumps({})
        }).execute()
        return True, "Account created."

    stored_password = row.data[0]["password"]
    if stored_password == password:     # login path
        return True, "Logged-in."
    return False, "Wrong password."

def load_plan(user_id):
    #MAKE THIS INTO UNDERSTANDABLE LATER: Load plan into session_state; return True iff raw_text is non-empty
    row = supabase.table("user_plans").select("*").eq("user_id", user_id).single().execute()
    if not row.data:          # should never happen after sign-up
        return False
    st.session_state.raw_text  = row.data["raw_text"]
    st.session_state.months    = json.loads(row.data["months"])
    st.session_state.weeks     = json.loads(row.data["weeks"])
    st.session_state.all_weeks = json.loads(row.data["all_weeks"])
    return bool(st.session_state.raw_text)   # ← TRUE only if a real plan exists

#SAVING every time there are major plan changes like task edits
def save_plan(user_id):
    st.info('save_plan called?')
    supabase.table("user_plans").update({
        "raw_text": st.session_state.raw_text,
        "months": json.dumps(st.session_state.months),
        "weeks": json.dumps(st.session_state.weeks),
        "all_weeks": json.dumps(st.session_state.all_weeks)
    }).eq("user_id", user_id).execute()

def save_local_creds(user_id, password):
    with open(CRED_FILE, "w") as f:
        json.dump({"user_id": user_id, "password": password}, f)

def load_local_creds():
    if os.path.exists(CRED_FILE):
        try:
            with open(CRED_FILE, "r") as f:
                creds = json.load(f)
                return creds.get("user_id"), creds.get("password")
        except json.JSONDecodeError:
            return None, None  # corrupted or empty file
    return None, None


def clear_local_creds():
    if os.path.exists(CRED_FILE):
        os.remove(CRED_FILE)
