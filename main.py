import streamlit as st
from openai import OpenAI
import time
from PIL import Image
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try to load from environment variables (including those loaded from .env)
API_KEY = os.getenv("API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")


# Set up OpenAI client
client = OpenAI(api_key=API_KEY)
# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None


# Set up the Streamlit app
st.set_page_config(page_title="AI Chat Assistant", page_icon="🤖")

# Load and display the enterprise logo
logo = Image.open("images/logo-dfm.png")
st.image(logo, width=200)

# Set up the Streamlit app
st.title("Chat with AI Assistant")


# # Load custom avatars
# user_avatar = Image.open("path_to_user_avatar.png")
# bot_avatar = Image.open("path_to_bot_avatar.png")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Get user input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Create a thread if it doesn't exist
    if not st.session_state.thread_id:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    # Add user message to the thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input
    )

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID
    )

    # Wait for the assistant to complete
    while run.status != "completed":
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)

    # Retrieve and display the assistant's response
    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
    assistant_message = messages.data[0].content[0].text.value

    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
    with st.chat_message("assistant"):
        st.write(assistant_message)

# Add a button to clear the chat history
if st.button("Clear Chat History"):
    st.session_state.messages = []
    st.session_state.thread_id = None
    st.experimental_rerun()