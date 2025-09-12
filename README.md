this is readme file
The following product specification is the most up to date, you need to make connections between systems and process to understand how the user experiences the app.

Product background:
My web app is programmed through Python (3.1+)  and hosted on Streamlit (latest version 1.3+) that takes in a 90-day **super goal** and reverse engineers it into **3 actions** (for 3 months), **12 milestones** (for the 12 weeks) that is stored and displayed in streamlit . All generative components are complete through the GPT API. User data annd authentication process done on a Supabase table named user_plans, auto saving for the user is placed throughout code interactions.

Input UI and main switchboard:

The app starts with the login/signup page, which users claim a temporary auth token. The app goes to the new users input page where there are input fields for user’s desired supergoal, profile, and desired plan structure.

The majority of User’s navigation is complete by a conditional switchboard (using the session_state.page variable)  inside the main code file [roadmap.py](http://roadmap.py/) which calls different functions to display the appropriate page: the login page, goal input page, and the main dashboard with auxiliary progress like weekly progress status and banner generation. Most of the time the user will spend their time in the main roadmap dashboard. If an authenticated user already has an existing plan on supabase, they will be taken to the main dashboard first.

Generative component: OpenAI GPT-4o’s text generation is done through chat completion inside [generation.py](http://generation.py/). Based on the user inputs, the chatbot will make: month actions, week milestones generation. Later on demand, rhe use can also call other functions in the generation file to make contextual daily tasks and adjust weekly milestone titles.

main dashboard UI:

Once the chatbot generates the two basic list (The 3 actions and 12 corresponding milestones), they are first parsed, then stored as JSON lists inside supabase. Then they are displayed across month columns and week row with the main dashboards container UI:

The main dashboard is hosted through the function render_dashboard() which enables a radio that can toggle between a full view, month view, week view, and today view. The full view has click through milestone buttons that can temporarily lead to a certain week using streamlit params (in the url) while the active week or day persists, the month view to week view to day view buttons all have a similar click-through system. the actual week and day are indicated where visible using a green circle prefix

To display the month and week views in more detail within the main dashboard, the [[milestone.py](http://milestone.py/)] is a helper that renders items within a week under two styles (month view seeing the four matching weeks and week view seeing the 7 matching days). Critically, when a user navigates to the active day through the “today view” radio toggle or any day using the temporary click through buttons, the render_day functions helps users access the generation of two day tasks with the ability to edit them. Daily tasks are stored in the  all_weeks mega list (with a supabase backup).

#built-in features

Goal prompt embedding: handled inside [goodprompt.py](http://goodprompt.py) and called by [generation.py](http://generation.py) when sending the prompt to chatGPT chat completion. at the generation stage, embeddings are used to match the user’s specific goal with the closest of the 10 example goals stored each with corresponding reference actions and milestones, the most aligned set is inserted into the main prompt.

Image generation: handled primarily inside imagegeneration.py, a user can call for a cartoon banner to be generated based on their super goal, once complete it borrows a space with show_progress_boss() to be displayed and the image is saved inside a supabase bucket with the corresponding image url inside the user_plans. The image generation is called from a threadpoolexecutor setup in [roadmap.py](http://roadmap.py) so the generation handling is separate and doesn’t freeze the main UI.

Timekeeping: the active day is calculated by finding the user’s start_date set inside the supabase. This is managed inside supabasecode.py

progress boss UI: hosted in parallel to render_dashbaord() in [roadmap.py](http://roadmap.py) using show_progress_boss(), a cartoon character is displayed with an emotional state based on the completion rate of the daily tasks that the user generated current week. Under the character are the existing tasks for the active day. Later on, this is meant to be the “at a glance” for the users main phone screen.

Tokenized autologin: Supabase is used for automating login/signup, loading the plan, saving the plan (used at certain checkpoints in the main flow), tracking the date, and modifying the date, this is all done through functions in the [[supabasecode.py](http://supabasecode.py/)] file. After signing in, two autologin tokens are stored in streamlit params (in the url) to be authorized if refreshed.