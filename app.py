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

# System instructions
SYSTEM_INSTRUCTIONS = """
You are a helpful assistant for prospective EF Gap Year students. Your role is to help them prepare for their 
upcoming gap year or semester programs by providing quick, accurate, and helpful responses based on the 
information from approved EF Gap Year resources.

Guidelines:
1. ONLY answer questions about EF Gap Year programs using ONLY the information from the provided context.
2. Your tone should be kind, thorough (but clear), helpful, trustworthy, and confidence-inspiring.
3. Remember, these are nervous students who are about to embark on a grand trip around the world, and their nerves are high.
4. Under NO circumstances should your responses be fabricated or misleading.
5. If you are not confident that you have an accurate answer to a student's question, respond with:
   "I am not sure I can provide an accurate answer to that question. I suggest connecting with your human EF Gap Year advisor on this one."
6. If a user asks any question that is NOT about an EF Gap Year program, politely respond with:
   "My role is to help you to prepare for your EF Gap Year or Semester program, so I am afraid I cannot help with this particular question."
7. After each response, ask ONE relevant follow-up question to further engage the student in conversation.
8. Your follow-up question should allow them to expand on their initial query, request more information, or ensure they're receiving necessary information.

Context Information:
{context}

Conversation History:
{conversation}

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

def load_ef_content():
    """Load EF Gap Year content from text files"""
    # Check if content is already loaded in session state
    if "ef_content" not in st.session_state:
        content_dict = {}
        
        # Look for text files in the 'ef_content' directory
        try:
            content_files = glob.glob("ef_content/*.txt")
            
            if not content_files:
                st.warning("No content files found. Please make sure you've added the text files to the 'ef_content' directory.")
                # Return a minimal content dictionary with instructions
                return {
                    "missing_content": "No EF Gap Year content files found. Please follow the setup instructions."
                }
            
            # Load each file
            for file_path in content_files:
                try:
                    file_name = os.path.basename(file_path).replace(".txt", "")
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        content_dict[file_name] = content
                except Exception as e:
                    st.error(f"Error loading {file_path}: {str(e)}")
            
            st.session_state.ef_content = content_dict
        except Exception as e:
            st.error(f"Error loading content files: {str(e)}")
            return {
                "error": f"Error loading content: {str(e)}"
            }
    
    return st.session_state.ef_content

def get_relevant_content(query, content_dict, max_chunks=5, chunk_size=2000):
    """Get most relevant content chunks for the query"""
    # If there's an error or missing content, return that message
    if "error" in content_dict or "missing_content" in content_dict:
        return next(iter(content_dict.values()))
    
    # Simple keyword-based relevance scoring
    query_lower = query.lower()
    scored_chunks = []
    
    # Keywords for different program types
    keywords = {
        "changemaker": ["changemaker", "service", "sustainability", "conservation", "costa rica", "dominican", "peru", "ecuador", "galapagos"],
        "pathfinder": ["pathfinder", "europe", "england", "france", "spain", "portugal", "germany", "switzerland", "italy"],
        "voyager": ["voyager", "australia", "thailand", "japan", "adventure", "exploration"],
        "year": ["year program", "full year", "academic year", "gap year", "23-week", "23 week"],
        "general": ["preparation", "packing", "visa", "safety", "accommodation", "meals", "flight", "budget", "money", "credit", "college"]
    }
    
    # Determine which program types are most relevant
    program_scores = {}
    for program, program_keywords in keywords.items():
        score = sum(1 for keyword in program_keywords if keyword in query_lower)
        program_scores[program] = score
    
    # Get relevant programs (those with score > 0, or all if none have score > 0)
    relevant_programs = [p for p, s in program_scores.items() if s > 0]
    if not relevant_programs:
        relevant_programs = list(keywords.keys())
    
    # Add 'general' if it's not already included
    if "general" not in relevant_programs:
        relevant_programs.append("general")
    
    # Get all content chunks from relevant programs
    all_chunks = []
    for file_name, content in content_dict.items():
        if any(program in file_name.lower() for program in relevant_programs):
            # Split content into chunks
            content_chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            all_chunks.extend([(file_name, chunk) for chunk in content_chunks])
    
    # If specific program not found, use all content
    if not all_chunks:
        for file_name, content in content_dict.items():
            content_chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            all_chunks.extend([(file_name, chunk) for chunk in content_chunks])
    
    # Simple scoring: count occurrences of query words in chunks
    query_words = set(query_lower.split())
    for file_name, chunk in all_chunks:
        chunk_lower = chunk.lower()
        score = sum(1 for word in query_words if word in chunk_lower)
        scored_chunks.append((file_name, chunk, score))
    
    # Sort by score and take top chunks
    scored_chunks.sort(key=lambda x: x[2], reverse=True)
    top_chunks = scored_chunks[:max_chunks]
    
    # Format the context with file names
    context_text = ""
    for file_name, chunk, _ in top_chunks:
        context_text += f"--- From {file_name} ---\n{chunk}\n\n"
    
    return context_text

def get_chatbot_response(query, conversation_history):
    """Get response from OpenAI with relevant context"""
    try:
        # Load content
        content_dict = load_ef_content()
        
        # Get relevant content
        relevant_context = get_relevant_content(query, content_dict)
        
        # Format conversation history
        conversation_text = ""
        for message in conversation_history[-6:]:  # Last 6 messages
            role = "Student" if message["role"] == "user" else "Assistant"
            conversation_text += f"{role}: {message['content']}\n\n"
        
        # Format the prompt
        prompt = SYSTEM_INSTRUCTIONS.format(
            context=relevant_context,
            conversation=conversation_text,
            question=query
        )
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-16k",  # Using the 16k model for longer context
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
    
    # Check for content files
    content_dict = load_ef_content()
    if "missing_content" in content_dict:
        st.warning("""
        ⚠️ EF Gap Year content files not found. Please follow these steps:
        
        1. Create a folder named 'ef_content' in your repository
        2. Save the content from each of your program guide URLs as text files in that folder
        3. Each file should be named descriptively (e.g., 'changemaker-fall-2025.txt')
        4. Push these files to your GitHub repository
        5. Redeploy the app
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
