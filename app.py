import streamlit as st
import os
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

# Pre-populated knowledge base about EF Gap Year programs
KNOWLEDGE_BASE = """
EF Gap Year Programs Overview:

1. The Changemaker Program:
   - Focus: Language learning, service learning, leadership
   - Fall 2025 Session 1: September-December 2025
   - Fall 2025 Session 2: January-April 2026
   - Spring 2026 Sessions: Also available
   - Destinations typically include: London, Paris, Barcelona, Madrid
   - Activities: Language study, service projects, leadership training

2. The Pathfinder Program:
   - Focus: Language study, internship, cultural immersion
   - Fall 2025 Session 1: September-December 2025
   - Fall 2025 Session 2: January-April 2026
   - Spring 2026 Sessions: Also available
   - Destinations typically include: Tokyo, Sydney, Berlin, Florence
   - Activities: Language classes, international internship, cultural activities

3. The Voyager Program:
   - Focus: Cultural exploration across multiple countries
   - Fall 2025 Session 1: September-December 2025
   - Fall 2025 Session 2: January-April 2026
   - Spring 2026 Sessions: Also available
   - Destinations typically include: Multiple European and Asian cities
   - Activities: Cultural tours, adventure activities, experiential learning

4. The Year Program:
   - Duration: Full academic year (September 2025-April 2026)
   - Focus: Comprehensive experience combining best elements
   - 2025-26 Session: September 2025-April 2026
   - Destinations: Multiple international locations
   - Activities: Language learning, service, internship, cultural immersion

General Information:
- All programs include 24/7 support from EF staff
- Pre-departure support includes visa guidance, packing assistance
- Programs include international health insurance
- College credit options available for most programs
- Language classes taught by certified instructors
- Accommodation typically includes homestays, residence centers, or hotels
- Transportation between destinations arranged by EF
- Regular group activities and excursions included
- All programs have health, safety, and emergency protocols

Preparing for your trip:
- Required documentation: Valid passport (valid 6+ months after program end)
- Many destinations require visas which EF helps arrange
- Recommended: Basic language preparation for destination countries
- Packing essentials: Weather-appropriate clothing, adapter plugs, necessary medications
- Budgeting: Students should bring spending money for personal expenses
- Communication: International phone plans or local SIM cards recommended
- Cultural preparation: Research local customs and traditions

Common pre-departure concerns:
- Homesickness: EF provides support and community to help students adjust
- Safety: All destinations monitored for safety, staff available 24/7
- Language barriers: Programs designed for all language levels, including beginners
- Making friends: Orientation activities designed to foster friendships
- Academic concerns: Academic advisors help with college credit transfers
"""

# System instructions for the chatbot
SYSTEM_INSTRUCTIONS = """
You are a helpful assistant for prospective EF Gap Year students. Your role is to help them prepare for their 
upcoming gap year or semester programs by providing quick, accurate, and helpful responses based on the 
information provided about EF Gap Year resources.

Guidelines:
1. ONLY answer questions about EF Gap Year programs using ONLY the information from the provided knowledge base.
2. Your tone should be kind, thorough (but clear), helpful, trustworthy, and confidence-inspiring.
3. Remember, these are nervous students who are about to embark on a grand trip around the world, and their nerves are high.
4. Under NO circumstances should your responses be fabricated or misleading.
5. If you are not confident that you have an accurate answer to a student's question, respond with:
   "I am not sure I can provide an accurate answer to that question. I suggest connecting with your human EF Gap Year advisor on this one."
6. If a user asks any question that is NOT about an EF Gap Year program, politely respond with:
   "My role is to help you to prepare for your EF Gap Year or Semester program, so I am afraid I cannot help with this particular question."
7. After each response, ask ONE relevant follow-up question to further engage the student in conversation.
8. Your follow-up question should allow them to expand on their initial query, request more information, or ensure they're receiving necessary information.

Knowledge Base:
{knowledge_base}

Conversation History:
{conversation_history}

Student Question: {question}
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

def get_chatbot_response(query, conversation_history):
    """Get response from the chatbot using the static knowledge base"""
    try:
        # Format conversation history
        history_text = ""
        for msg in conversation_history[-6:]:  # Include up to last 6 messages
            role = "Student" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n\n"
        
        # Format the prompt with all the required information
        formatted_prompt = SYSTEM_INSTRUCTIONS.format(
            knowledge_base=KNOWLEDGE_BASE,
            conversation_history=history_text,
            question=query
        )
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for EF Gap Year students."},
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.7,
            max_tokens=600
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
