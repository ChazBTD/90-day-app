#This is roadmap.py

import streamlit as st
import math
import time
import datetime as _dt

#this has to come before st.cache and other stuff is initiated
st.set_page_config(page_title="90-Day Goal Engineer", layout="wide", initial_sidebar_state="collapsed")


from generation import plan, parse, inline_text_input, render_footer, test_structure_dictionary
from milestone import render_day_block, render_week_block, update_progress
from supabasecode import signup_or_login, load_plan, save_plan, set_start_date
from supabasecode import supabase

def compute_day_week():
    delta = (_dt.date.today() - st.session_state.start_date).days
    delta = max(0, delta)                        # never negative
    st.session_state.current_week = delta // 7 + 1
    st.session_state.current_day  = delta % 7 + 1

# 1) Render the “input” page where user defines super goal, profile, etc.
def render_input_page():
    if st.button("Sign Out Completely", key="input_sign_out_button"):
        sign_out()

    st.markdown("---")
    goal = inline_text_input("I want to", "in 90 days.", 1,
        "build a software startup newsletter and scale it to 1000 target audiences (college students who want to build viral apps.)",
        key="super_goal_input"
    )
    profile = inline_text_input(
        "For more context, I am a", "", 2.8,
        "product manager for a 50-people B2B SAAS with 5 years experience", 
        key="profile_input"
    )

    # Predefined structures (if user checks “Use Structure”)
    structure_dictionary = test_structure_dictionary

    use_structure = st.checkbox(
        "Use Structure", 
        key="use_structure_checkbox",
        help="Use predefined structure for your 3-month plan."
    )
    month_structure = None
    if use_structure:
        structure_options = st.selectbox(
            label=" ",
            label_visibility="collapsed",
            key="structure_select",
            options=list(structure_dictionary.keys()),
            help="Use 3 if you are uncertain about goal."
        )
        month_structure = structure_dictionary[structure_options]

    if st.button("Lock in my Plan 😤", type="primary"):
        st.session_state.super_goal = "Super Goal: I want to " + st.session_state.super_goal_input + " in 90 days."
        st.session_state.profile = "For better context I am a " + st.session_state.profile_input + "."

        if st.session_state.super_goal:
            with st.spinner("Be Patient..."):
                #CALLING the PLAN with one necesary variable
                raw_text = plan(st.session_state.super_goal, st.session_state.profile, month_structure)
                if raw_text:
                    #first clear all daily actions
                    st.session_state.all_weeks = {}
                    st.session_state.raw_text = raw_text
                    parsed_plan = parse(raw_text)
                    st.session_state.months = parsed_plan["month_list"]
                    st.session_state.weeks = parsed_plan["week_list"]
                    st.session_state.page = 'roadmap'
                    save_plan(st.session_state.username)
                    st.rerun()
        else:
            st.warning("Please enter your Super Goal first!", icon="⚠️")

    render_footer()

# This comes before the roadmap at all times
def show_progress_boss():
    week_num = st.session_state.current_week
    day_num = st.session_state.current_day
    week_key = f"Week_{week_num}"

    #BOSS state based on completed/total tasks made PROGRESS
    st.markdown(f"## Your boss for Week {week_num} Day {day_num}")
    update_progress(week_key, False)
    percentage = st.session_state.milestone_progress.get(week_key, 0)
    if percentage == 100:
        st.image("state3.png", width=300)
    elif percentage >= 50:
        st.image("state2.png", width=300)
    elif percentage < 50:
        st.image("state1.png", width=300)
    st.markdown(f"### progress: {percentage}%")

    week_days = st.session_state.all_weeks.get(week_key, [None]*7)
    today_tasks = week_days[int(day_num) - 1]

    if today_tasks:
        st.markdown("### Today's stuff")
        for idx, (text, done_flag) in enumerate(today_tasks):
            widget_key = f"{week_key}_day{day_num}_task{idx}_roadmap"
            checked = st.checkbox(text, value=done_flag, key=widget_key)
            if checked != done_flag:
                today_tasks[idx][1] = checked
                save_plan(st.session_state.username)
                st.rerun()

    notes = st.session_state.milestone_notes.get(week_key)
    if notes:
        st.markdown("### Notes from this week:")
        st.markdown(f"{notes}")

def render_dashboard():
    st.title("🎯 90-Day Goal Engineer")
    
    if st.button("Create New Plan", key="new_plan_button"):
        st.info("new plan started")
        time.sleep(2)
        st.session_state.page = 'input'
        st.rerun()
    if st.button("Sign Out Completely", key="roadmap_sign_out_button"):
        sign_out() 

    compute_day_week()
    st.markdown(
        f"### 📆 Day **{st.session_state.current_day}**  |  "
        f"Week **{st.session_state.current_week}**"
    )
    col_b, col_r, col_f = st.columns(3)

    if col_b.button("⬅️ Back 1 day"):
        new_start = st.session_state.start_date + _dt.timedelta(days=1)
        set_start_date(st.session_state.username, new_start)
        st.session_state.start_date = new_start
        st.rerun()

    if col_r.button("🔄 Reset Day 1 → Today"):
        today = _dt.date.today()
        set_start_date(st.session_state.username, today)
        st.session_state.start_date = today
        st.rerun()

    if col_f.button("➡️ Forward 1 day"):
        new_start = st.session_state.start_date - _dt.timedelta(days=1)
        set_start_date(st.session_state.username, new_start)
        st.session_state.start_date = new_start
        st.rerun()


    #NOT show if day view using psuedocode selection
    if st.session_state.active_view == "full" or st.session_state.active_view == "month" or st.session_state.active_view == "week":
        show_progress_boss()

    # Handle view switching with URL params or default to current week/day
    view_week = st.query_params.get("week", st.session_state.current_week)
    view_day = st.query_params.get("day", st.session_state.current_day)
    
    try:
        view_week = int(view_week)
        view_day = int(view_day)
    except (ValueError, TypeError):
        view_week = st.session_state.current_week
        view_day = st.session_state.current_day
    
    active_view = st.radio(
        "View:",
        options=["full", "month", "week", "today"],
        format_func=lambda x: {"full":"🗺 Full",
                               "month":"📅 Month",
                               "week":"📖 Week",
                               "today":"✅ Today"}[x],
        horizontal=True,
        index=["full", "month", "week", "today"].index(
            st.session_state.active_view),
        key="view_radio"
    )

    if active_view != st.session_state.active_view:
        st.session_state.active_view = active_view
        st.rerun()

    # -------- FULL VIEW (previous roadmap) --------
    if st.session_state.active_view == "full":
        st.query_params["week"] = st.session_state.current_week
        st.query_params["day"] = st.session_state.current_day

        for m in range(1, 4):
            st.subheader(f"Month {m}")
            st.markdown(f"**{st.session_state.months.get(f'Month_{m}', 'No action')}**")
            week_cols = st.columns(4)
            for j in range(4):
                wk_num   = (m - 1) * 4 + j + 1
                week_txt = st.session_state.weeks.get(f"Week_{wk_num}", "No milestone")
                green    = "🟢" if wk_num == st.session_state.current_week else ""
                label    = f"{green} Week {wk_num}: {week_txt}"
                key      = f"wk_btn_{wk_num}"

                # Clicking ➜ set query params, switch to Week tab
                if week_cols[j].button(label, key=key):
                    st.query_params["week"] = wk_num
                    st.query_params["day"] = 1
                    st.session_state.active_view = "week"
                    st.rerun()

    elif st.session_state.active_view == "month":
        wk_active   = int(st.session_state.current_week)
        month_index = (wk_active - 1) // 4 + 1
        st.header(f"Month {month_index}")
        st.markdown(f"### {st.session_state.months.get(f'Month_{month_index}', 'No action')}")
        col_m = st.columns(4)
        for idx in range(4):
            wk_num = (month_index - 1) * 4 + idx + 1
            with col_m[idx]:
                render_week_block(wk_num, mode="month")

    # -------- WEEK VIEW --------
    elif st.session_state.active_view == "week":
        render_week_block(view_week, mode="week")

    # -------- TODAY VIEW --------
    elif st.session_state.active_view == "today":
        render_day_block(view_week, int(view_day))

    with st.expander("Show Raw AI Response and lists"):
        st.text(st.session_state.raw_text)
        st.text(st.session_state.weeks)
        st.text(st.session_state.months)

    render_footer()

def render_login_page():
    st.title("The 90-Day Goal Engineer")
    st.image("image1.png", width=800)
    st.markdown("**☝️ save this page so you don't have to re-login**")

    if "access_token" in st.query_params and "refresh_token" in st.query_params and "username" not in st.session_state:
        at = st.query_params["access_token"]
        rt = st.query_params["refresh_token"]

        try:
            supabase.auth.set_session(at, rt)
            user = supabase.auth.get_user()
            if user and user.user.email:
                st.session_state.username = user.user.email
                has_plan = load_plan(st.session_state.username)
                if has_plan:
                    st.success("plan loaded")
                    st.session_state.page = "roadmap"
                else:
                    st.session_state.page = "input"
                st.rerun()
        except Exception as e:
            st.warning(f"Session restore failed: {e}")

    st.markdown('## Sign Up / Login (Very easy)')
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Continue"):
        if username and password:
            ok, message = signup_or_login(username, password)
            st.info(message)
            if ok:
                has_plan = load_plan(username)
                if has_plan:
                    st.success("plan loaded")
                    st.session_state.page = "roadmap"
                else:
                    st.session_state.page = "input"
                st.rerun()
        else:
            st.warning("please put in a username and password")

def sign_out():
    st.session_state.clear()
    st.query_params.clear()  # clears token from browser URL
    st.session_state.page = "login"
    time.sleep(2)
    st.rerun()

#Initialization


# Initialize session_state keys (if missing)
if 'page' not in st.session_state:
    st.session_state.page = 'login'

if 'super_goal' not in st.session_state:
    st.session_state.super_goal = ""
if 'super_goal_input' not in st.session_state:
    st.session_state.super_goal_input = ""
if 'profile_input' not in st.session_state:
    st.session_state.profile_input = None
if 'profile' not in st.session_state:
    st.session_state.profile = None

if 'raw_text' not in st.session_state:
    st.session_state.raw_text = ""
#months and weeks are dictionaries
if 'months' not in st.session_state:
    st.session_state.months = {}
if 'weeks' not in st.session_state:
    st.session_state.weeks = {}
if 'all_weeks' not in st.session_state:
    st.session_state.all_weeks = {}

if "active_view" not in st.session_state:
    st.session_state.active_view = "full" 
if 'selected_milestone' not in st.session_state:
    st.session_state.selected_milestone = None
if 'milestone_notes' not in st.session_state:
    st.session_state.milestone_notes = {}
if 'milestone_progress' not in st.session_state:
    st.session_state.milestone_progress = {}


if 'current_day' not in st.session_state:
    st.session_state.current_day = 1
if 'current_week' not in st.session_state:
    st.session_state.current_week = 1
if 'start_date' not in st.session_state:
    st.session_state.start_date = None



# 4) Improved page‐state logic

page = st.session_state.page

if page == 'input':
    render_input_page()
elif page == 'login':
    render_login_page()
elif page == 'roadmap':
    render_dashboard()
#I can basically cancel the milestone page system for the tab switch version
elif page == 'milestone':
    render_milestone_page()
else:
    st.error("Unknown page state!")
    st.session_state.page = 'login'