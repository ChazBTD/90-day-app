import streamlit as st
import math
import time

#this has to come before st.cache and other stuff is initiated
st.set_page_config(page_title="90-Day Goal Engineer", layout="wide", initial_sidebar_state="collapsed")


from generation import plan, parse, inline_text_input, render_footer, test_structure_dictionary
from milestone import render_milestone_page, update_progress
from milestone import render_day_block, render_week_block  
from supabasecode import signup_or_login, load_plan, save_plan, save_local_creds, load_local_creds, clear_local_creds

# Navigate to a specific week’s milestone page
def show_milestone_page(week_num, milestone_text):
    st.session_state.page = 'milestone'
    st.session_state.selected_milestone = {
        'number': week_num,
        'text': milestone_text
    }

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
                raw_text = plan(st.session_state.super_goal, st.session_state.profile, month_structure)
                if raw_text:
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

# 2) Render the “roadmap” page with clickable weeks
def render_roadmap_page():
    st.title("🎯 90-Day Goal Engineer")
    if st.button("Create New Plan", key="new_plan_button"):
        st.success("new plan started")
        time.sleep(2)
        st.session_state.page = 'input'
        st.rerun()
    if st.button("Sign Out Completely", key="roadmap_sign_out_button"):
        sign_out()
    st.image("image1.png", caption="Roadmap reference", width=1000)
    st.markdown("---")
    st.header("Your 90-Day Road")

    cols = st.columns(3)
    for i in range(1, 4):
        col = cols[i - 1]
        col.subheader(f"Month {i}")
        month_action = st.session_state.months.get(f"Month {i}", "No Action")
        if len(month_action) <= 35:
            col.markdown(f"## {month_action}<br>", unsafe_allow_html=True)
        else:
            col.markdown(f"## {month_action}")

        for j in range(1, 5):
            week_num = (i - 1) * 4 + j
            week_container = col.container(border=True)

            if week_num == int(st.session_state.current_week):
                week_container.markdown(f"**:large_green_circle: Week {week_num}**")
            else:
                week_container.markdown(f"**Week {week_num}**")

            #the week milestone text
            week_action = st.session_state.weeks.get(f"Week {week_num}", "No milestone here")

            week_container.button(
                week_action,
                key=f"week_{week_num}_button",
                on_click=show_milestone_page,
                args=(week_num, week_action)
            )

            # Show a progress message under each week, if applicable
            week_key = f"Week_{week_num}"
            if week_key in st.session_state.milestone_progress:
                progress = st.session_state.milestone_progress[week_key]
                progress_messages = [
                    (20, "Starting up 👏"),
                    (50, "Keep going 🤜"),
                    (70, "Getting there 🥊"),
                    (99, "Last push 🚀"),
                    (100, "Complete ✅")
                ]
                for threshold, message in progress_messages:
                    if progress <= threshold:
                        week_container.markdown(f"Current progress: {message}")
                        break

    if st.session_state.raw_text:
        with st.expander("Show Raw AI Response and lists"):
            st.text(st.session_state.raw_text)
            st.text(st.session_state.weeks)
            st.text(st.session_state.months)

# This comes before the roadmap at all times
def show_progress_boss():
    week_num = st.session_state.current_week
    day_num = st.session_state.current_day
    week_key = f"Week_{week_num}"

    #BOSS state based on completed/total tasks made PROGRESS
    st.markdown(f"## Your boss for Week {week_num} Day {day_num}")
    update_progress(week_key)
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
        st.success("new plan started")
        time.sleep(2)
        st.session_state.page = 'input'
        st.rerun()
    if st.button("Sign Out Completely", key="roadmap_sign_out_button"):
        sign_out() 

    #Top-level page with tabs: Full ▸ Month ▸ Week ▸ Today"""
    # ── controls always visible ───────────────────────────
    cols = st.columns(2)
    with cols[0]:
        st.session_state.current_week = st.number_input(
            "Current week", 1, 12, int(st.session_state.current_week),
            key="current_week_dash"
        )
    with cols[1]:
        st.session_state.current_day = st.number_input(
            "Current day", 1, 7, int(st.session_state.current_day),
            key="current_day_dash"
        )

    #NOT show if day view using psuedocode selection
    show_progress_boss()

    # ── choose view ───────────────────────────────────────
    tab_full, tab_month, tab_week, tab_today = st.tabs(
        ["🗺 Full", "📅 Month", "📖 Week", "✅ Today"]
    )

    # -------- FULL VIEW (previous roadmap) --------
    with tab_full:
        for m in range(1, 4):
            st.subheader(f"Month {m}")
            st.markdown(f"**{st.session_state.months.get(f'Month {m}', 'No action')}**")
            week_cols = st.columns(4)
            for j in range(4):
                wk = (m - 1) * 4 + j + 1
                active = wk == st.session_state.current_week
                week_action = st.session_state.weeks.get(f"Week {wk}", "No milestone here")
                if active:
                    label = (f":large_green_circle: Week {wk}: " + week_action)
                else:
                    label = (f"Week {wk}: " + week_action)
                key = f"wk{wk}_btn"
                if week_cols[j].button(label, key=key, disabled=not active):
                    st.session_state.current_week = wk
                    st.session_state.page = "roadmap"        # stay in dashboard
                    st.session_state.current_day = 1
                    st.rerun()

    with st.expander("Show Raw AI Response and lists"):
        st.text(st.session_state.raw_text)
        st.text(st.session_state.weeks)
        st.text(st.session_state.months)

    # -------- MONTH VIEW --------
    with tab_month:
        wk = int(st.session_state.current_week)
        active_month = math.ceil(wk / 4)
        st.header(f"Month {active_month}")
        st.markdown(f"### {st.session_state.months.get(f'Month {active_month}', 'No action')}")

        col_m = st.columns(4)
        for idx in range(4):
            wk_num = (active_month - 1) * 4 + idx + 1
            with col_m[idx]:
                render_week_block(wk_num, mode = "month")

    # -------- WEEK VIEW --------
    with tab_week:
        wk = int(st.session_state.current_week)
        render_week_block(wk, mode="week")

    # -------- TODAY VIEW --------
    with tab_today:
        wk = int(st.session_state.current_week)
        day = int(st.session_state.current_day)
        render_day_block(wk, day)

def render_login_page():
    st.title("The 90-Day Goal Engineer")
    st.image("image1.png", caption="You in a week easily", width=800)

    cached_user, cached_password = load_local_creds()
    if cached_user and cached_password:
        ok, _ = signup_or_login(cached_user, cached_password)   # validates password
        if ok:
            st.session_state.username = cached_user
            has_plan = load_plan(cached_user)
            if has_plan:
                st.session_state.page = "roadmap"
            else:
                st.session_state.page = "input"
            st.rerun()
            return  # stop here
        pass

    st.markdown('## Sign Up / Login (Very easy)')
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Continue"):
        if username and password:
            ok, message = signup_or_login(username, password)
            st.info(message)
            if ok:
                save_local_creds(username, password)
                st.session_state.username = username
                time.sleep(2)
                # load plan → decide destination
                has_plan = load_plan(username)
                if has_plan:
                    st.session_state.page = "roadmap"
                else:
                    st.session_state.page = "input"
                st.rerun()
        else:
            st.warning("please put in a username and password")

def sign_out():
    clear_local_creds()
    st.session_state.clear()
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
    st.session_state.profile_input = ""
if 'profile' not in st.session_state:
    st.session_state.profile = ""

if 'raw_text' not in st.session_state:
    st.session_state.raw_text = ""
#months and weeks are dictionaries
if 'months' not in st.session_state:
    st.session_state.months = {}
if 'weeks' not in st.session_state:
    st.session_state.weeks = {}

if 'selected_milestone' not in st.session_state:
    st.session_state.selected_milestone = None
if 'milestone_notes' not in st.session_state:
    st.session_state.milestone_notes = {}
if 'milestone_progress' not in st.session_state:
    st.session_state.milestone_progress = {}

if 'all_weeks' not in st.session_state:
    st.session_state.all_weeks = {}
if 'current_day' not in st.session_state:
    st.session_state.current_day = 1
if 'current_week' not in st.session_state:
    st.session_state.current_week = 1


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