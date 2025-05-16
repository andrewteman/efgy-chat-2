import streamlit as st
import os
import requests
from bs4 import BeautifulSoup
import time
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
    .debug-box {
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 4px;
        margin: 10px 0;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# Initial knowledge base with comprehensive information
KNOWLEDGE_BASE = """
EF Gap Year offers several comprehensive programs for students looking to take a gap year before starting or continuing college. Here's detailed information about each program:

1. THE CHANGEMAKER PROGRAM (Fall 2025 & Spring 2026)
   Focus: Language learning, service learning, and leadership development
   
   Fall 2025 Session 1 (September-December 2025):
   - Destinations: Start in London, then study language in Paris or Barcelona, followed by service learning in Costa Rica or Dominican Republic
   - Modules: Leadership, Language Learning, Service Learning
   - Activities include: Leadership workshop in London, language study in Paris/Barcelona, volunteer projects in Costa Rica/Dominican Republic
   - Accommodations: Student residence in London, homestay during language study, share apartments during service learning
   - Program fee: $15,990 (not including flights)

   Fall 2025 Session 2 (January-April 2026):
   - Similar structure to Session 1 with potential seasonal variations
   - Program fee: $15,990 (not including flights)
   
   Spring 2026 Sessions follow a similar structure
   - Each module includes excursions, cultural activities, and 24/7 staff support
   - 12 college credits available through Southern New Hampshire University

2. THE PATHFINDER PROGRAM (Fall 2025 & Spring 2026)
   Focus: Language study, internship placements, and cultural immersion
   
   Fall 2025 Session 1 (September-December 2025):
   - Destinations: Start in London, then language study in Paris, Tokyo or Florence, followed by an international internship
   - Modules: Leadership, Language Learning, Internship
   - Activities include: Leadership workshop in London, immersive language learning, professional internship placement
   - Accommodations: Student residence in London, homestay during language study, share apartments during internship
   - Program fee: $16,390 (not including flights)
   
   Fall 2025 Session 2 (January-April 2026):
   - Similar structure with potential seasonal variations
   - Program fee: $16,390 (not including flights)
   
   Spring 2026 Sessions follow a similar structure
   - Internships available in various fields including business, marketing, tourism, education, etc.
   - 12 college credits available through Southern New Hampshire University

3. THE VOYAGER PROGRAM (Fall 2025 & Spring 2026)
   Focus: Multi-destination cultural exploration and adventure
   
   Fall 2025 Session 1 (September-December 2025):
   - Destinations: Start in London, then travel to Peru and Costa Rica, followed by an optional module in Japan or Europe
   - Modules: Leadership, Global Explorer, additional optional module
   - Activities include: Leadership workshop in London, exploring Machu Picchu, whitewater rafting, surfing lessons, cultural immersion
   - Accommodations: Student residences and hotels
   - Program fee: $16,990 (not including flights)
   
   Fall 2025 Session 2 (January-April 2026):
   - Similar structure with potential seasonal variations
   - Program fee: $16,990 (not including flights)
   
   Spring 2026 Sessions follow a similar structure
   - Includes guided excursions, adventure activities, and cultural experiences
   - 12 college credits available through Southern New Hampshire University

4. THE YEAR PROGRAM (2025-2026)
   Focus: Comprehensive gap year experience combining elements of all programs
   
   2025-2026 Academic Year (September 2025-April 2026):
   - Multiple destinations across Europe, Latin America, and Asia
   - Modules include: Leadership, Language Learning, Service Learning, Cultural Exploration, and International Internship
   - Complete gap year experience with language study, service learning, and professional internship
   - Accommodations vary by module: student residences, homestays, shared apartments
   - Program fee: $38,500 for full year (not including flights)
   - 18-24 college credits available through Southern New Hampshire University

GENERAL INFORMATION FOR ALL PROGRAMS:

Pre-Departure Preparation:
- Comprehensive pre-departure support including visa guidance, packing lists, cultural preparation
- Online portal with resources and information
- Dedicated EF staff member assigned to each student
- Pre-departure orientation materials and webinars
- Required documents: Valid passport with 6+ months validity beyond program end date
- Most students require visas for certain destinations, which EF helps arrange
- Health preparations: Recommended vaccinations vary by destination
- Travel insurance: Comprehensive travel and health insurance included in program fee

Safety & Support:
- 24/7 emergency support line
- Local EF staff available at all destinations
- Regular check-ins with program leaders
- Comprehensive health and safety protocols
- Professional internships vetted for safety and quality
- All accommodations selected with safety as priority
- Regular group activities and excursions led by experienced staff
- Cultural orientation provided at each new destination

Financial Information:
- Program fees cover: accommodations, some meals, transportation between destinations, activities, excursions, language courses, internship placement, 24/7 support
- Not included: Flights to and from program locations, some meals, personal spending money
- Automatic $500 scholarship for Early Decision applicants
- Additional scholarships available through separate application
- Payment plans available with monthly installments
- Recommended spending money: $100-200 per week depending on destination and lifestyle

Academics & College Credit:
- College credit available through Southern New Hampshire University
- Credits typically transferable to most US institutions
- Credit options: 12 credits for semester programs, 18-24 for year program
- Academic components include reflective essays, projects, language assessments
- Official transcripts provided after program completion
- College counseling services available throughout the program

Accommodations & Meals:
- London: Modern student residence with shared rooms, common areas
- Language destinations: Homestays with local families, breakfast and dinner included
- Service learning: Shared apartments or residence centers
- Internship locations: Shared apartments near work locations
- Some meals included (varies by location and module)
- All accommodations vetted for safety, cleanliness, and location
- WiFi available at all accommodations
- Laundry facilities available at or near all accommodations

Packing Essentials:
- Clothing appropriate for multiple climates and cultural contexts
- Appropriate attire for professional settings (internship module)
- Electrical adapters and converters
- Prescription medications (in original packaging with doctor's note)
- Comfortable walking shoes
- Backpack/day bag for excursions
- Laptop or tablet for academic components
- EF provides detailed packing lists specific to program destinations

Communication:
- WiFi available at all accommodations
- International phone plans recommended or local SIM cards available
- Regular check-ins with program leaders and home
- EF emergency contact line available 24/7
- Apps recommended for international communication

Common Concerns:
- Homesickness: Staff trained to help students adjust, regular group activities to foster community
- Language barriers: No prior language experience required, staff available to assist
- Cultural adjustment: Orientation provided at each destination
- Money management: Guidance provided on budgeting in different economies
- Balance of structure and independence: Programs designed with both group activities and free time
- Making friends: Orientation activities designed to foster connections between participants

Specific Program Features:

Language Learning:
- Accredited language schools with certified instructors
- 20 hours of language instruction per week
- Placement test to determine appropriate level
- Focus on practical communication skills
- Cultural activities integrated into language learning
- Classes typically held Monday-Friday mornings
- Certificate of completion provided

Service Learning:
- Partnerships with local community organizations and NGOs
- Projects focus on education, environmental conservation, community development
- 25-30 hours of service per week
- Orientation and training provided
- Reflection activities to process experiences
- Cultural context and background information provided
- Opportunity to develop specific skills while making meaningful contribution

Leadership Module:
- Based in London with experienced leadership coaches
- Workshops on communication, problem-solving, teamwork
- Personal development planning
- Cultural excursions in London
- Group activities and team-building experiences
- Interactive sessions with guest speakers
- Self-reflection and peer feedback components

Internship Placements:
- Available in various fields: business, marketing, hospitality, media, education, etc.
- Personalized placement process based on interests and experience
- 25-30 hours per week in professional environment
- Regular check-ins with internship coordinator
- Resume and interview coaching prior to placement
- Professional development workshops
- Reference letter provided upon completion

Global Explorer:
- Guided cultural immersion in multiple destinations
- Adventure activities led by qualified instructors
- Cultural workshops and interactive experiences
- Historical site visits with expert guides
- Local transportation and logistics arranged
- Balance of group activities and independent exploration
- Focus on developing global perspective and adaptability
"""

# Advanced System Instructions
SYSTEM_INSTRUCTIONS = """
You are a knowledgeable assistant for prospective EF Gap Year students. Your role is to help them prepare for their 
upcoming gap year or semester programs by providing detailed, accurate, and helpful responses based on the information
provided in the knowledge base.

Guidelines:
1. Answer questions ONLY using information from the knowledge base. If information isn't explicitly provided, admit you don't know 
   and suggest the student contact their EF Gap Year advisor.
2. Your tone should be warm, thorough (but clear), helpful, trustworthy, and confidence-inspiring.
3. Remember, these are nervous students who are about to embark on a grand trip around the world, so be reassuring and positive.
4. Provide specific details whenever possible: dates, locations, costs, activities, etc.
5. Structure your responses clearly, using lists or bullet points for complex information when appropriate.
6. When answering questions about specific programs, provide comprehensive details about that program's structure, destinations, 
   activities, and features.
7. If you are not confident that you have an accurate answer, respond with:
   "I am not sure I can provide a complete answer to that question. I suggest connecting with your human EF Gap Year advisor on this one."
8. If a user asks any question that is NOT about an EF Gap Year program, politely respond with:
   "My role is to help you prepare for your EF Gap Year or Semester program, so I'm afraid I cannot help with this particular question."
9. After each response, ask ONE relevant follow-up question that naturally extends the conversation. Make this question specific 
   to what the student has asked about, not generic.

Knowledge Base:
{knowledge_base}

Conversation History:
{conversation_history}

Student Question: {question}
"""

# URLs for optional dynamic content enrichment
PROGRAM_URLS = {
    "changemaker_fall1": "https://efgapyear.com/program-guide-the-changemaker-fall-2025-session-1/",
    "pathfinder_fall1": "https://efgapyear.com/program-guide-the-pathfinder-fall-2025-session-1/",
    "voyager_fall1": "https://efgapyear.com/program-guide-the-voyager-fall-2025-session-1/",
    "year_1": "https://efgapyear.com/program-guide-the-year-2025-26-session-1/"
}

def extract_web_content(url, timeout=10):
    """Extract content from web pages with timeout"""
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
        return text[:15000]  # Limit to 15k characters
    except Exception as e:
        st.error(f"Error fetching content: {str(e)}")
        return ""

def get_additional_content(query):
    """Conditionally fetch additional content based on query keywords"""
    # Only try to fetch additional content for specific program questions
    additional_content = ""
    
    # Check which program the query might be about
    if any(keyword in query.lower() for keyword in ["changemaker", "language", "service"]):
        if "additional_content_changemaker" not in st.session_state:
            with st.spinner("Loading additional program details..."):
                content = extract_web_content(PROGRAM_URLS["changemaker_fall1"])
                if content:
                    st.session_state.additional_content_changemaker = content
        if "additional_content_changemaker" in st.session_state:
            additional_content = st.session_state.additional_content_changemaker
    
    elif any(keyword in query.lower() for keyword in ["pathfinder", "internship"]):
        if "additional_content_pathfinder" not in st.session_state:
            with st.spinner("Loading additional program details..."):
                content = extract_web_content(PROGRAM_URLS["pathfinder_fall1"])
                if content:
                    st.session_state.additional_content_pathfinder = content
        if "additional_content_pathfinder" in st.session_state:
            additional_content = st.session_state.additional_content_pathfinder
    
    elif any(keyword in query.lower() for keyword in ["voyager", "explorer", "adventure"]):
        if "additional_content_voyager" not in st.session_state:
            with st.spinner("Loading additional program details..."):
                content = extract_web_content(PROGRAM_URLS["voyager_fall1"])
                if content:
                    st.session_state.additional_content_voyager = content
        if "additional_content_voyager" in st.session_state:
            additional_content = st.session_state.additional_content_voyager
    
    elif any(keyword in query.lower() for keyword in ["year", "full year", "academic year"]):
        if "additional_content_year" not in st.session_state:
            with st.spinner("Loading additional program details..."):
                content = extract_web_content(PROGRAM_URLS["year_1"])
                if content:
                    st.session_state.additional_content_year = content
        if "additional_content_year" in st.session_state:
            additional_content = st.session_state.additional_content_year
    
    return additional_content

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
    """Get response from the chatbot using knowledge base and optional dynamic content"""
    try:
        # Try to get additional content for specific queries
        additional_content = get_additional_content(query)
        
        # Combine knowledge base with any additional content
        full_knowledge_base = KNOWLEDGE_BASE
        if additional_content:
            full_knowledge_base += "\n\nADDITIONAL PROGRAM DETAILS:\n" + additional_content
        
        # Format conversation history
        history_text = ""
        for msg in conversation_history[-6:]:  # Include up to last 6 messages
            role = "Student" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n\n"
        
        # Format the prompt with all the required information
        formatted_prompt = SYSTEM_INSTRUCTIONS.format(
            knowledge_base=full_knowledge_base,
            conversation_history=history_text,
            question=query
        )
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-16k",  # Using the 16k model for longer context
            messages=[
                {"role": "system", "content": "You are a helpful assistant for EF Gap Year students."},
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.7,
            max_tokens=1000  # Increased token limit for more detailed responses
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
