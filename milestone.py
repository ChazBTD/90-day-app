import streamlit as st
from generation import generate_steps_better, regenerate_milestone
from supabasecode import save_plan

def update_progress(week_key):
    week_days = st.session_state.all_weeks.get(week_key, [None] *7)

    all_tasks = []
    for day in week_days:
        if day is not None:
            all_tasks.extend(day)
    total_tasks = len(all_tasks)
    if total_tasks > 0:
        completed_count = sum(1 for (txt, done) in all_tasks if done)
        percentage = int(completed_count / total_tasks * 100)
    else:
        percentage = 0

    st.session_state.milestone_progress[week_key] = percentage

# Render the weekly milestone page, buts kinda old
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
    if col1.button("Make Harder 💪", key="make_harder"):
        with st.spinner("Regenerating milestone..."):
            new_milestone = regenerate_milestone(week_num, milestone['text'], "harder", st.session_state.super_goal)
            if new_milestone:
                st.session_state.temp_new_milestone = new_milestone
                st.session_state.show_milestone_preview = True
                st.rerun()

    if col2.button("Make Easier 🎯", key="make_easier"):
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

#this is the main one being used with tab logic
def render_week_block(week_num: int, mode: str = "month"):
    week_key = f"Week_{week_num}"
    milestone_text  = st.session_state.weeks.get(f"Week {week_num}", "No milestone found")

    # ---------- Header ----------
    week_is_active  = (week_num == st.session_state.current_week)
    if week_is_active:
        if mode == "month":
            header = f":large_green_circle: **Week {week_num}**"
        elif mode == "week":
            header = f"### :large_green_circle: Week {week_num}"
    else:
        if mode == "month":
            header = f"**Week {week_num}**"
        elif mode == "week":
            header = f"### Week {week_num}"

    st.markdown(header)
    st.write(milestone_text)

    # ---------- Progress bar ----------
    update_progress(week_key)
    progress_percent = st.session_state.milestone_progress.get(week_key, 0)
    st.progress(progress_percent)

    # ---------- Day list ----------
    week_days = st.session_state.all_weeks.get(week_key, [None] * 7)

    for day_index, day_entry in enumerate(week_days, start=1):
        # Month-mode  → terse caption
        # Week-mode   → each day in a bordered container
        if mode == "week":
            with st.container(border=True):
                # Green circle for the current day when in week view
                current_day_is_active = week_is_active and (day_index == st.session_state.current_day)
                if current_day_is_active:
                    day_prefix = ":large_green_circle: "
                else:
                    day_prefix = ""

                if day_entry:
                    tasks_completed = sum(1 for _, done in day_entry if done)
                    tasks_total     = len(day_entry)
                    st.markdown(f"{day_prefix}**Day {day_index}** — {tasks_completed}/{tasks_total} done")
                else:
                    st.markdown(f"{day_prefix}**Day {day_index}** — ⟡ not generated")

        elif mode == "month":
            if week_is_active:          # ← active week
                if day_entry:                                      # tasks already generated
                    # more traditional counting, easier to read
                    total     = len(day_entry)
                    completed = 0
                    for _text, done in day_entry:
                        if done:
                            completed += 1
                    st.caption(f"Day {day_index} — {completed}/{total} done")
                else:                                              # not generated yet
                    st.caption(f"Day {day_index} — ⟡ not generated")

    # ---------- Extra controls (only in week mode) ----------
    if mode == "week":
        # ── Difficulty tweaker (shown only in Week view) ─────────────────────────
        btn_hard, btn_easy, btn_rev = st.columns([1, 1, 9])

        # helper
        def _swap(difficulty: str):
            old = milestone_text
            new = regenerate_milestone(week_num, old, difficulty, st.session_state.super_goal)
            if new:
                st.session_state[f"old_milestone_week_{week_num}"] = old
                st.session_state.weeks[f"Week {week_num}"] = new
                save_plan(st.session_state.username)
                st.rerun()

        if btn_hard.button("Make Harder 💪", key=f"wk{week_num}_harder"):
            with st.spinner("Regenerating…"):
                _swap("harder")

        if btn_easy.button("Make Easier 🎯", key=f"wk{week_num}_easier"):
            with st.spinner("Regenerating…"):
                _swap("easier")

        # show Revert only when we have something to roll back to
        old_key = f"old_milestone_week_{week_num}"
        if old_key in st.session_state:
            if btn_rev.button("Revert ⤺", key=f"wk{week_num}_revert"):
                st.session_state.weeks[f"Week {week_num}"] = st.session_state.pop(old_key)
                save_plan(st.session_state.username)
                st.rerun()

        if st.button("Generate all 7 days", key=f"generate_all_{week_key}"):
            for day_num in range(1, 8):
                if week_days[day_num - 1] is None:
                    tasks = generate_steps_better(
                        week_num,
                        milestone_text,
                        day_num,
                        st.session_state.super_goal,
                        week_days,
                    )
                    if tasks:
                        week_days[day_num - 1] = [
                            [tasks["step_1"], False],
                            [tasks["step_2"], False],
                        ]
            st.session_state.all_weeks[week_key] = week_days
            save_plan(st.session_state.username)
            st.rerun()
        if st.button("Clear this week", key=f"reset_{week_key}"):
            st.session_state.all_weeks[week_key] = [None] * 7
            save_plan(st.session_state.username)
            st.rerun()

        # Notes area
        notes_key     = f"notes_{week_num}"
        saved_notes   = st.session_state.milestone_notes.get(week_key, "")
        updated_notes = st.text_area("Week notes", value=saved_notes, key=notes_key, height=120)
        st.session_state.milestone_notes[week_key] = updated_notes

def render_day_block(week_num: int, day_num: int):
    """Single-day view — identical behaviour to the original milestone page UI."""
    wk_key = f"Week_{week_num}"
    wk_days = st.session_state.all_weeks.setdefault(wk_key, [None]*7)
    idx = day_num - 1
    milestone = st.session_state.weeks.get(f"Week {week_num}", "No milestone")

    st.subheader(f"Week {week_num} → Day {day_num}")
    if wk_days[idx] is None:
        if st.button(f"Generate actions for Day {day_num}"):
            tasks = generate_steps_better(
                week_num, milestone, day_num,
                st.session_state.super_goal, wk_days
            )
            if tasks:
                wk_days[idx] = [[tasks["step_1"], False],
                                [tasks["step_2"], False]]
                save_plan(st.session_state.username)
                st.rerun()
    else: #If tasks exsist, editing and VIEW mode
        edit_key = f"editing_{wk_key}_{day_num}"
        st.session_state.setdefault(edit_key, False)
        tasks_today = wk_days[idx]

        # EDIT MODE
        if st.session_state[edit_key]:
            new_texts = []
            for i, (txt, _) in enumerate(tasks_today):
                new_texts.append(
                    st.text_area(f"Task {i+1}", value=txt, height=80,
                                 key=f"{wk_key}_d{day_num}_txt{i}")
                )
            if st.button("Apply Changes ✅", key=f"apply_{wk_key}_{day_num}"):
                for i, nt in enumerate(new_texts):
                    tasks_today[i][0] = nt
                    tasks_today[i][1] = False          # reset checkbox
                st.session_state[edit_key] = False
                save_plan(st.session_state.username)
                st.rerun()

        # READ-ONLY MODE
        else:
            for i, (txt, done) in enumerate(tasks_today):
                checked = st.checkbox(txt, value=done,
                                      key=f"{wk_key}_d{day_num}_{i}")
                if checked != done:
                    tasks_today[i][1] = checked
                    save_plan(st.session_state.username)
                    st.rerun()

            if st.button("Edit tasks ✏️", key=f"edit_{wk_key}_{day_num}"):
                st.session_state[edit_key] = True
                st.rerun()
