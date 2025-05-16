import streamlit as st
import os
import requests
from bs4 import BeautifulSoup
import json
from openai import OpenAI

# Page configuration
st.set_page_config(
    page_title="EF Gap Year Assistant",
    page_icon="🌎",
    layout="centered"
)

# Custom CSS for chat interface
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

# URLs in the proper order as provided by the user
PROGRAM_URLS = [
    "https://a.storyblok.com/f/234741/x/46a3c53899/socialidentityresourcesfortravelers_2-14-23.pdf",
    "https://efgapyear.com/program-guide-the-changemaker-fall-2025-session-1/",
    "https://efgapyear.com/program-guide-the-changemaker-fall-2025-session-2/",
    "https://efgapyear.com/program-guide-the-changemaker-spring-2026-session-1/",
    "https://efgapyear.com/program-guide-the-changemaker-spring-2026-session-2/",
    "https://efgapyear.com/program-guide-the-pathfinder-fall-2025-session-1/",
    "https://efgapyear.com/program-guide-the-pathfinder-fall-2025-session-2/",
    "https://efgapyear.com/en/program-guide-the-pathfinder-spring-2026-session-1/",
    "https://efgapyear.com/program-guide-the-pathfinder-spring-2026-session-2/",
    "https://efgapyear.com/program-guide-the-voyager-fall-2025-session-1/",
    "https://efgapyear.com/program-guide-the-voyager-fall-2025-session-2/",
    "https://efgapyear.com/program-guide-the-voyager-spring-2026-session-1/",
    "https://efgapyear.com/program-guide-the-voyager-spring-2026-session-2/",
    "https://efgapyear.com/program-guide-the-year-2025-26-session-1/",
    "https://efgapyear.com/program-guide-the-year-2025-26-session-2/",
    "https://efgapyear.com/program-guide-the-year-2025-26-session-3/"
]

# Simplified EF Gap Year program information based on latest research
PROGRAM_SUMMARIES = {
    "changemaker": """
    The Changemaker is designed for impact-driven adventurers who want to experience sustainable lifestyles and work on conservation projects.
    - Focus: Service learning, sustainability, conservation
    - Destinations: Costa Rica, Dominican Republic, Peru, Ecuador, Galapagos
    - Activities: Working with locals on global challenges, exploring ecosystems, conservation projects
    - Duration: 10-week semester program
    - Fall 2025 Session 1: September-December 2025
    - Fall 2025 Session 2: January-April 2026
    - Spring 2026 Sessions also available
    """,
    
    "pathfinder": """
    The Pathfinder is perfect for hands-on learners trying to figure out their next steps in life.
    - Focus: Career exploration, cultural immersion, academic discovery
    - Destinations: England, France, Spain, Portugal, Germany, Switzerland, Italy
    - Activities: Exploring international cities, cultural immersion, introduction to various academic fields
    - Duration: 10-week semester program
    - Fall 2025 Session 1: September-December 2025
    - Fall 2025 Session 2: January-April 2026
    - Spring 2026 Sessions also available
    """,
    
    "voyager": """
    The Voyager allows students to explore natural wonders and diverse cultures across multiple countries.
    - Focus: Cultural exploration, adventure, conservation
    - Destinations: Australia, Thailand, Japan
    - Activities: Exploring lush environments, conservation projects, cultural immersion
    - Duration: 10-week semester program
    - Fall 2025 Session 1: September-December 2025
    - Fall 2025 Session 2: January-April 2026
    - Spring 2026 Sessions also available
    """,
    
    "year": """
    The Year Program offers a comprehensive gap year experience combining the best elements of other programs.
    - Focus: Comprehensive experience with language, service, internship, and cultural immersion
    - Destinations: Multiple international locations across Europe, Asia, and Latin America
    - Duration: 23-week full academic year program
    - 2025-2026 Academic Year: September 2025-April 2026
    """
}

# General program information
GENERAL_INFO = """
All EF Gap Year programs include:
- 24/7 support from EF staff
- Pre-departure support with visa guidance
- International health insurance
- College credit options
- Regular group activities and excursions
- Orientation and leadership training
- Cultural immersion experiences
- Accommodation (varies by program: homestays, residences, hotels)
- Some meals (varies by program)
- Transportation between destinations

Required documentation:
- Valid passport (valid 6+ months after program end)
- Visas (varies by destination, EF provides guidance)
- Health documentation (varies by destination)

Common concerns addressed:
- Safety: 24/7 staff support, vetted accommodations and activities
- Homesickness: Community-building activities, regular check-ins
- Language barriers: No prior experience needed, staff assistance provided
- Making friends: Orientation activities designed to foster connections
"""

# System instructions
SYSTEM_INSTRUCTIONS = """
You are an assistant for prospective EF Gap Year students, designed to help them prepare for their upcoming programs.

Guidelines:
1. Answer ONLY questions about EF Gap Year programs using the provided information.
2. Be kind, thorough, clear, helpful, trustworthy, and confidence-inspiring.
3. Remember these are nervous students preparing for international travel.
4. If you don't have an accurate answer, say: "I am not sure I can provide an accurate answer to that question. I suggest connecting with your human EF Gap Year advisor on this one."
5. For non-EF Gap Year questions, politely respond: "My role is to help you prepare for your EF Gap Year or Semester program, so I'm afraid I cannot help with this particular question."
6. After each response, ask ONE relevant follow-up question.

Use the following information to answer questions:
{program_info}

{general_info}

Student Query: {query}
Previous Conversation: {conversation}
"""

# Check for OpenAI API key
if "OPENAI_API_KEY" not in os.environ and "openai_api_key" not in st.session_state:
    st.error("⚠️ OpenAI API key not found. Please enter your API key below:")
    
    api_key = st.text_input("OpenAI API Key:", type="password")
    if api_key:
        st.session_state.openai_api_key = api_key
        st.success("API key set successfully!")
    else:
        st.stop()
else:
    api_key = os.environ.get("OPENAI_API_KEY", st.session_state.get("openai_api_key", ""))

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

def get_program_info_for_query(query):
    """Get relevant program information based on the query"""
    query_lower = query.lower()
    
    # Combine all program summaries
    all_info = ""
    
    # Check which programs are relevant to the query
    if any(keyword in query_lower for keyword in ["changemaker", "sustainability", "costa rica", "dominican", "peru", "ecuador", "galapagos", "conservation"]):
        all_info += "CHANGEMAKER PROGRAM:\n" + PROGRAM_SUMMARIES["changemaker"] + "\n\n"
    
    if any(keyword in query_lower for keyword in ["pathfinder", "europe", "england", "france", "spain", "portugal", "germany", "switzerland", "italy"]):
        all_info += "PATHFINDER PROGRAM:\n" + PROGRAM_SUMMARIES["pathfinder"] + "\n\n"
    
    if any(keyword in query_lower for keyword in ["voyager", "australia", "thailand", "japan", "adventure"]):
        all_info += "VOYAGER PROGRAM:\n" + PROGRAM_SUMMARIES["voyager"] + "\n\n"
    
    if any(keyword in query_lower for keyword in ["year", "full year", "23-week", "23 week", "academic year"]):
        all_info += "YEAR PROGRAM:\n" + PROGRAM_SUMMARIES["year"] + "\n\n"
    
    # If no specific program is mentioned, include all program information
    if not all_info or any(keyword in query_lower for keyword in ["all programs", "programs", "options", "compare", "difference"]):
        all_info = "PROGRAM OPTIONS:\n"
        for program, info in PROGRAM_SUMMARIES.items():
            all_info += f"{program.upper()} PROGRAM:\n{info}\n\n"
    
    return all_info

def get_chatbot_response(query, conversation_history):
    """Get response from OpenAI using program information"""
    try:
        # Get relevant program information
        program_info = get_program_info_for_query(query)
        
        # Format conversation history
        conversation_text = ""
        for message in conversation_history[-6:]:  # Last 6 messages
            role = "Student" if message["role"] == "user" else "Assistant"
            conversation_text += f"{role}: {message['content']}\n\n"
        
        # Format the prompt
        prompt = SYSTEM_INSTRUCTIONS.format(
            program_info=program_info,
            general_info=GENERAL_INFO,
            query=query,
            conversation=conversation_text
        )
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for EF Gap Year students."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return "I encountered an error processing your question. Please try again or contact your EF Gap Year advisor for assistance."

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
    """Main function for the Streamlit app"""
    # Header
    st.markdown("<h1 class='ef-header'>EF Gap Year Assistant</h1>", unsafe_allow_html=True)
    st.markdown("""
    Welcome to the EF Gap Year Assistant! I'm here to help you prepare for your upcoming 
    gap year or semester program. Feel free to ask me any questions about your program,
    travel preparations, or what to expect during your EF Gap Year experience.
    """)
    
    # Initialize session state for messages
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    display_messages()
    
    # Chat input
    user_input = st.chat_input("Type your question here...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Show spinner during processing
        with st.spinner("Thinking..."):
            response = get_chatbot_response(user_input, st.session_state.messages)
            
        # Add bot response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Force a rerun to update the UI with the new messages
        st.rerun()

if __name__ == "__main__":
    main()
