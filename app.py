import streamlit as st
import os
import glob
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

# Fallback program information (used if content files are not found)
FALLBACK_PROGRAM_INFO = """
EF Gap Year offers several comprehensive programs for students:

1. The Changemaker Program (Fall 2025 & Spring 2026)
   - Focus: Service learning, sustainability, conservation
   - Destinations: Costa Rica, Dominican Republic, Peru, Ecuador, Galapagos
   - Activities include conservation projects, community service, and cultural immersion
   - Duration: 10-week semester program

2. The Pathfinder Program (Fall 2025 & Spring 2026)
   - Focus: Career exploration, cultural immersion, academic discovery
   - Destinations: England, France, Spain, Portugal, Germany, Switzerland, Italy
   - Activities include exploring international cities and introduction to various fields
   - Duration: 10-week semester program

3. The Voyager Program (Fall 2025 & Spring 2026)
   - Focus: Cultural exploration, adventure, conservation
   - Destinations: Australia, Thailand, Japan
   - Activities include exploring natural environments and conservation projects
   - Duration: 10-week semester program

4. The Year Program (2025-2026)
   - Focus: Comprehensive experience (language, service, internship, cultural immersion)
   - Destinations: Multiple international locations
   - Duration: 23-week full academic year program

All programs include 24/7 support, pre-departure assistance, international health insurance, 
and accommodations. Programs may offer college credit options through partner institutions.
"""

# System instructions
SYSTEM_INSTRUCTIONS = """
You are a helpful assistant for prospective EF Gap Year students. Help them prepare for their 
upcoming programs by providing accurate, helpful responses based on the program information.

Guidelines:
1. Answer ONLY questions about EF Gap Year programs using the provided information.
2. Be kind, thorough, clear, helpful, trustworthy, and confidence-inspiring.
3. If you don't have an accurate answer, say: "I am not sure I can provide an accurate answer 
   to that question. I suggest connecting with your human EF Gap Year advisor on this one."
4. For non-EF Gap Year questions, say: "My role is to help you prepare for your EF Gap Year 
   or Semester program, so I'm afraid I cannot help with this particular question."
5. After each response, ask ONE relevant follow-up question.

Program Information:
{program_info}

Student Question: {question}
"""

def load_content_files():
    """Load content from files in the ef_content folder safely"""
    try:
        # Check if ef_content folder exists
        if not os.path.exists('ef_content'):
            st.warning("ef_content folder not found. Using fallback information.")
            return {"fallback": FALLBACK_PROGRAM_INFO}
        
        # Try to load files from the folder
        content_files = glob.glob('ef_content/*.txt')
        
        if not content_files:
            st.warning("No content files found in ef_content folder. Using fallback information.")
            return {"fallback": FALLBACK_PROGRAM_INFO}
        
        # Load content from each file
        content_dict = {}
        for file_path in content_files:
            try:
                file_name = os.path.basename(file_path).replace(".txt", "")
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    content_dict[file_name] = content
            except Exception as e:
                st.warning(f"Error loading {file_path}: {str(e)}")
        
        if not content_dict:
            st.warning("Failed to load any content files. Using fallback information.")
            return {"fallback": FALLBACK_PROGRAM_INFO}
        
        return content_dict
    
    except Exception as e:
        st.warning(f"Error accessing content files: {str(e)}. Using fallback information.")
        return {"fallback": FALLBACK_PROGRAM_INFO}

def get_relevant_content(query, content_dict):
    """Get relevant content based on the query"""
    query_lower = query.lower()
    
    # Check which content is most relevant to the query
    if "fallback" in content_dict:
        # Only fallback content is available
        return content_dict["fallback"]
    
    # Identify potentially relevant content
    relevant_content = ""
    
    # Check for program-specific keywords
    if any(keyword in query_lower for keyword in ["changemaker", "service", "costa rica", "dominican", "peru"]):
        for key, content in content_dict.items():
            if "changemaker" in key.lower():
                relevant_content += f"\n{content}\n"
    
    if any(keyword in query_lower for keyword in ["pathfinder", "europe", "england", "france"]):
        for key, content in content_dict.items():
            if "pathfinder" in key.lower():
                relevant_content += f"\n{content}\n"
    
    if any(keyword in query_lower for keyword in ["voyager", "australia", "thailand", "japan"]):
        for key, content in content_dict.items():
            if "voyager" in key.lower():
                relevant_content += f"\n{content}\n"
    
    if any(keyword in query_lower for keyword in ["year", "full year", "academic year", "23-week"]):
        for key, content in content_dict.items():
            if "year" in key.lower() and "voyager" not in key.lower():
                relevant_content += f"\n{content}\n"
    
    # If no specific content found, use a combination of key files
    if not relevant_content:
        # Get up to 3 random content files as samples
        sample_keys = list(content_dict.keys())[:3]
        for key in sample_keys:
            relevant_content += f"\n{content_dict[key]}\n"
    
    # Limit content length to avoid token issues
    if len(relevant_content) > 15000:
        relevant_content = relevant_content[:15000] + "..."
    
    return relevant_content

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

# Initialize content (only once at startup)
if 'program_content' not in st.session_state:
    st.session_state.program_content = load_content_files()
    st.session_state.content_loaded = True

def get_chatbot_response(query):
    """Get response from OpenAI using program information"""
    try:
        # Get relevant content for the query
        program_info = get_relevant_content(query, st.session_state.program_content)
        
        # Format the prompt
        prompt = SYSTEM_INSTRUCTIONS.format(
            program_info=program_info,
            question=query
        )
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for EF Gap Year students."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
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
                <img class="avatar" src="https://efgapyear.com/wp-content/uploads/2023/09/favicon-32x32.png">
                <div class="message">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)

def main():
    """Main function for the Streamlit app"""
    # Header
    st.title("EF Gap Year Assistant")
    st.markdown("""
    Welcome to the EF Gap Year Assistant! I'm here to help you prepare for your upcoming 
    gap year or semester program. Feel free to ask me any questions about your program,
    travel preparations, or what to expect during your EF Gap Year experience.
    """)
    
    # Display status of content loading
    if st.session_state.get('content_loaded'):
        if "fallback" in st.session_state.program_content:
            st.info("Using basic program information. For more detailed responses, add content files to the 'ef_content' folder.")
        else:
            num_files = len(st.session_state.program_content)
            st.success(f"Loaded {num_files} content files successfully!")
    
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
            response = get_chatbot_response(user_input)
            
        # Add bot response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Force a rerun to update the UI with the new messages
        st.rerun()

if __name__ == "__main__":
    main()
