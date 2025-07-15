import json
from supabase import create_client, Client
import streamlit as st # Assuming you are using Streamlit

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

data = {
    "user_id": "me new",
    "raw_text": "here some raw text",
    "months": json.dumps(["Jan", "Feb", "Mar"]),
    "weeks": json.dumps(["Week 1", "Week 2"]),
}

if st.button("test it"):
	try:
	    response = supabase.table("user_plans").upsert(data, on_conflict=["user_id"]).execute()
	    st.success("Upsert successful!") # Use st.success for success messages
	    st.json(response.data) # Display the response data as JSON
	except Exception as e:
	    st.error(f"Error during upsert: {e}") # Corrected error message