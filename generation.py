#This is generation.py

import streamlit as st
import openai
import os

import re
import feedparser
import time

openai.api_key = st.secrets.get("OPENAI_API_KEY")
model = "gpt-4o"

# 1) Generate a 90-day plan via GPT
def plan(goal, profile=None, structure=None):

    prompt = test_prompt(goal, profile, structure)
    st.markdown(prompt, unsafe_allow_html=True)
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are built to break down large and ambitious goals into distinct steps using the exact 90-day framework given by the user prompt."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
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

# 3) Build the GPT prompt
def test_prompt(test_goal, test_profile, test_structure=""):
    return f"""
        Read my 90-day 'Super Goal' and reverse-engineer a plan with **distinct steps**

        {test_goal}
        {test_profile}

        Required Final Output:
        *Generate 3 Monthly Actions. Format the output ONLY as follows, with each action on a new line*

        Month 1 Action: Action text for Month 1...
        Month 2 Action: Action text for Month 2...
        Month 3 Action: Action text for Month 3...

        *Then, Generate 12 Weekly Milestones (4 for each Month in order). Format the output ONLY as follows, with each milestone on a new line*

        Week 1 Milestone: Milestone text for Week 1...
        Week 2 Milestone: Milestone text for Week 2...
        Week 3 Milestone: Milestone text for Week 3...
        Week 4 Milestone: Milestone text for Week 4...

        Week 5 Milestone: Milestone text for Week 5...
        Week 6 Milestone: Milestone text for Week 6...
        Week 7 Milestone: Milestone text for Week 7...
        Week 8 Milestone: Milestone text for Week 8...

        Week 9 Milestone: Milestone text for Week 9...
        Week 10 Milestone: Milestone text for Week 10...
        Week 11 Milestone: Milestone text for Week 11...
        Week 12 Milestone: Milestone text for Week 12...

        Output Guidelines:
        * Monthly actions must be concise with 4 to 7 keywords.
        {test_structure}
        * Week milestones break down the 3 Monthly actions and flow logically:
            - Weeks 1 to 4 support Month 1 Action
            - Weeks 5 to 8 support Month 2 Action
            - Weeks 9 to 12 support Month 3 Action
        * Specific Instructions for generating weekly milestones under each Month group:
            - Each milestone must be achievable within one week and be distinct from other milestones
            - Each weekly milestone must be hyperspecific and target the exact action with the concise context (location, platform, tool, or people)
            - Choose two weeks to be quantitative, almost like programming a robot.
            - Choose two weeks to be boldly prescriptive and uncomfortably specific to break the ice for me
            - After writing down each milestone, ensure it follows the specificity standards
            - Never use generalities like “define target audience.” Instead, use statements like \"Turn X poll into 10-pro interview\"
        * The bottom line is to follow each item listed in the Required Output with zero tolerance for off-topic discussions.
        """

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
        response = openai.chat.completions.create(
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
        response = openai.chat.completions.create(
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

test_structure_dictionary = {
    "Planning → Execution → Iterate": """* Specific montly structure:
        - Month 1: Planning and trial
        - Month 2: Brutaland specific execution
        - Month 3: Evaluate and iterate on better parts of work""",
    "Specific Action + Reflect ×3": """* Specific montly structure:
        - Month 1: (Ditch all planning-based language): Weirdly hyperspecific action first three weeks and a clear reflection for last week to specific to that weird action
        - Month 2: Different hyperspecific action with the same exact shocking pattern (action -> toppling reflection)
        - Month 3: Another interesting hyperspecific action with the same exact shocking pattern (action -> toppling reflection)""",
    "Explore → Exploit → Expand": """* Specific montly structure:
        - Month 1: Unique and structured exploration of super goal (specific methods, objectives, audience)
        - Month 2: Highly leverage intial knowledge and resources to take specific actions
        - Month 3: Expand from these actions for better apporahc, then final narrowing executions on last 2 weeks""",
    "Crack Mode": """* Crack mode on. For each month, Generate HYPERSPECIFIC targets like an emotionless bloodbath machine
        - Month 1: Slice open a target so hard it seems impossible.
        - Month 2: Assume I've gotten ahead, now it's all a brutal numbers game
        - Month 3: Blow my goals away with hyperscaled completion, metrics, and outreach
        * Week milestones must have same brutal concision, don't worry about intepretation (if numbers and periods are there)"""
}

# --- NEW: banner generatorNOT CURRENTLY BEING USED
def generate_banner(super_goal: str, reference_ids):
    """
    One‑shot 800×300 banner that visually matches the user's super goal.
    Saves nothing – just returns raw PNG bytes.
    reference_ids = image IDs of local reference files already in /static
    """
    prompt = f"""
    Please help me design a landscape dashboard banner for this super goal: {super_goal}

    If the original super goal text is has more than 12 words or has complex wording:
    - shorten the title by removing excessive details
    - keep the keywords and key numbers (eg. subscriber target)
    - focus on practical action verbs (eg. reach, learn, make) ignore common english sentence structure

    The optimized super goal title is placed in the top-left overlay in a clean, bold title font.

    The main element of the banner is the cartoon:
    - The theme of the goal should be illustrated with a primary subject
    - The story telling is complete through lighthearted and humurous states and actions
    - ONLY if suitable, humour can be convyed with exaggerated body proportions, especially through contrast with multiple characters

    Specific artistic choice for the cartoon: 
    - Simple and bold look for characters, settings, and props
    - No background wash
    - Preferably consistent line style: Thick, black outlines with rounded ends; no sketchy or variable stroke.
    - Selective colour. Keep most lines black on white; use 1‑2 accent colours only for goal‑defining items (eg. youtube plaque, computer)
    - The stylization, palette, and detailing can imitate the reference images provided
    """

    st.markdown(prompt, unsafe_allow_html = True)

    # Convert local reference files to byte‑buffers OpenAI will accept
    refs = [{"image": open(p, "rb").read()} for p in reference_ids] if reference_ids else None

    rsp = openai.images.generate(
        model = "gpt-image-1",
        prompt       = prompt,
        size         = "1536x1024",
        n            = 1         # must use OpenAI ≥ v1.30
    )
    return base64.b64decode(rsp.data[0].b64_json)

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