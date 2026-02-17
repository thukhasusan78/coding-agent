import streamlit as st
import yaml
import os
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime

# Internal imports (assumed structure based on context)
# from tutor_engine import ChineseTutorEngine 

class ChineseTutorApp:
    def __init__(self):
        self.config = self._load_config()
        self._setup_page()
        self._init_session_state()
        self.db_path = "checkpoints.sqlite"

    def _load_config(self) -> Dict:
        """Load configuration from config.yml"""
        try:
            with open("config.yml", "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {
                "app_name": "AI Chinese Tutor",
                "hsk_levels": ["HSK 1", "HSK 2", "HSK 3", "HSK 4", "HSK 5", "HSK 6"],
                "lessons": {
                    "HSK 1": ["Greetings", "Numbers", "Family", "Food"],
                    "HSK 2": ["Shopping", "Weather", "Transport", "Health"]
                }
            }

    def _setup_page(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title=self.config.get("app_name", "Chinese Tutor"),
            page_icon="🏮",
            layout="wide"
        )
        st.markdown("""
            <style>
            .main { background-color: #f5f7f9; }
            .stChatMessage { border-radius: 15px; }
            .pinyin { color: #888; font-size: 0.8em; }
            </style>
        """, unsafe_allow_html=True)

    def _init_session_state(self):
        """Initialize persistent session variables"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "current_lesson" not in st.session_state:
            st.session_state.current_lesson = "Greetings"
        if "hsk_level" not in st.session_state:
            st.session_state.hsk_level = "HSK 1"
        if "thread_id" not in st.session_state:
            import uuid
            st.session_state.thread_id = str(uuid.uuid4())

    def render_sidebar(self):
        """Render the navigation and settings sidebar"""
        with st.sidebar:
            st.title("🏮 Learning Hub")
            
            st.subheader("Curriculum")
            hsk_level = st.selectbox(
                "Select HSK Level", 
                options=self.config.get("hsk_levels", []),
                index=0
            )
            
            lessons = self.config.get("lessons", {}).get(hsk_level, ["General Conversation"])
            lesson = st.selectbox("Select Lesson", options=lessons)
            
            if lesson != st.session_state.current_lesson or hsk_level != st.session_state.hsk_level:
                st.session_state.hsk_level = hsk_level
                st.session_state.current_lesson = lesson
                self.reset_conversation()

            st.divider()
            
            st.subheader("Settings")
            st.toggle("Show Pinyin", value=True, key="show_pinyin")
            st.toggle("Auto-Translate", value=False, key="auto_translate")
            st.slider("Speaking Speed", 0.5, 1.5, 1.0, 0.1)

            if st.button("Clear Chat History", use_container_width=True, type="secondary"):
                self.reset_conversation()
                st.rerun()

    def reset_conversation(self):
        """Reset the chat state"""
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": f"Ni hao! I am your {st.session_state.hsk_level} tutor. Today we are practicing: **{st.session_state.current_lesson}**. How can I help you start?"
            }
        ]

    def display_chat(self):
        """Render the conversation history"""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "pinyin" in message and st.session_state.show_pinyin:
                    st.caption(f"Pinyin: {message['pinyin']}")

    def handle_user_input(self):
        """Process user input and generate tutor response"""
        if prompt := st.chat_input("Type your Chinese or English here..."):
            # Add user message to state
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                # Logic for Tutor Engine (Mocking the LLM call here)
                # In a real scenario, this would call a LangChain/LangGraph agent
                # using the checkpoints.sqlite for memory.
                
                # Mock Response Logic
                mock_response = f"That's a great start for our '{st.session_state.current_lesson}' lesson! Can you try saying that in Chinese?"
                full_response = mock_response
                
                response_placeholder.markdown(full_response)
                
                # Add to history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": full_response,
                    "pinyin": "Nà shì yīgè hǎo de kāishǐ..." # Example pinyin
                })

    def run(self):
        """Main application loop"""
        st.title(f"Interactive Chinese Tutor: {st.session_state.current_lesson}")
        
        self.render_sidebar()
        
        # Main UI Layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            self.display_chat()
            self.handle_user_input()
            
        with col2:
            st.subheader("Vocabulary List")
            st.info("New words from this session will appear here.")
            # Example vocab list
            vocab = {"你好 (Nǐ hǎo)": "Hello", "谢谢 (Xièxiè)": "Thank you"}
            for zh, en in vocab.items():
                st.write(f"**{zh}**: {en}")

            st.divider()
            st.subheader("Grammar Tips")
            st.warning("Subject + Verb + Object is the basic structure in Chinese.")

if __name__ == "__main__":
    app = ChineseTutorApp()
    app.run()