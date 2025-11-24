# MockMate-AIMockInterviewer
Bridging the Gap Between Preparation and Performance.

#**Table of Contents**
1.	Setup Instructions
2.	Architecture
3.	Design Decision

**1.Setup instruction:**
1.	Vs code
2.	Python 3.8 installed
3.	Get groq api key(get it for free from (https://console.groq.com/keys)
4.	Create a folder named stremlit-ui2
Open the terminal-
5.	Create a virtual environment using 
    - Windows
    python -m venv venv
    .\venv\Scripts\activate
    - Mac/Linux
     python3 -m venv venv
     source venv/bin/activate
     make sure if your system allows scripts from settings
6.	Install dependencies
    pip install streamlit groq streamlit-mic-recorder gTTS edge-tts requests
7.	Create a file named app.py in the streamlit-ui2 folder
Write the required code there

**2. Architecture (Step-by-Step):**

A. The Setup & UI (Lines 1-80)
"I started by setting up the page configuration and injecting Custom CSS. I moved away from the standard Streamlit look to create a 'Glassmorphism' UI. This includes:
•	Gradient Backgrounds: To give it a modern, tech feel.
•	3D Chat Bubbles: I added shadow and hover effects so the chat feels interactive.
•	Forced Visibility: I overrode the default styles to ensure high contrast (White/Cyan text) against the dark background."
B. The "Ears" & "Mouth" (Lines 83-147)
"For the conversational loop, I created two helper functions:
1.	transcribe_audio: This takes the raw audio bytes from the microphone and sends them to Groq's Whisper model to get text.
2.	text_to_speech: This is an asynchronous function using EdgeTTS. It converts the AI's response into a neural audio stream that plays automatically in the browser."
C. The "Brain" & Agentic Logic (Lines 149-208)
(This is the most important part to explain)
"This function, get_ai_response, is where the Agentic Behavior lives. Instead of a simple chatbot, I implemented a State Machine inside the System Prompt.
•	Dynamic Context: The prompt injects the Target Role (e.g., Software Engineer) and Experience Level so the AI adapts its persona.
•	State Management: The agent tracks which stage it is in: Introduction, Hard Skills, Soft Skills, or Feedback.
•	Hidden Triggers: I instructed the LLM to output hidden tokens like MOVING_TO_HARD_SKILLS. My Python code detects these tokens to automatically advance the interview stage without the user needing to do anything."
D. Session State & Sidebar (Lines 210-256)
"Streamlit re-runs the code on every interaction. To prevent the bot from forgetting the conversation, I used st.session_state to act as the app's 'Memory'.
In the Sidebar, I included:
•	Configuration: Where users set their target role.
•	Visual Feedback: A Lottie animation to give the agent a 'face' and a dynamic status box showing the current interview stage."
E. The Main Execution Loop (Lines 258-End)
"Finally, this is the main event loop:
1.	The mic_recorder captures user audio.
2.	We transcribe it to text.
3.	We append the user's text to the chat history.
4.	We query the Llama-3 model for a response.
5.	We generate audio for the response and play it back.
This cycle repeats, creating a seamless voice-to-voice interview experience.

**3.Design Decision :**

1. The Brain (Inference Engine):
Used: Groq (Llama-3.3-70b)
Rejected: OpenAI (GPT-4o) or Local LLMs
"For the inference engine, I chose Groq's LPU architecture over standard GPUs like OpenAI's. In a voice-based application, latency is the killer. OpenAI often has a 2-3 second delay before responding, which breaks the immersion. Groq provides near-instantaneous responses, maintaining the flow of a real interview."
________________________________________
2. The Mouth (Text-to-Speech)
Used: EdgeTTS (Microsoft Neural)
Rejected: gTTS (Google Translate TTS) or ElevenLabs

"I initially considered gTTS because it's standard, but it sounds too robotic and lacks intonation. I also looked at ElevenLabs, but the cost and latency were too high. I settled on EdgeTTS as the perfect middle ground—it offers Neural Voice quality (comparable to paid tools) completely for free and with very low latency."
________________________________________
3. The Ears (Speech-to-Text)
Used: Whisper-Large-v3 (via Groq)
Rejected: Browser Native API (speech_recognition)

"I avoided the standard Python speech_recognition library because it struggles with technical jargon. Since this is a technical interview bot, it needs to understand words like 'Polymorphism' or 'Recursion' accurately. Whisper-Large-v3 provides state-of-the-art accuracy for technical vocabulary."
________________________________________
4. The Body (Frontend)
Used: Streamlit
Rejected: React/Next.js or Flask

"I chose Streamlit because it allowed me to focus on the Agentic Logic rather than writing boilerplate HTML/CSS. Its session_state management is perfect for handling the linear flow of an interview (Intro -> Questions -> Feedback) without needing a complex backend database."
________________________________________
5. The Logic (Agent Structure)
Used: Finite State Machine (FSM) in Prompt
Rejected: Standard RAG or "Chain of Thought"
"Most chatbots just answer whatever the user asks. However, an interviewer needs to lead the conversation. I implemented a State Machine approach. The agent isn't just generating text; it's deciding transitions. It explicitly tracks if it's in the 'Hard Skills' phase or 'Feedback' phase, ensuring the interview follows a logical, professional arc.











