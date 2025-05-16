import streamlit as st
import os
from dotenv import load_dotenv
import logging
import traceback
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
import requests
from bs4 import BeautifulSoup
import PyPDF2
from io import BytesIO
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

# Setup logging with stream handler to capture logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="EF Gap Year Assistant",
    page_icon="🌎",
    layout="centered"
)

# Constants
PERSIST_DIRECTORY = "ef_gapyear_db"
OPENAI_MODEL = "gpt-3.5-turbo"  # Using GPT-3.5 as a fallback model if GPT-4 isn't available

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

# URLs to scrape
urls = [
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

# System prompt for the chatbot
SYSTEM_PROMPT = """
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

Context: {context}

Chat History: {chat_history}
Student Question: {question}
"""

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

def extract_pdf_content(url):
    """Extract content from PDF files"""
    try:
        response = requests.get(url)
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

def extract_web_content(url):
    """Extract content from web pages"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
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

def scrape_content():
    """Scrape content from all the URLs"""
    all_content = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, url in enumerate(urls):
        status_text.text(f"Scraping {url}...")
        try:
            if url.endswith('.pdf'):
                content = extract_pdf_content(url)
            else:
                content = extract_web_content(url)
                
            if content:
                all_content.append({
                    'source': url, 
                    'content': content
                })
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
        
        # Update progress
        progress = (i + 1) / len(urls)
        progress_bar.progress(progress)
    
    status_text.empty()
    progress_bar.empty()
    
    return all_content

def process_and_store_content(all_content, persist_directory=PERSIST_DIRECTORY):
    """Process and store content in a vector database"""
    status_text = st.empty()
    status_text.text("Processing content...")
    
    try:
        # Combine all content
        documents = []
        for item in all_content:
            # Create chunks with metadata about source
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            chunks = text_splitter.split_text(item['content'])
            for chunk in chunks:
                documents.append({
                    "text": chunk,
                    "metadata": {"source": item['source']}
                })
        
        logger.info(f"Created {len(documents)} chunks from {len(all_content)} sources")
        status_text.text(f"Created {len(documents)} chunks from {len(all_content)} sources. Building vector database...")
        
        # Create embeddings and store in vector DB
        embeddings = OpenAIEmbeddings()
        
        # Create vector store
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        # Create the DB
        logger.info(f"Creating new vector store in {persist_directory}")
        db = Chroma.from_texts(
            texts=texts, 
            embedding=embeddings, 
            metadatas=metadatas,
            persist_directory=persist_directory
        )
        db.persist()
        
        status_text.empty()
        return db
    except Exception as e:
        status_text.empty()
        logger.error(f"Error processing content: {e}")
        raise

def load_retriever(persist_directory=PERSIST_DIRECTORY):
    """Load the vector store retriever"""
    error_container = st.container()
    
    try:
        embeddings = OpenAIEmbeddings()
        
        # Check if directory exists
        if not os.path.exists(persist_directory):
            # If not, scrape the content and create the vector store
            with st.status("Building knowledge base. This might take a few minutes...", expanded=True) as status:
                st.write("Scraping content from EF Gap Year resources...")
                all_content = scrape_content()
                
                if not all_content:
                    status.update(state="error", label="Failed to scrape content")
                    error_container.error("Failed to scrape content from any of the provided URLs. Please check your internet connection.")
                    raise Exception("Failed to scrape content")
                
                st.write(f"Successfully scraped {len(all_content)} resources. Processing content...")
                db = process_and_store_content(all_content, persist_directory)
                status.update(state="complete", label="Knowledge base built successfully!")
        else:
            # Load the existing vector store
            db = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        
        # Create a retriever with search parameters
        retriever = db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}  # Retrieve top 5 most relevant chunks
        )
        
        return retriever
    except Exception as e:
        logger.error(f"Error loading retriever: {str(e)}")
        error_container.error(f"Error loading retriever: {str(e)}")
        error_container.error("Try refreshing the page or check your OpenAI API key settings.")
        
        if "openai" in str(e).lower():
            error_container.error("There appears to be an issue with your OpenAI API key. Please check that it is valid and has enough credits.")
        
        st.code(traceback.format_exc())
        raise

def create_chatbot():
    """Create the chatbot with RAG capabilities"""
    try:
        # Load the retriever
        retriever = load_retriever()
        
        # Set up the language model
        try:
            llm = ChatOpenAI(
                temperature=0.2,
                model=OPENAI_MODEL
            )
        except Exception as model_error:
            logger.warning(f"Error initializing GPT-4 model: {model_error}. Falling back to GPT-3.5-turbo.")
            # Fallback to GPT-3.5 if GPT-4 is not available
            llm = ChatOpenAI(
                temperature=0.2,
                model="gpt-3.5-turbo"
            )
        
        # Create prompt template
        prompt = PromptTemplate(
            input_variables=["context", "chat_history", "question"],
            template=SYSTEM_PROMPT
        )
        
        # Set up memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create the conversational chain
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={"prompt": prompt}
        )
        
        return qa_chain
    except Exception as e:
        logger.error(f"Error creating chatbot: {e}")
        raise

def get_response(chain, query):
    """Get a response from the chatbot"""
    try:
        response = chain({"question": query})
        return response["answer"]
    except Exception as e:
        logger.error(f"Error getting response: {e}")
        
        # Check if it's an API key error
        if "API key" in str(e):
            return "I'm having trouble with my API connection. Please check the API key settings and try again."
        
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
    
    # Display chat messages
    display_messages()
    
    # Initialize chatbot (with better error handling)
    if 'chatbot' not in st.session_state:
        try:
            with st.spinner("Initializing chatbot..."):
                st.session_state.chatbot = create_chatbot()
        except Exception as e:
            st.error(f"Failed to initialize the chatbot: {str(e)}")
            st.error("Check the logs for more details and try refreshing the page.")
            
            # Add debug info in an expander
            with st.expander("Debug Information"):
                st.write("Error details:", str(e))
                st.code(traceback.format_exc())
                st.write("Environment:")
                st.write(f"- OpenAI API Key set: {'Yes' if 'OPENAI_API_KEY' in os.environ else 'No'}")
                st.write(f"- Database directory exists: {'Yes' if os.path.exists(PERSIST_DIRECTORY) else 'No'}")
            
            # Still allow the user to see the chat interface
    
    # Chat input
    user_input = st.chat_input("Type your question here...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        try:
            # Check if chatbot is initialized
            if 'chatbot' in st.session_state:
                # Get response from chatbot
                response = get_response(st.session_state.chatbot, user_input)
            else:
                response = "I'm sorry, the chatbot is not initialized properly. Please try refreshing the page or contact support."
                
            # Add bot response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Force a rerun to update the UI with the new messages
            st.rerun()
        except Exception as e:
            logger.error(f"Error getting response: {e}")
            st.error("Sorry, I encountered an error. Please try again or contact your EF Gap Year advisor.")
            
            # Add error to chat if needed
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "I'm sorry, I encountered a technical issue. Please try again or contact your EF Gap Year advisor for assistance."
            })

if __name__ == "__main__":
    main()
