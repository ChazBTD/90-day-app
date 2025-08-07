#this is supabasecode.py

import streamlit as st
from supabase import create_client, Client
import json
import datetime as _dt
from gotrue.errors import AuthApiError

SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

def signup_or_login(email: str, password):
    """Create user if new; otherwise validate password. Uses Supabase auth token."""
    username = email.strip().lower()

    try:
        result = supabase.auth.sign_in_with_password({"email": username, "password": password})
        msg = "Logged in."

    except AuthApiError:
        try:
            result = supabase.auth.sign_up({"email": username, "password": password})
            supabase.table("user_plans").insert({
                "user_id":   username,
                "password":  password,
                "start_date": _dt.date.today().isoformat(),
                "raw_text":  "",
                "months":    json.dumps({}),
                "weeks":     json.dumps({}),
                "all_weeks": json.dumps({}),
                "super_goal": "",
                "banner_url": ""
            }).execute()
            msg = "Account made"

        except AuthApiError as e:
            if "User already registered" in str(e):
                return False, "Wrong password."
            else:
                return False, f"Auth error: {e}"

    st.query_params["access_token"] = result.session.access_token
    st.query_params["refresh_token"] =result.session.refresh_token
    st.session_state.username = username
    return True, msg

def load_plan(user_id):
    row = supabase.table("user_plans").select("*").eq("user_id", user_id).single().execute()
    if not row.data:          # should never happen after sign-up
        return False
    #this following line gives start_date the latest supabase start_date or today
    st.session_state.start_date = get_or_init_start_date(user_id)
    st.session_state.raw_text  = row.data["raw_text"]
    st.session_state.months    = json.loads(row.data["months"])
    st.session_state.weeks     = json.loads(row.data["weeks"])
    st.session_state.all_weeks = json.loads(row.data["all_weeks"])
    st.session_state.super_goal = row.data.get("super_goal", "")
    st.session_state.banner_url = row.data.get("banner_url", "") #emtpy strings are falsy
    return bool(st.session_state.raw_text)   # ← TRUE only if a real plan exists

#SAVING every time there are major plan changes like task edits
def save_plan(user_id):
    st.info('plan saved!')
    supabase.table("user_plans").update({
        "raw_text": st.session_state.raw_text,
        "months": json.dumps(st.session_state.months),
        "weeks": json.dumps(st.session_state.weeks),
        "all_weeks": json.dumps(st.session_state.all_weeks),
        "super_goal": st.session_state.super_goal,
        "banner_url": st.session_state.get("banner_url", "")
    }).eq("user_id", user_id).execute()


#time helpers
def get_or_init_start_date(user_id: str) -> _dt.date:
    row = supabase.table("user_plans").select("start_date").eq("user_id", user_id).single().execute()
    raw = row.data.get("start_date")
    if not raw:                                  # handle old accounts
        today = _dt.date.today()
        supabase.table("user_plans").update({"start_date": today.isoformat()}).eq("user_id", user_id).execute()
        return today
    return _dt.date.fromisoformat(raw)

def set_start_date(user_id: str, new_date: _dt.date):
    supabase.table("user_plans").update({"start_date": new_date.isoformat()}).eq("user_id", user_id).execute()

def upload_banner(user_id: str, data: bytes) -> str:
    file_path = f"{user_id}/banner.png"
    supabase.storage.from_("banners").upload(
        file_path,
        data,
        {'upsert':'true',})
    public_url_response = supabase.storage.from_("banners").get_public_url(file_path)
    return public_url_response

#autosave, does work in local testing
"""
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
"""