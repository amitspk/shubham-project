# app.py
import streamlit as st
from agent import process_query

st.set_page_config(page_title="Shopping Assistant", page_icon="/Users/aks000z/Downloads/walmart_image.png")
st.image("/Users/aks000z/Downloads/walmart_image.png", width=150)
st.title("Shopping Assistant")


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display existing chat
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("What are you looking for today?")

if user_input:
    # Show user message
    st.chat_message("user").markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Let me find something for you..."):
            # Pass chat_history to process_query for context-aware responses
            print("chat_history" + str(st.session_state.chat_history))
            response = process_query(user_input, st.session_state.chat_history)
            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
