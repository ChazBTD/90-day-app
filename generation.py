#This is generation.py

import streamlit as st
from openai import OpenAI
import os

import re
import feedparser
import time

from goodprompt import test_prompt

model = "gpt-4o"
client = OpenAI(api_key="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")

# 1) Generate a 90-day plan via GPT
def plan(goal: str, profile="", structure=""):
    prompt = test_prompt(goal, profile, structure)
    st.markdown(prompt, unsafe_allow_html=True)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are built to break down large and ambitious goals into distinct steps using the exact 90-day framework given by the user prompt."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            )
        plan_text = response.choices[0].message.content.strip()
        return plan_text
    except openai.AuthenticationError:
        st.error("Server Authentication Error. Check your API key configuration.", icon="🚨")
        return None
    except openai.RateLimitError:
        st.error("SERVER Rate Limit Exceeded. Please wait and try again or check your plan.")
        return None
    except Exception as e:
        st.error(f"An error occurred interacting with OpenAI: {e}", icon="🔥")
        return None

# 2) Parse raw text into 3 monthly actions + 12 weekly milestones
def parse(text):
    result = {"month_list": {}, "week_list": {}}
    if not text:
        return result

    # Extract monthly actions
    for i in range(1, 4):
        match = re.search(rf"Month {i} Action:(.*?)(?=Month \d|Week \d|$)", text, re.IGNORECASE | re.DOTALL)
        if match:
            result["month_list"][f"Month_{i}"] = match.group(1).strip()

    # Extract weekly milestones
    for i in range(1, 13):
        match = re.search(rf"Week {i} Milestone:(.*?)(?=Week \d|Month \d|$)", text, re.IGNORECASE | re.DOTALL)
        if match:
            result["week_list"][f"Week_{i}"] = match.group(1).strip()

    return result

# 4) Regenerate a weekly milestone with altered difficulty
def regenerate_milestone(week_num, current_milestone, difficulty_change, super_goal):
    difficulty_instruction = {
        "harder": "Make this milestone more specifically challenging and ambitious. If there are numbers, quantatively greater as well",
        "easier": "Make this milestone more achievable and less overwhelming. give it to me with simpler wording as well."
    }
    prompt = f"""
    Please make a difficulty modification for the Week {week_num} milestone in my 90-day super goal plan.
    The current Week {week_num} milestone is: {current_milestone}
    For context higher level, my original super goal is: {super_goal}

    Please {difficulty_instruction[difficulty_change]}
    Infer as much as you can from the given context to make this modification meaningful.
    HOWEVER, the final output should be similar length as original
    
    Final Output Format, no exceptions:
    Week {week_num} Milestone: [New milestone text]
    """

    st.markdown(prompt, unsafe_allow_html = True)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert at making specific, and actionable weekly milestones by focusing down from larger plans."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        new_milestone = response.choices[0].message.content.strip()
        match = re.search(rf"Week {week_num} Milestone:(.*)", new_milestone, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        else:
            return new_milestone + " (Not clean)"
    except Exception as e:
        st.error(f"Error regenerating milestone: {e}")
        return None

#the real one for generating daily steps
def generate_steps_better(week_num, current_milestone, current_day, super_goal, week_days = list[list]):
    """
    week_days: list of days for this week, where each day is the list: [[task text, bool], [task text 2, bool]]
    """

    # 1) Build a summary of previous days’ tasks (and indicate catchup needed if not)
    catch_up = ""
    prev_context = ""

    if current_day > 1 and len(week_days) > 0:
        lines = []
        max_index = min(current_day - 1, len(week_days))
        for day_idx in range(max_index):
            tasks = week_days[day_idx]

            if not tasks:
                lines.append(f"- I missed Day {day_idx + 1}")
                catch_up = "Note: Help me consider catchup based on the number of days I missed"
                continue

            #done_texts basically means tasks that were generated
            done_texts = [t_text for (t_text, _) in tasks]
            if done_texts:
                lines.append(f"- Day {day_idx + 1} completed tasks: " + "; ".join(done_texts))

        if lines:
            prev_context = "**Current context:**\n" + "\n".join(lines) + "\n\n"
    
    prompt = f"""
    Week {week_num} Milestone: {current_milestone}
    Super Goal Context: {super_goal}
    {prev_context}
    {catch_up}

    Task: Generate 2 actionable steps for the current Day {current_day}.
    Make sure there are no repeated steps.
    These 2 actions should be based on what has been completed to help me progress logically and linearly towards the weekly milestone.
    If milestone has a defined scope or quantity, do remember to help me achieve this by the end as well.

    Formatting requirements:
    - Daily step must be specific enough with 7-10 words
    - Each step should take 30-60 minutes to complete
    - No generic advice, instead be concrete and specific
    
    Format your response as:
    Day {current_day} Step 1: [action step]
    Day {current_day} Step 2: [action step]
    """

    st.markdown(prompt, unsafe_allow_html=True)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert at making specific daily steps from a singular weekly goal."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        daily_steps_text = response.choices[0].message.content.strip()
        steps = {}

        # Use dynamic regex based on current_day
        # e.g. r"Day 3 Step 1:(.*?)(?=Day 3 Step 2|$)"
        step_1_pattern = rf"Day {current_day} Step 1:(.*?)(?=Day {current_day} Step 2|$)"
        step_2_pattern = rf"Day {current_day} Step 2:(.*?)$"

        step_1_match = re.search(step_1_pattern, daily_steps_text, re.DOTALL)
        step_2_match = re.search(step_2_pattern, daily_steps_text, re.DOTALL)

        if step_1_match:
            steps["step_1"] = step_1_match.group(1).strip()
        if step_2_match:
            steps["step_2"] = step_2_match.group(1).strip()

        return steps

    except Exception as e:
        st.error(f"Error generating daily steps: {e}")
        return None

# 6) Custom inline text input for the input page
def inline_text_input(before_text, after_text, first_column, placeholder, key="input_key"):
    col1, col2, col3 = st.columns([first_column, 9, 4])
    col1.markdown(f"<span style='font-size:1.3rem; font-weight:700;'>{before_text}</span>", unsafe_allow_html=True)
    #HERES what the user puts in
    user_input = col2.text_input(placeholder=placeholder, label=".", label_visibility="collapsed", key=key)
    col3.markdown(f"<span style='font-size:1.3rem; font-weight:700;'>{after_text}</span>", unsafe_allow_html=True)
    return user_input

# Use Streamlit's caching to avoid fetching on every rerun, update every hour (3600 seconds)
@st.cache_data(ttl=3600)
def get_post(feed_url="https://spoonfedacademy.substack.com/feed"):
    """
    Fetches the latest post title from a Substack RSS feed.
    Returns the title string on success, or an error message string on failure.
    """

    try:
        feed = feedparser.parse(feed_url)
        if feed.entries:
            title = feed.entries[0].title
            link = feed.entries[0].link
            return [title, link]
        else:
            return None
            st.error(f"No entries found in substack: {feed_url}") #Debug

    except Exception as e:
        st.error(f"Error with getting substack title:\n {e}")
        return None

def render_footer():
    #error message will output from get_post()
    post = get_post()
    latest_link = post[1]
    latest_title = post[0]

    # HTML render using streamlit markdown
    footer_html = f"""
    <hr style="margin-top:2em; margin-bottom:1em; border:1px solid #eee;">
    <div style="text-align:left; color:#888; font-size:1.2rem; padding-bottom:10px; line-height:2;">
        <!-- Second line -->
        <div>
            <strong>⚠️ Latest:</strong>
            <a href="{latest_link}" style="color:#888; text-decoration:underline;">
                {latest_title}
            </a>
        </div>
        <!-- First line -->
        <div>
            <strong>ℹ️ Contact:</strong>
            <a href="mailto:chazbtd@gmail.com" style="color:#888; text-decoration:underline;">
                my email
            </a>
        </div>
        <!-- Additional Message -->
        <div>
            💀 Made for ©SpoonFedStudy
        </div>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)