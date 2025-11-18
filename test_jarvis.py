import streamlit as st
st.set_page_config(page_title="Jarvis", page_icon="🧠")
st.title("🧠 BrotherG Jarvis")
st.success("SUCCESS!")
user_input = st.text_input("Type:")
if user_input:
    st.info(f"You said: {user_input}")
