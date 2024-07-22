import streamlit as st
from openai import OpenAI
import openai
import time
from PIL import Image
import os
from dotenv import load_dotenv
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

# Try to load from environment variables (including those loaded from .env)
API_KEY = os.getenv("API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Set up OpenAI client
client = OpenAI(api_key=API_KEY)
openai.api_key = API_KEY

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "file_id" not in st.session_state:
    st.session_state.file_id = None

if "uploaded_file_id" not in st.session_state:
    st.session_state.uploaded_file_id = None

# Set up the Streamlit app
st.set_page_config(page_title="AI Chat Assistant", page_icon="🤖")

# Load and display the enterprise logo
logo = Image.open("images/logo-dfm.png")
st.image(logo, width=200)

# Set up the Streamlit app
st.title("Chat with AI Assistant")
st.sidebar.title("Image uploader")


uploaded_file = st.sidebar.file_uploader("Upload an image file", type=["jpg", "jpeg", "png"])

if (uploaded_file):
    image = Image.open(uploaded_file)
    st.sidebar.image(image, caption='Uploaded Image.', use_column_width=True)



# If there is an uploaded file and it is different from the last uploaded file
if uploaded_file is not None and st.session_state.uploaded_file_id != uploaded_file.file_id:
    # we add this condition to avoid uploading the same file multiple times for each users message

    # Convert PIL Image back to bytes
    buffered = BytesIO()
    image.save(buffered, format=image.format)
    image_bytes = buffered.getvalue()


    response = openai.files.create(
        file=("imageUploadedFromMikes."+image.format.lower(), image_bytes, f"image/{image.format.lower()}"),
        purpose='vision',
    )

    st.session_state.uploaded_file_id = uploaded_file.file_id
    st.session_state.file_id = response.id


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

    content = [{
        "type": "text",
        "text": user_input
        }
    ]

    if st.session_state.file_id:
        content.append({
            "type": "image_file",
            "image_file": {
                "file_id": st.session_state.file_id
            }
        })

    # Add user message to the thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=content
    )

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID,
        additional_instructions="Veuillez ne pas inclure de citations ou de références sous la forme de 4:0†source】 à la fin de chaque réponse. Fournissez simplement les informations demandées sans ajouter de références explicites."
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