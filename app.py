import streamlit as st
import os
from dotenv import load_dotenv
import logging
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import time

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="EF Gap Year Assistant",
    page_icon="🌎",
    layout="centered"
)

# Constants - keep these minimal
MAX_URLS_TO_PROCESS = 3  # Extremely limited to avoid timeouts
GPT_MODEL = "gpt-3.5-turbo"  # Using GPT-3.5 for speed
REQUEST_TIMEOUT = 10  # Short timeout for web requests

# Check for OpenAI API key
if "OPENAI_API_KEY" not in os.environ:
    st.error("⚠️ OpenAI API key not found. Please set your API key in the app settings.")
    st.info("You can set your OpenAI API key in the app settings by clicking on 'Manage app' in the lower right corner.")
    
    # Add a form for entering the API key directly
    with st.form("api_key_form"):
        api_key = st.text_input("Enter your OpenAI API key:", type="password")
        submit_button = st.form_submit_button("Set API Key")
        
        if submit_button:
            if api_key.strip():
                os.environ["OPENAI_API_KEY"] = api_key
                st.success("API key set successfully! Please refresh the page.")
                st.experimental_rerun()
            else:
                st.error("Please enter a valid API key.")
    
    # Stop execution if no API key
    st.stop()

# Initialize OpenAI client
try:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except Exception as e:
    st.error(f"Failed to initialize OpenAI client: {str(e)}")
    st.stop()

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
    .ef-header {
        color: #FF5252;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: row;
        align-items: flex-start;
    }
    .chat-message.user {
        background-color: #E0F7FA;
    }
    .chat-message.bot {
        background-color: #F3E5F5;
    }
    .chat-message .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 1rem;
    }
    .chat-message .message {
        flex-grow: 1;
    }
</style>
""", unsafe_allow_html=True)

# System instructions - kept brief to reduce token usage
SYSTEM_INSTRUCTIONS = """
You are a helpful assistant for EF Gap Year students.
Answer questions based ONLY on the provided context information.
Be kind, helpful, and confidence-inspiring.
If unsure, suggest contacting an EF Gap Year advisor.
For non-program questions, politely explain your role is to help with EF Gap Year programs.
End responses with a relevant follow-up question.
"""

# Essential URLs only - extremely limited to avoid resource issues
URLS = [
    # Only most important pages for essential programs
    "https://efgapyear.com/program-guide-the-changemaker-fall-2025-session-1/",
    "https://efgapyear.com/program-guide-the-pathfinder-fall-2025-session-1/",
    "https://efgapyear.com/program-guide-the-voyager-fall-2025-session-1/"
]

# Hard-coded backup information in case scraping fails
BACKUP_PROGRAM_INFO = """
EF Gap Year offers several programs:

1. The Changemaker: A program focused on language learning, service learning, and leadership development.
   - Fall 2025 Session 1: September - December 2025
   - Fall 2025 Session 2: January - April 2026
   - Spring 2026 Sessions also available

2. The Pathfinder: A program with language study, internship, and cultural immersion.
   - Fall 2025 Session 1: September - December 2025
   - Fall 2025 Session 2: January - April 2026
   - Spring 2026 Sessions also available

3. The Voyager: A program focused on cultural exploration across multiple countries.
   - Fall 2025 Session 1: September - December 2025
   - Fall 2025 Session 2: January - April 2026
   - Spring 2026 Sessions also available

4. The Year: A comprehensive program combining the best elements of all programs.
   - 2025-26 Sessions run from September 2025 through April 2026

For specific details about destinations, activities, and pricing, please contact your EF Gap Year advisor.
"""

def extract_web_content(url, timeout=REQUEST_TIMEOUT, max_length=10000):
    """Extract content from web pages with timeout and length limit"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code != 200:
            return ""
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Truncate to avoid memory issues
        return text[:max_length]
    except Exception as e:
        logger.error(f"Error extracting web content from {url}: {e}")
        return ""

def fetch_minimal_content(max_urls=MAX_URLS_TO_PROCESS):
    """Fetch content with extreme resource constraints"""
    if "content_cache" not in st.session_state:
        content_collection = []
        
        with st.status("Loading information...", expanded=True) as status:
            for i, url in enumerate(URLS[:max_urls]):
                if i > 0:
                    # Add delay between requests to avoid rate limiting
                    time.sleep(2)
                
                st.write(f"Loading program information {i+1}/{max_urls}...")
                try:
                    content = extract_web_content(url)
                    if content:
                        content_collection.append({
                            'source': url.split('/')[-2],  # Just use program name as source
                            'content': content
                        })
                except Exception as e:
                    logger.error(f"Error fetching {url}: {e}")
            
            # If we couldn't get content, use backup info
            if not content_collection:
                st.write("Using backup program information...")
                content_collection = [{
                    'source': 'backup-info',
                    'content': BACKUP_PROGRAM_INFO
                }]
            
            status.update(label="Information loaded", state="complete")
            st.session_state.content_cache = content_collection
    
    return st.session_state.content_cache

def get_chatbot_response(query, chat_history=None):
    """Get response using minimal processing"""
    if chat_history is None:
        chat_history = []
    
    try:
        # Get content
        content_collection = fetch_minimal_content()
        
        # Prepare context (use all available content - we have very limited content)
        context_text = "\n\n".join([
            f"Information about {item['source']}:\n{item['content'][:5000]}"  # Limit size
            for item in content_collection
        ])
        
        # Keep context size manageable
        if len(context_text) > 15000:
            context_text = context_text[:15000] + "..."
        
        # Prepare chat history (keep minimal)
        history_text = ""
        for msg in chat_history[-4:]:  # Just last 4 messages
            role = "Student" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content'][:150]}\n"  # Truncate long messages
        
        # Create prompt
        prompt = f"{SYSTEM_INSTRUCTIONS}\n\nCONTEXT:\n{context_text}\n\nHISTORY:\n{history_text}\n\nStudent: {query}\n\nAssistant:"
        
        # Get response
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500  # Keep responses reasonably short
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error in chatbot response: {e}")
        return "I'm sorry, I encountered a technical issue. Please try asking again or contact your EF Gap Year advisor for assistance."

def display_messages():
    """Display chat messages"""
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user">
                <img class="avatar" src="https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y">
                <div class="message">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message bot">
                <img class="avatar" src="https://a.storyblok.com/f/152976/x/807eb80d2a/favicon-removebg-preview.png">
                <div class="message">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)

def main():
    """Main function with minimal processing"""
    # Header
    st.markdown("<h1 class='ef-header'>EF Gap Year Assistant</h1>", unsafe_allow_html=True)
    st.markdown("""
    Welcome to the EF Gap Year Assistant! I'm here to help you prepare for your upcoming 
    gap year or semester program. Feel free to ask me any questions about your program.
    """)
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Initialize content - don't do this on first load to avoid timeout
    # Let it happen when the user asks a question
    
    # Display chat messages
    display_messages()
    
    # Chat input
    user_input = st.chat_input("Type your question here...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.experimental_rerun()  # Rerun to show the user message immediately
    
    # Process the last user message if it hasn't been responded to yet
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.spinner("Thinking..."):
            user_query = st.session_state.messages[-1]["content"]
            response = get_chatbot_response(user_query, st.session_state.messages[:-1])
            
            # Add bot response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Force a rerun to update the UI with the bot response
        st.experimental_rerun()

if __name__ == "__main__":
    main()
