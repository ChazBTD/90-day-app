#this is supabasecode.py

import streamlit as st
from supabase import create_client, Client
import json
import datetime as _dt
from supabase.lib.auth_client import AuthApiError

SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")

@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase(SUPABASE_URL, SUPABASE_KEY)

def signup_or_login(email: str, password):
    """
    Attempts to log in an existing user.
    If login fails due to a user not existing, it falls back to a signup process.
    """
    username = email.strip().lower()

    if not supabase:
        return False, "Database connection failed."

    try:
        # 1. Attempt to log in with the provided credentials.
        result = supabase.auth.sign_in_with_password({"email": username, "password": password})
        msg = "Logged in."

    except AuthApiError as e:
        # Catch specific errors to distinguish between login failure and a new user.
        error_message = str(e)
        
        # Check if the login failed because the user doesn't exist
        if "Invalid login credentials" in error_message:
            st.write("User not found. Attempting to sign up...")
            try:
                # 2. If login fails for an unknown user, attempt to sign them up.
                result = supabase.auth.sign_up({"email": username, "password": password})
                
                # IMPORTANT: This is a security risk. Storing a plaintext password
                # in your table should be removed once testing is complete.
                supabase.table("user_plans").insert({
                    "user_id": username,
                    "password": password,
                    "start_date": _dt.date.today().isoformat(),
                    "raw_text": "",
                    "months": json.dumps({}),
                    "weeks": json.dumps({}),
                    "all_weeks": json.dumps({}),
                    "super_goal": "",
                    "banner_url": ""
                }).execute()
                
                msg = "Account created. You can now log in."

            except AuthApiError as signup_e:
                # This will catch errors during signup, like "User already registered".
                if "User already registered" in str(signup_e):
                    # This case should technically not be reached with the new logic,
                    # but it's a good fallback to handle race conditions or other issues.
                    return False, "This email is already registered."
                else:
                    return False, f"Signup failed: {signup_e}"
        else:
            # Handle other AuthApiErrors (e.g., rate-limiting, disabled email provider).
            return False, f"Login failed: {e}"

    # After a successful login or signup, set session variables
    st.query_params["access_token"] = result.session.access_token
    st.query_params["refresh_token"] = result.session.refresh_token
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
    #Since the signup sets the start date, this is the handle old accounts
    if not raw:                                  
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