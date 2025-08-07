base_prompt = f"""
    Please help me design a 1536:512 landscape dashboard banner for this super goal: {super_goal}
    If the original super goal text is has more than 12 words or has complex wording:
    - adapt to to a banner title by removing excessive details
    - keep the keywords and a key number
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
    """
    
edit_prompt = f"""
    Focus on first landscape banner for my super goal: {super_goal}
    - Ensure it's size is 1536:512
    - Ensure alignment between the banner and the theme of the goal
    - Tweak the style of the banner to align more with the two reference images provided: NAMELY the character style, contrasting and humurous details, and detailing
    - Make sure the palette remains simpel and only serves as an accent for goal-defining details
    """

#This was to generate the daily steps in generation.py
def generate_daily_steps(week_num, current_milestone, current_day, super_goal):
    prompt = f"""
    Week {week_num} Milestone: {current_milestone}
    Super Goal Context: {super_goal}
    
    Generate exactly 2 actionable daily steps for Day {current_day} for completing this weekly milestone.
    
    Requirements:
    - Daily step must be specific enough with 7-10 words
    - Steps must focus on actually getting what the milestone says done
    - Each step should take 40-60 minutes to complete
    - No generic advice, instead be concrete and specific
    
    Format your response as:
    Day {current_day} Step 1: [action step]
    Day {current_day} Step 2: [action step]
    """
    st.markdown(prompt, unsafe_allow_html = True)

    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert at making specific daily actions from a singular weekly goal."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        daily_steps_text = response.choices[0].message.content.strip()
        steps = {}
        step_1_match = re.search(r"Day 1 Step 1:(.*?)(?=Day 1 Step 2|$)", daily_steps_text, re.DOTALL)
        step_2_match = re.search(r"Day 1 Step 2:(.*?)$", daily_steps_text, re.DOTALL)
        if step_1_match:
            steps["step_1"] = step_1_match.group(1).strip()
        if step_2_match:
            steps["step_2"] = step_2_match.group(1).strip()
        return steps
    except Exception as e:
        st.error(f"Error generating daily steps: {e}")
        return None

# 2) Render the “roadmap” page with clickable weeks inside roadmap.py this is OBSELETE
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
    with st.expander("Forgot what your goal was?"):
        st.text(st.session_state.super_goal)
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
                week_container.markdown(f"**🟢 Week {week_num}**")
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

# Render the weekly milestone page in milestone.py, buts kinda old
def render_milestone_page():
    milestone = st.session_state.selected_milestone
    week_num = milestone['number']

    #used for indexing actions and etc
    week_key = f"Week_{week_num}"

    if st.button("← Back to Roadmap"):
        st.session_state.page = 'roadmap'
        st.rerun()

    st.title(f"Week {week_num} Milestone")
    st.markdown(f"### {milestone['text']}")
    st.markdown("#### Adjust Milestone Difficulty")

    col1, col2, col3 = st.columns([1, 1, 7])
    if col1.button("Harder Milestone 💪", key="make_harder"):
        with st.spinner("Regenerating milestone..."):
            new_milestone = regenerate_milestone(week_num, milestone['text'], "harder", st.session_state.super_goal)
            if new_milestone:
                st.session_state.temp_new_milestone = new_milestone
                st.session_state.show_milestone_preview = True
                st.rerun()

    if col2.button("Easier Milestone 🎯", key="make_easier"):
        with st.spinner("Regenerating milestone..."):
            new_milestone = regenerate_milestone(week_num, milestone['text'], "easier", st.session_state.super_goal)
            if new_milestone:
                st.session_state.temp_new_milestone = new_milestone
                st.session_state.show_milestone_preview = True
                st.rerun()

    # Preview the newly generated milestone (if any)
    if st.session_state.get('show_milestone_preview', False):
        st.markdown("#### Preview New Milestone:")
        st.info(f"**You want it?:** {st.session_state.temp_new_milestone}")

        apply_col, cancel_col, _ = st.columns([1, 1, 5])
        if apply_col.button("Apply Changes ✅", type="primary"):
            st.session_state.weeks[f"Week {week_num}"] = st.session_state.temp_new_milestone
            st.session_state.selected_milestone['text'] = st.session_state.temp_new_milestone
            st.session_state.show_milestone_preview = False
            del st.session_state.temp_new_milestone
            save_plan(st.session_state.username)
            st.success("Milestone updated successfully!")
            st.rerun()

        if cancel_col.button("Cancel Changes ❌"):
            st.session_state.show_milestone_preview = False
            del st.session_state.temp_new_milestone
            st.rerun()

    st.markdown("---")
    st.markdown("### Action Steps")

    st.session_state.current_day = st.number_input(
        "Set Day (1–7)",
        min_value=1,
        max_value=7,
        value=1,
        key="day_input"
    )

    ### Fixed Daily‐Task Generation & Progress Code (updated)
    # This replaces the previous block inside render_milestone_page().

    # 1) Pre‐allocate exactly 7 day slots for each week
    if week_key not in st.session_state.all_weeks:
        st.session_state.all_weeks[week_key] = [None] * 7

    week_days = st.session_state.all_weeks[week_key]
    #List of das 1 to 7
    current_day = int(st.session_state.current_day)
    current_index = current_day - 1

    # 2) If this day has not been generated yet (slot is None), show Generate button
    if week_days[current_index] is None:
        if st.button(f"Generate Day {current_day} Steps 🚀", key=f"gen_day_{current_day}"):
            with st.spinner(f"Generating daily steps for Day {current_day}..."):
                tasks = generate_steps_better(
                    week_num,
                    milestone['text'],
                    current_day,
                    st.session_state.super_goal,
                    week_days
                )
                if tasks:
                    day_list = [[tasks["step_1"], False], [tasks["step_2"], False]]
                    week_days[current_index] = day_list
                    #replace empty list with new tasks set to incomplete
                    save_plan(st.session_state.username)
                    st.rerun()

    # 3) If this day exists (not None), render its tasks
    elif week_days[current_index] is not None:
        today_tasks = week_days[current_index]
        st.markdown(f"**Day {current_day} Tasks:**")

        # Unique key to track edit‐mode for this specific day
        editing_key = f"editing_{week_key}_{current_index}"
        if editing_key not in st.session_state:
            st.session_state[editing_key] = False

        # a) EDIT MODE: show text_areas + checkboxes + "Apply Changes" button
        if st.session_state[editing_key]:
            updated_texts = []
            for idx, (text, done_flag) in enumerate(today_tasks):
                new_val = st.text_area(
                    f"Task {idx+1}:",
                    value=text,
                    height=80,
                    key=f"{week_key}_day{current_index}_text{idx}"
                )
                updated_texts.append(new_val)

            if st.button("Apply Changes", key=f"apply_{week_key}_{current_day}"):
                for idx, new_txt in enumerate(updated_texts):
                    today_tasks[idx][0] = new_txt
                    today_tasks[idx][1] = False
                st.session_state[editing_key] = False

                save_plan(st.session_state.username)

        # b) READ‐ONLY MODE: show plain text + checkboxes + "Edit Tasks" button
        else:
            with st.container(border = True):
                for idx, (text, done_flag) in enumerate(today_tasks):
                    widget_key = f"{week_key}_day{current_day}_task{idx}"
                    checked = st.checkbox(text, value=done_flag, key=widget_key)
                    if checked != done_flag:
                        today_tasks[idx][1] = checked
                        save_plan(st.session_state.username)
                        st.rerun()

                if st.button(f"Edit Tasks for Day {current_day}", key=f"edit_{week_key}_{current_day}"):
                    st.session_state[editing_key] = True
                    st.rerun()

    update_progress(week_key)
    percentage = st.session_state.milestone_progress[week_key]
    st.markdown(f"**Progress: {percentage}%**")
    st.progress(percentage)

    # 5) Button to regenerate (wipe) all 7 days for this week
    if st.button("🔄 Regenerate All Days", key=f"reset_{week_key}"):
        st.session_state.all_weeks[week_key] = [None] * 7
        st.rerun()


    # Notes section
    saved_notes = st.session_state.milestone_notes.get(week_key, "")
    notes_key = f"notes_{week_num}"
    st.text_area(
        "Notes:",
        value=saved_notes,
        height=150,
        key=notes_key,
        placeholder="Add your notes about this milestone here..."
    )
    if notes_key in st.session_state:
        st.session_state.milestone_notes[week_key] = st.session_state[notes_key]
