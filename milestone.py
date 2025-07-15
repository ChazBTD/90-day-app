#This is milestone.py
import streamlit as st
from generation import generate_steps_better, regenerate_milestone
from supabasecode import save_plan

def update_progress(week_key, show: bool):
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
    
    if show:
        st.progress(st.session_state.milestone_progress.get(week_key, 0))

#this is the main one being used with tab logic
def render_week_block(week_num, mode):
    week_key = f"Week_{week_num}"

    milestone_text  = st.session_state.weeks.get(f"Week_{week_num}", "No milestone found")
    week_is_active  = (week_num == st.session_state.current_week)
    week_days = st.session_state.all_weeks.get(week_key, [None] * 7)

    if mode == "month":
        if week_is_active:
            st.markdown(f"🟢 **Week {week_num}**")
        else:
            st.markdown(f"**Week {week_num}**")

        if st.button(f"{milestone_text}", key=f"month_wk_{week_num}"):
            st.query_params["week"] = week_num
            st.query_params["day"] = 1
            st.session_state.active_view = "week"
            st.rerun()

        update_progress(week_key, True)

        for day_idx, day in enumerate(week_days, start=1):
            if week_is_active:
                if day:
                    done  = sum(1 for _, d in day if d)
                    total = len(day)
                    st.caption(f"Day {day_idx} — {done}/{total} done")
                else:
                    st.caption(f"Day {day_idx} — ⟡ not generated")

    if mode == "week":
        if week_is_active:
            st.markdown(f"#### 🟢 **Week {week_num}**")
        else:
            st.markdown(f"#### Week {week_num}")
        st.write(milestone_text)

        for day_idx, day in enumerate(week_days, start=1):
            if day:
                done  = sum(1 for _, d in day if d)
                total = len(day)
                status = f"{done}/{total} done"
            else:
                status = "⟡ not generated"

            # Green circle on currently-selected day
            is_active_day = (week_is_active and day_idx == st.session_state.current_day)
            prefix = ":large_green_circle: " if is_active_day else ""

            label = f"{prefix}Day {day_idx} — {status}"
            # 👇 add '_week' to guarantee uniqueness across different modes
            key   = f"wk{week_num}_day{day_idx}_week"

            if st.button(label, key=key):
                st.query_params["week"] = week_num
                st.query_params["day"] = day_idx
                st.session_state.active_view = "today"
                st.rerun()

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
                st.session_state.weeks[f"Week_{week_num}"] = new
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
                st.session_state.weeks[f"Week_{week_num}"] = st.session_state.pop(old_key)
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


def render_day_block(week_num, day_num):
    """Single-day view — identical behaviour to the original milestone page UI."""
    wk_key = f"Week_{week_num}"
    wk_days = st.session_state.all_weeks.setdefault(wk_key, [None]*7)
    idx = day_num - 1
    milestone = st.session_state.weeks.get(f"Week_{week_num}", "No milestone")

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