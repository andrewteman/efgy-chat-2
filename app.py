import streamlit as st
import os
from dotenv import load_dotenv
import logging
import traceback
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import PyPDF2
from io import BytesIO
import re
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

# Constants
MAX_URLS_TO_PROCESS = 5  # Limit initial processing to avoid resource constraints
GPT_MODEL = "gpt-3.5-turbo"  # Using GPT-3.5 for cost and speed

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
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
    .debug-info {
        background-color: #F8F9FA;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 2rem;
        border: 1px solid #DEE2E6;
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
"""

# URLs to scrape (prioritized)
URLS = [
    # Start with most important URLs to ensure we get some content even if process is interrupted
    "https://efgapyear.com/program-guide-the-changemaker-fall-2025-session-1/",
    "https://efgapyear.com/program-guide-the-pathfinder-fall-2025-session-1/",
    "https://efgapyear.com/program-guide-the-voyager-fall-2025-session-1/",
    "https://efgapyear.com/program-guide-the-year-2025-26-session-1/",
    "https://a.storyblok.com/f/234741/x/46a3c53899/socialidentityresourcesfortravelers_2-14-23.pdf",
    # Add more URLs if resources allow
    "https://efgapyear.com/program-guide-the-changemaker-fall-2025-session-2/",
    "https://efgapyear.com/program-guide-the-pathfinder-fall-2025-session-2/",
    "https://efgapyear.com/program-guide-the-voyager-fall-2025-session-2/",
    "https://efgapyear.com/program-guide-the-year-2025-26-session-2/",
    "https://efgapyear.com/program-guide-the-changemaker-spring-2026-session-1/",
    "https://efgapyear.com/program-guide-the-pathfinder-spring-2026-session-1/",
    "https://efgapyear.com/program-guide-the-voyager-spring-2026-session-1/",
    "https://efgapyear.com/program-guide-the-year-2025-26-session-3/",
    "https://efgapyear.com/program-guide-the-changemaker-spring-2026-session-2/",
    "https://efgapyear.com/program-guide-the-pathfinder-spring-2026-session-2/",
    "https://efgapyear.com/program-guide-the-voyager-spring-2026-session-2/"
]

def extract_pdf_content(url, timeout=30):
    """Extract content from PDF files with timeout"""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        pdf_file = BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        
        # Clean the extracted text
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting PDF content from {url}: {e}")
        return ""

def extract_web_content(url, timeout=30):
    """Extract content from web pages with timeout"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        logger.error(f"Error extracting web content from {url}: {e}")
        return ""

def fetch_content(max_urls=MAX_URLS_TO_PROCESS):
    """Fetch content from URLs with progress indicators"""
    if "content_cache" not in st.session_state:
        content_collection = []
        
        with st.status("Fetching content from EF Gap Year resources...", expanded=True) as status:
            for i, url in enumerate(URLS[:max_urls]):
                st.write(f"Fetching from {url}...")
                try:
                    if url.endswith('.pdf'):
                        content = extract_pdf_content(url)
                    else:
                        content = extract_web_content(url)
                        
                    if content:
                        content_collection.append({
                            'source': url, 
                            'content': content
                        })
                        st.write(f"✅ Successfully fetched content ({len(content)} characters)")
                    else:
                        st.write(f"⚠️ No content retrieved")
                except Exception as e:
                    st.write(f"❌ Error: {str(e)}")
                
                # Brief pause to prevent rate limiting
                time.sleep(1)
            
            if content_collection:
                status.update(label=f"Fetched content from {len(content_collection)} sources", state="complete")
                st.session_state.content_cache = content_collection
            else:
                status.update(label="Failed to fetch content", state="error")
                st.error("Could not fetch content from any sources. Please try again.")
                return None
    
    return st.session_state.content_cache

def simple_semantic_search(query, content_collection, n=3):
    """Simple semantic search using OpenAI embeddings"""
    try:
        # Create embedding for the query
        query_response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=query
        )
        query_embedding = query_response.data[0].embedding
        
        # Filter content to avoid token limits (simple truncation)
        processed_content = []
        for item in content_collection:
            # Split content into manageable chunks to avoid token limits
            chunks = [item['content'][i:i+4000] for i in range(0, len(item['content']), 4000)]
            for chunk in chunks[:3]:  # Take only first few chunks from each source
                processed_content.append({
                    'source': item['source'],
                    'content': chunk
                })
        
        # Score each content chunk against query (using OpenAI)
        # This is more efficient than computing embeddings for every chunk
        context_scoring_prompt = f"""
        I need to find content relevant to a user query from multiple sources.
        
        Query: {query}
        
        For each piece of content below, provide a relevance score (0-10) where:
        - 10: Directly and completely answers the query
        - 7-9: Contains significant relevant information
        - 4-6: Has some relevant information
        - 1-3: Tangentially related
        - 0: Not relevant at all
        
        Return only the scores, one per line, with no explanations.
        """
        
        contents_to_score = [f"Content {i+1}: {item['content'][:1000]}..." for i, item in enumerate(processed_content)]
        
        # Split into batches to avoid token limits
        batch_size = 5
        all_scores = []
        
        for i in range(0, len(contents_to_score), batch_size):
            batch = contents_to_score[i:i+batch_size]
            scoring_prompt = context_scoring_prompt + "\n\n" + "\n\n".join(batch)
            
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that evaluates document relevance."},
                        {"role": "user", "content": scoring_prompt}
                    ],
                    temperature=0.0
                )
                
                # Parse scores (expecting one number per line)
                score_text = response.choices[0].message.content.strip()
                scores = []
                for line in score_text.split('\n'):
                    try:
                        score = float(line.strip())
                        scores.append(score)
                    except:
                        continue
                
                # Pad with zeros if parsing failed
                scores = scores + [0] * (len(batch) - len(scores))
                all_scores.extend(scores)
            except Exception as e:
                logger.error(f"Error scoring batch {i}: {e}")
                # If scoring fails, assign zero scores to the batch
                all_scores.extend([0] * len(batch))
        
        # Pad with zeros if we have fewer scores than content items
        all_scores = all_scores + [0] * (len(processed_content) - len(all_scores))
        
        # Pair scores with content
        scored_content = [
            {**processed_content[i], 'score': score}
            for i, score in enumerate(all_scores) if i < len(processed_content)
        ]
        
        # Sort by score and take top n
        top_content = sorted(scored_content, key=lambda x: x['score'], reverse=True)[:n]
        
        return top_content
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        # Return a subset of content as fallback
        return content_collection[:n] if content_collection else []

def get_chatbot_response(query, chat_history=None):
    """Get response from the chatbot using relevant content"""
    if chat_history is None:
        chat_history = []
    
    try:
        # Initialize content if not already done
        content_collection = fetch_content()
        if not content_collection:
            return "I'm having trouble accessing information about EF Gap Year programs. Please try again later or contact your EF Gap Year advisor."
        
        # Fetch relevant content
        relevant_content = simple_semantic_search(query, content_collection)
        
        # Prepare context from relevant content
        context = "\n\n".join([
            f"Content from {item['source']}:\n{item['content']}"
            for item in relevant_content
        ])
        
        # Prepare chat history for context
        formatted_history = ""
        for msg in chat_history[-6:]:  # Include last 6 messages at most
            role = "Student" if msg["role"] == "user" else "Assistant"
            formatted_history += f"{role}: {msg['content']}\n\n"
        
        # Create the complete prompt
        prompt = f"""
{SYSTEM_INSTRUCTIONS}

CONTEXT INFORMATION:
{context}

CONVERSATION HISTORY:
{formatted_history}

Student Question: {query}

Your response:
"""
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for EF Gap Year students."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error getting chatbot response: {e}")
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
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Initialize content on first load
    if 'initialized' not in st.session_state:
        try:
            with st.spinner("Initializing, please wait..."):
                # This will trigger content fetching and caching
                fetch_content()
                st.session_state.initialized = True
        except Exception as e:
            st.error(f"Initialization error: {str(e)}")
            st.session_state.initialized = False
    
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
