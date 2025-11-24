import streamlit as st
import os
from groq import Groq
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
from streamlit_lottie import st_lottie
import requests
import base64
import io
import edge_tts
import asyncio

# --- 1. CONFIGURATION & PAGE SETUP ---
st.set_page_config(
    page_title="MOCKMATE - AI Interviewer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS FOR VISIBILITY & GLASSMORPHISM ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #FFFFFF;
    }
    
    /* FORCE ALL TEXT TO WHITE */
    h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
    }
    
    /* 3D Glass Cards for Chat */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.1); 
        backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 15px;
    }
    
    /* Hover Effect */
    .stChatMessage:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(135, 206, 250, 0.5); /* Light blue border on hover */
    }

    /* FIX INPUT FIELDS (Text Input & Selectbox) */
    /* This solves the "Black text on dark background" issue */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] div {
        color: #00FFFF !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Title Gradient - Made Brighter (Cyan to Blue) */
    .gradient-text {
        background: -webkit-linear-gradient(left, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3em;
        font-weight: bold;
    }
    
    /* Info Text (Light Blue) */
    .info-text {
        color: #87CEFA !important; /* Light Sky Blue */
        font-size: 1.1em;
        font-weight: 500;
    }
    /* CUSTOM BUTTON STYLING */
    div.stButton > button {
        background: linear-gradient(to right, #ff416c, #ff4b2b); /* Red Gradient */
        color: white !important;
        border: none;
        padding: 10px 20px;
        border-radius: 10px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(255, 75, 43, 0.4);
        transition: all 0.3s ease;
    }

    /* Hover Effect for Button */
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 75, 43, 0.6);
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

def text_to_speech(text):
    """
    Uses Edge TTS (Microsoft Azure Neural Voice) for free high-quality audio.
    """
    async def generate_audio():
        communicate = edge_tts.Communicate(text, "en-US-BrianNeural") # Brian is a great interviewer voice
        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])
        return audio_buffer

    try:
        # Run the async function
        audio_buffer = asyncio.run(generate_audio())
        audio_bytes = audio_buffer.getvalue()
        
        audio_base64 = base64.b64encode(audio_bytes).decode()
        audio_html = f'<audio src="data:audio/mp3;base64,{audio_base64}" autoplay="autoplay" controls="controls" style="display:none;"></audio>'
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Edge TTS Error: {e}")

def transcribe_audio(audio_bytes):
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "input.wav" 
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3",
            prompt="The audio is a job interview candidate speaking.", 
            response_format="json",
            language="en"
        )
        return transcription.text
    except Exception as e:
        st.error(f"Transcription Error: {e}")
        return None

def get_ai_response(user_text, client):
    """
    The Brain: Dynamically adapts to the Role and Interview Stage.
    """
    role = st.session_state.target_role
    level = st.session_state.experience_level
    stage = st.session_state.interview_stage.upper()
    
    system_prompt = f"""
    You are an expert AI Interview practice agent.
    Target Role: {role}
    Candidate Level: {level}
    Current Stage: {stage}
    
    YOUR GOAL: Conduct a realistic interview.
    
    ### BEHAVIORAL GUIDELINES
    1. **Adaptability:** - If user is **Confused**: Provide a hint relevant to {role}.
       - If user is **Efficient**: Move to next topic.
       - If user is **Chatty**: Steer back to {role} skills.
    
    ### STAGE INSTRUCTIONS
    - **INTRODUCTION**: Ask about background in {role}. 
      *TRANSITION RULE:* If satisfied, output token: "MOVING_TO_HARD_SKILLS".
      
    - **HARD_SKILLS**: Ask technical question for {role}.
      *TRANSITION RULE:* If answered, output token: "MOVING_TO_SOFT_SKILLS".
      
    - **SOFT_SKILLS**: Ask situational question.
      *TRANSITION RULE:* If answered, output token: "MOVING_TO_FEEDBACK".
      
    - **FEEDBACK**: Give constructive feedback.
    
    ### FORMAT
    - Keep output conversational (under 3 sentences).
    - Ask ONE question at a time.
    """

    messages = [{"role": "system", "content": system_prompt}] + st.session_state.chat_history
    messages.append({"role": "user", "content": user_text})
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.6,
            max_tokens=800
        )
        ai_text = response.choices[0].message.content
        
        # --- HIDDEN STATE LOGIC ---
        if "MOVING_TO_HARD_SKILLS" in ai_text:
            st.session_state.interview_stage = "hard_skills"
            ai_text = ai_text.replace("MOVING_TO_HARD_SKILLS", f"Thanks. Let's move to technical questions about {role}.")
            
        elif "MOVING_TO_SOFT_SKILLS" in ai_text:
            st.session_state.interview_stage = "soft_skills"
            ai_text = ai_text.replace("MOVING_TO_SOFT_SKILLS", "Good answer. Now, let's look at how you handle situations.")
            
        elif "MOVING_TO_FEEDBACK" in ai_text:
            st.session_state.interview_stage = "feedback"
            ai_text = ai_text.replace("MOVING_TO_FEEDBACK", "I've gathered enough. Here is my feedback on your interview.")
            
        return ai_text
    
    except Exception as e:
        return "I apologize, I lost my train of thought. Could you repeat that?"

# --- 4. SESSION STATE INITIALIZATION ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "interview_stage" not in st.session_state:
    st.session_state.interview_stage = "introduction"
if "target_role" not in st.session_state:
    st.session_state.target_role = "General Role"
if "experience_level" not in st.session_state:
    st.session_state.experience_level = "Entry Level"

# --- 5. SIDEBAR SETTINGS ---
with st.sidebar:
    st.title("⚙️ Settings")
    
    # Lottie Animation
    lottie_url = "https://assets5.lottiefiles.com/packages/lf20_49rdyysj.json" 
    lottie_json = load_lottieurl(lottie_url)
    if lottie_json:
        st_lottie(lottie_json, height=150, key="ai_anim")
        
    api_key_input = st.text_input("Groq API Key:", type="password")
    if api_key_input:
        st.session_state.GROQ_API_KEY = api_key_input
        
    st.markdown("---")
    
    # --- Config Inputs ---
    st.subheader("🎯 Interview Config")
    st.session_state.target_role = st.text_input("Target Role:", value=st.session_state.target_role)
    st.session_state.experience_level = st.selectbox("Experience:", ["Entry Level", "Mid-Level", "Senior/Executive"], index=0)

    st.markdown("---")
    st.markdown(f"**Current Stage:** `{st.session_state.interview_stage.replace('_', ' ').upper()}`")
    
    if st.button("🔄 Reset Interview"):
        st.session_state.chat_history = []
        st.session_state.interview_stage = "introduction"
        st.experimental_rerun()

# --- 6. MAIN LOGIC ---
if "GROQ_API_KEY" not in st.session_state:
    st.session_state.GROQ_API_KEY = "" # Replaced hardcoded key for security

if not st.session_state.GROQ_API_KEY:
    st.warning("⚠️ Please enter your Groq API Key in the sidebar.")
    st.stop()

client = Groq(api_key=st.session_state.GROQ_API_KEY)

# --- UI LAYOUT ---
st.markdown('<h1 class="gradient-text">MOCKMATE: AI INTERVIEWER</h1>', unsafe_allow_html=True)

# Styled info text
st.markdown(
    f"""<div class="info-text">
        Targeting Role: <b>{st.session_state.target_role}</b> | 
        Level: <b>{st.session_state.experience_level}</b>
    </div>""", 
    unsafe_allow_html=True
)

# Chat Area (Legacy Version)
chat_container = st.container()
with chat_container:
    for message in st.session_state.chat_history:
        if message["role"] == "assistant":
            st.info(f"🤖 AI: {message['content']}")
        else:
            st.warning(f"👤 You: {message['content']}")

# Footer / Input Area
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    audio_data = mic_recorder(
        start_prompt="🎙️ Start Speaking",
        stop_prompt="🛑 Stop & Send",
        key="recorder",
        just_once=True,
        use_container_width=True
    )

if audio_data is not None:
    user_text = transcribe_audio(audio_data['bytes'])
    if user_text:
        st.session_state.chat_history.append({"role": "user", "content": user_text})
        
        # Pass both arguments correctly:
        ai_response = get_ai_response(user_text, client) 
        
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        st.experimental_rerun()

# Audio Autoplay
if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "assistant":
    last_response = st.session_state.chat_history[-1]["content"]
    text_to_speech(last_response)
