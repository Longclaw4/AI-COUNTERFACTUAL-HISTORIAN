import streamlit as st
import google.generativeai as genai
import os
import json
import base64
from datetime import datetime


# Using the key provided by the user for this setup:
API_KEY = "AIzaSyDVA-jr9PE55ElskBpDHYRMp553NdK57Q4"

# --- Helper Functions ---
def get_download_link(text_content, filename, link_text):
    """Generate a download link for text content"""
    b64 = base64.b64encode(text_content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def generate_content_with_error_handling(prompt, spinner_text="Generating..."):
    """Calls the Gemini API and handles potential errors."""
    try:
        with st.spinner(spinner_text):
            response = model.generate_content(prompt)
            # Basic check if response has expected attribute
            if hasattr(response, 'text'):
                 # Basic safety check - replace potentially harmful markdown/html patterns
                cleaned_text = response.text.replace('<', '&lt;').replace('>', '&gt;')
                return cleaned_text
            else:
                 # Handle cases where the response might be blocked or empty
                st.warning(f"Received an unexpected response format from the API: {response}")
                # Log the full response for debugging if possible (be careful with sensitive data)
                print(f"DEBUG: Unexpected API Response: {response}") 
                # Check for specific block reasons if available in the response structure
                try:
                    block_reason = response.prompt_feedback.block_reason
                    st.error(f"Content generation blocked. Reason: {block_reason}")
                except AttributeError:
                    st.error("Content generation failed or was blocked. No specific reason provided.")

                return None # Indicate failure
    except Exception as e:
        st.error(f"API Error during generation: {e}")
        st.error(f"Details: {getattr(e, 'message', repr(e))}")
        return None # Indicate failure
#prompt to ai 
def create_engaging_summary(narrative):
    """Creates a clear, engaging summary focusing on key outcomes and possibilities"""
    summary_prompt = f"""
    You're a professional historian who loves making complex ideas simple and exciting. Create a short, powerful summary (2-3 sentences) that:
    1. Starts with the most important outcome or change
    2. Explains why this outcome matters in simple, clear words
    3. Shows how this change affects people's lives
    4. Makes it sound both professional and exciting
    5. Uses everyday words that anyone can understand
    6. Focuses on real, interesting possibilities

    Example style:
    "India becomes the world's richest country, with amazing technology and happy people. Their ancient knowledge mixed with modern ideas creates incredible cities and schools. Everyone wants to visit and learn from India's success story."

    Write it like you're explaining something amazing to a smart friend who wants to understand quickly.

    Narrative: {narrative}
    """
    
    try:
        response = model.generate_content(summary_prompt)
        if hasattr(response, 'text'):
            return response.text.strip()
        return None
    except Exception as e:
        print(f"Error creating summary: {e}")
        return None

# --- Document Types Definition ---
DOCUMENT_TYPES = [
    {
        "id": "newspaper",
        "name": "Breaking News Story", 
        "description": "A front-page news story from the alternate world",
        "prompt_modifier": "Write a short, exciting news story (headline + 1-2 paragraphs) from about 50 years into this alternate world, reporting on a big event or change mentioned in the story. Make it sound like real news from that time."
    },
    {
        "id": "diary",
        "name": "Personal Story", 
        "description": "Someone's personal thoughts and experiences",
        "prompt_modifier": "Write a short diary entry from an ordinary person living about 30-40 years into this alternate world. Show how the changes affect their daily life and feelings. Make it sound real and personal."
    },
    {
        "id": "academic",
        "name": "Research Summary", 
        "description": "A short summary of a study or research paper",
        "prompt_modifier": "Write a short summary (100-150 words) of a research paper written about 70-80 years into this alternate world. The paper should talk about one interesting change (like new technology, politics, or ideas) that came from the different history. Use smart but clear language."
    },
    {
        "id": "letter",
        "name": "Important Letter", 
        "description": "A formal letter between important people",
        "prompt_modifier": "Write a short, official letter between two important people (like leaders or officials) about 60 years into this alternate world. The letter should talk about how things are different now. Use formal but clear language."
    },
    {
        "id": "advertisement", 
        "name": "Cool Ad",
        "description": "An advertisement for something from that world",
        "prompt_modifier": "Create a short ad (with a catchy slogan) for something that would exist in this alternate world about 40-50 years after the change. Show how technology and life are different. Make it sound like a real ad from that time."
    },
    {
        "id": "decree",
        "name": "Official Announcement", 
        "description": "An important law or rule from the government",
        "prompt_modifier": "Write a short announcement of a new law or rule from about 20-30 years into this alternate world. It should be about something important that changed because of the different history. Use official but clear language."
    }
]
#doc render
DOCUMENT_TEMPLATES = {
    "newspaper": """
        <div class="historical-document newspaper">
            <div class="newspaper-header">
                <div class="newspaper-date">ALTERNATE TIMELINE - {year}</div>
                <h1 class="newspaper-title">THE CHRONICLE</h1>
                <div class="newspaper-subtitle">Truth Across Timelines</div>
            </div>
            <div class="newspaper-content">
                <h3 class="headline">{headline}</h3>
                <div class="article-text">{content}</div>
            </div>
        </div>
    """,
    "diary": """
        <div class="historical-document diary">
            <div class="diary-header">
                <div class="diary-date">Date: {date}</div>
            </div>
            <div class="diary-content">
                <p class="diary-text">{content}</p>
                <div class="diary-signature">- {author}</div>
            </div>
        </div>
    """,
    "academic": """
        <div class="historical-document academic">
            <div class="academic-header">
                <h3 class="academic-title">JOURNAL OF {subject}</h3>
                <div class="academic-info">Volume {volume}, Issue {issue} • {year}</div>
            </div>
            <h4 class="abstract-title">ABSTRACT</h4>
            <div class="academic-content">
                <p class="abstract-text">{content}</p>
            </div>
        </div>
    """,
    "letter": """
        <div class="historical-document letter">
            <div class="letter-header">
                <div class="letter-date">{date}</div>
                <div class="letter-address">{sender_address}</div>
            </div>
            <div class="letter-salutation">Dear {recipient},</div>
            <div class="letter-content">
                <p class="letter-text">{content}</p>
            </div>
            <div class="letter-signature">
                <p>Respectfully,</p>
                <p>{sender}</p>
                <p>{title}</p>
            </div>
        </div>
    """,
    "advertisement": """
        <div class="historical-document advertisement">
            <div class="ad-header">
                <h2 class="ad-title">{product_name}</h2>
            </div>
            <div class="ad-content">
                <p class="ad-text">{content}</p>
            </div>
            <div class="ad-slogan">"{slogan}"</div>
            <div class="ad-footer">{manufacturer} • {year}</div>
        </div>
    """,
    "decree": """
        <div class="historical-document decree">
            <div class="decree-seal"></div>
            <div class="decree-header">
                <h2 class="decree-title">BY ORDER OF {authority}</h2>
                <div class="decree-date">{date}</div>
            </div>
            <div class="decree-intro">BE IT KNOWN THAT:</div>
            <div class="decree-content">
                <p class="decree-text">{content}</p>
            </div>
            <div class="decree-signature">
                <p>{ruler_name}</p>
                <p>{title}</p>
            </div>
        </div>
    """
}

#Extract Document Parts ---
def extract_document_parts(doc_type, content):
    """Extract parts from document content for template insertion"""
    parts = {}
    content = content.strip()
    
    current_year = datetime.now().year
    alternate_year = current_year - 100  # Default to 100 years ago
    
    # Common defaults
    parts["content"] = content
    parts["year"] = str(alternate_year)
    parts["date"] = f"{alternate_year % 100}/0{alternate_year % 12}/1{alternate_year % 28}"
    
    # Type-specific defaults and extraction
    if doc_type == "newspaper":
        # Extract headline from first line if possible
        lines = content.split('\n')
        if len(lines) > 0:
            parts["headline"] = lines[0].strip()
            if len(lines) > 1:
                parts["content"] = '\n'.join(lines[1:])
        else:
            parts["headline"] = "BREAKING NEWS"
    
    elif doc_type == "diary":
        parts["author"] = "Anonymous"
    
    elif doc_type == "academic":
        parts["subject"] = "ALTERNATE HISTORY"
        parts["volume"] = str(alternate_year % 50)
        parts["issue"] = str(alternate_year % 12)
    
    elif doc_type == "letter":
        parts["sender"] = "John Smith"
        parts["recipient"] = "Distinguished Sir"
        parts["sender_address"] = "Royal Court, New Britannia"
        parts["title"] = "Minister of Affairs"
    
    elif doc_type == "advertisement":
        # Try to extract product name from content
        lines = content.split('\n')
        products = ["New Invention", "Revolutionary Product", "Modern Marvel"]
        parts["product_name"] = products[alternate_year % len(products)]
        parts["slogan"] = "The Future Is Now"
        parts["manufacturer"] = "Universal Company"
    
    elif doc_type == "decree":
        parts["authority"] = "THE SOVEREIGN COUNCIL"
        parts["ruler_name"] = "Augustus Rex"
        parts["title"] = "Supreme Chancellor"
    
    return parts

# --- Gemini API Setup ---
try:
    genai.configure(api_key=API_KEY)
    # Using a model known for stronger reasoning and generation
    model = genai.GenerativeModel('gemini-1.5-flash') 
except Exception as e:
    st.error(f"Fatal Error: Could not configure Gemini API. Check API Key and permissions. Error: {e}")
    st.stop() # Stop execution if API setup fails

# --- Streamlit App ---
st.set_page_config(
    page_title="AI Counterfactual Historian",
    page_icon="⏳",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* General styling */
    .main-header {text-align: center;}
    .stTabs [data-baseweb="tab-list"] {gap: 24px;}
    .stTabs [data-baseweb="tab"] {height: 50px; white-space: pre-wrap;}
    .preset-btn {margin-bottom: 8px;}
    
    /* Document styling */
    .historical-document {
        border: 1px solid #8B7D6B;
        border-radius: 2px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
        background-color: #F8F3E6;
        color: #2C1E0F;
        font-family: 'Times New Roman', serif;
        position: relative;
        overflow: hidden;
    }
    
    /* Newspaper styling */
    .newspaper {
        background-color: #F2E8D5;
        font-family: 'Times New Roman', serif;
    }
    .newspaper:before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAMAAAAp4XiDAAAAUVBMVEWFhYWDg4N3d3dtbW17e3t1dXWBgYGHh4d5eXlzc3OLi4ubm5uVlZWPj4+NjY19fX2JiYl/f39ra2uRkZGZmZlpaWmXl5dvb29xcXGTk5NnZ2c4zIgwAAAAG3RSTlNAQEAwEAvLIy8NDnFEIVgkJjBWVxQUJEwtMU0AQHK4AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAX0lEQVQ4y92TSwKAIAxDi3j/cX0Gff+bKowMCDMt2LWEvTYNGGMMBwQduA7vQOcQYpELEG0yAXKR86Gm0r5C1M6SoDoXKXuJ7qxEZKPVZikPk6mWpDpQJevTelDz7jfX5QGTLje9/QAAAABJRU5ErkJggg==');
        opacity: 0.1;
        z-index: 0;
    }
    .newspaper-header {
        text-align: center;
        border-bottom: 2px solid #000;
        margin-bottom: 15px;
        padding-bottom: 10px;
        position: relative;
        z-index: 1;
    }
    .newspaper-title {
        font-size: 36px;
        margin: 5px 0;
        font-weight: 900;
        letter-spacing: 2px;
    }
    .newspaper-date, .newspaper-subtitle {
        font-size: 14px;
    }
    .headline {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 10px;
        text-align: center;
        position: relative;
        z-index: 1;
    }
    .article-text {
        column-count: 2;
        column-gap: 20px;
        position: relative;
        z-index: 1;
        text-align: justify;
        line-height: 1.5;
    }
    
    /* Diary styling */
    .diary {
        background-color: #F5E7C1;
        font-family: 'Brush Script MT', cursive;
    }
    .diary:before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAMAAAAp4XiDAAAAflBMVEVmZmZycnJ7e3t0dHRoaGhsbGx4eHhubm5qampiYmJgYGBaWlpeXl5cXFxkZGRISEhQUFBVVVVYWFhEREROTk5MTExCQkI+Pj5HR0dXV1c0NDQ6OjpAQEA2NjYyMjI4ODhLS0swMDBTU1MuLi4sLCwqKiomJiYkJCQiIiIeHh4c7aYvAAAAG3RSTlNAQEAwEAvLIy8NDnFEIVgkJjBWVxQUJEwtMU0AQHK4AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAX0lEQVQ4y92TSwKAIAxDi3j/cX0Gff+bKowMCDMt2LWEvTYNGGMMBwQduA7vQOcQYpELEG0yAXKR86Gm0r5C1M6SoDoXKXuJ7qxEZKPVZikPk6mWpDpQJevTelDz7jfX5QGTLje9/QAAAABJRU5ErkJggg==');
        opacity: 0.05;
        z-index: 0;
    }
    .diary-header {
        text-align: right;
        margin-bottom: 20px;
    }
    .diary-content {
        font-size: 18px;
        line-height: 1.5;
    }
    .diary-signature {
        text-align: right;
        margin-top: 15px;
        font-size: 22px;
    }
    
    /* Academic styling */
    .academic {
        background-color: #FFFFFF;
        font-family: 'Times New Roman', serif;
    }
    .academic-header {
        text-align: center;
        margin-bottom: 20px;
    }
    .academic-title {
        font-weight: bold;
        letter-spacing: 1px;
    }
    .abstract-title {
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
    .abstract-text {
        text-align: justify;
        line-height: 1.5;
    }
    
    /* Letter styling */
    .letter {
        background-color: #F5E7C1;
        font-family: 'Baskerville', serif;
    }
    .letter:before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAMAAAAp4XiDAAAAe1BMVEX///8zMzM5OTk9PT1BQUFFRUVJSUU1NTXr6+vv7+/z8/P39/f7+/vn5+dhYWFZWVlVVVVRUVFNTU3j4+Pb29vX19fPz8/Ly8vHx8fDw8O/v7+7u7u3t7ezs7Ovr6+rq6unp6ejo6Ofn5+bm5uXl5eTk5OPj4+Li4uHh4d9gvOXAAAAFnRSTlMAAgMGCgwOEBIVGR4iJDM8RFRsfoCfS/W4VwAAAQlJREFUSMftlMsSgyAMRbmKgGJtfdXaR9r6/1/YRUIQI8PeuXA2k5CTuUkA/lQUXJZnuc8O7Uzy8mD9qGtZluue9ay5JlZAT4IQmrRzL8TA9o2gkAJCCChZH95lG09vY0yjwGjRH4KOUXuw54U/BFXbz4Qu+qlBwMJpXpyDYZb2qftI9QQOBEeZ+SgQbHUoiEjnSrPRgZDS6WzXwnSP/dXI7B1jhg46H0qHQP0fS+GDErsqGEHJlkQgkLcpCgLxzZ8EPWSJnAm6IYqLzzMEN8QJyrMTRCyEUP+KIeKjf8sQMSXxfc4TJPdHfA+J70e5P3ItQAyKCCN+QMgYg8sIrTXUCO2BsXtCPYb+TX0C1n4v+mD0+/IAAAAASUVORK5CYII=');
        opacity: 0.05;
        z-index: 0;
    }
    .letter-header {
        text-align: right;
        margin-bottom: 30px;
    }
    .letter-salutation {
        margin-bottom: 20px;
    }
    .letter-content {
        text-align: justify;
        margin-bottom: 30px;
        line-height: 1.5;
    }
    .letter-signature {
        text-align: right;
    }
    
    /* Advertisement styling */
    .advertisement {
        background-color: #FCF5E5;
        font-family: 'Arial', sans-serif;
        text-align: center;
    }
    .advertisement:before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAMAAAAp4XiDAAAAe1BMVEX///8zMzM5OTk9PT1BQUFFRUVJSUU1NTXr6+vv7+/z8/P39/f7+/vn5+dhYWFZWVlVVVVRUVFNTU3j4+Pb29vX19fPz8/Ly8vHx8fDw8O/v7+7u7u3t7ezs7Ovr6+rq6unp6ejo6Ofn5+bm5uXl5eTk5OPj4+Li4uHh4d9gvOXAAAAFnRSTlMAAgMGCgwOEBIVGR4iJDM8RFRsfoCfS/W4VwAAAQlJREFUSMftlMsSgyAMRbmKgGJtfdXaR9r6/1/YRUIQI8PeuXA2k5CTuUkA/lQUXJZnuc8O7Uzy8mD9qGtZluue9ay5JlZAT4IQmrRzL8TA9o2gkAJCCChZH95lG09vY0yjwGjRH4KOUXuw54U/BFXbz4Qu+qlBwMJpXpyDYZb2qftI9QQOBEeZ+SgQbHUoiEjnSrPRgZDS6WzXwnSP/dXI7B1jhg46H0qHQP0fS+GDErsqGEHJlkQgkLcpCgLxzZ8EPWSJnAm6IYqLzzMEN8QJyrMTRCyEUP+KIeKjf8sQMSXxfc4TJPdHfA+J70e5P3ItQAyKCCN+QMgYg8sIrTXUCO2BsXtCPYb+TX0C1n4v+mD0+/IAAAAASUVORK5CYII=');
        opacity: 0.08;
        z-index: 0;
    }
    .ad-header {
        margin-bottom: 15px;
    }
    .ad-title {
        font-size: 32px;
        font-weight: bold;
        color: #8B0000;
        text-transform: uppercase;
    }
    .ad-content {
        margin: 20px 0;
        font-size: 16px;
    }
    .ad-slogan {
        font-style: italic;
        font-weight: bold;
        color: #8B0000;
        margin: 20px 0;
        font-size: 20px;
    }
    .ad-footer {
        margin-top: 15px;
        font-size: 12px;
    }
    
    /* Decree styling */
    .decree {
        background-color: #F0E2C4;
        font-family: 'Baskerville', serif;
        border: 8px double #8B7D6B;
        position: relative;
    }
    .decree:before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAMAAAAp4XiDAAAAflBMVEVmZmZycnJ7e3t0dHRoaGhsbGx4eHhubm5qampiYmJgYGBaWlpeXl5cXFxkZGRISEhQUFBVVVVYWFhEREROTk5MTExCQkI+Pj5HR0dXV1c0NDQ6OjpAQEA2NjYyMjI4ODhLS0swMDBTU1MuLi4sLCwqKiomJiYkJCQiIiIeHh4c7aYvAAAAG3RSTlNAQEAwEAvLIy8NDnFEIVgkJjBWVxQUJEwtMU0AQHK4AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAX0lEQVQ4y92TSwKAIAxDi3j/cX0Gff+bKowMCDMt2LWEvTYNGGMMBwQduA7vQOcQYpELEG0yAXKR86Gm0r5C1M6SoDoXKXuJ7qxEZKPVZikPk6mWpDpQJevTelDz7jfX5QGTLje9/QAAAABJRU5ErkJggg==');
        opacity: 0.1;
        z-index: 0;
    }
    .decree-seal {
        position: absolute;
        top: 10px;
        right: 10px;
        width: 80px;
        height: 80px;
        background-color: #8B0000;
        border-radius: 50%;
        border: 2px solid #000;
        z-index: 1;
    }
    .decree-seal:before {
        content: "SEAL";
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: #F0E2C4;
        font-size: 12px;
    }
    .decree-header {
        text-align: center;
        margin-bottom: 20px;
    }
    .decree-title {
        font-size: 24px;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }
    .decree-intro {
        font-weight: bold;
        text-align: center;
        margin-bottom: 15px;
    }
    .decree-content {
        line-height: 1.5;
        text-align: justify;
        margin-bottom: 30px;
    }
    .decree-signature {
        text-align: center;
        font-style: italic;
    }

    /* Document controls explanation */
    .help-text {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .help-text h4 {
        margin-top: 0;
        margin-bottom: 10px;
    }
    .help-item {
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- App Header ---
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown("<h1 class='main-header'>✨ Time Machine Stories & Documents</h1>", unsafe_allow_html=True)
    st.markdown("<p class='main-header'>See what might have happened if history went differently</p>", unsafe_allow_html=True)


if 'narrative' not in st.session_state:
    st.session_state.narrative = None
if 'documents' not in st.session_state:
    st.session_state.documents = {}
if 'current_question' not in st.session_state:
    st.session_state.current_question = ""
if 'generation_completed' not in st.session_state:
    st.session_state.generation_completed = False
if 'processing' not in st.session_state:
    st.session_state.processing = False

# --- Sidebar Controls ---
with st.sidebar:
    st.header("Document Controls")
    
    # Document selection (only shown if not processing)
    if not st.session_state.processing:
        st.subheader("Select Documents to Generate")
        selected_docs = []
        
        # Create checkboxes for document types
        for doc in DOCUMENT_TYPES:
            doc_selected = st.checkbox(
                f"{doc['name']}", 
                value=True,  # Default all selected
                help=doc['description']
            )
            if doc_selected:
                selected_docs.append(doc['id'])
        
        # Error if none selected
        if not selected_docs:
            st.warning("Please select at least one document type")
    
    # Controls explanation
    with st.expander("❓ How to Use This Tool"):
        st.markdown("""
        <div class="help-text">
            <h4>Quick Guide:</h4>
            <div class="help-item">
                <b>Choose Documents:</b> Pick which types of stories you want to see from the alternate world.
            </div>
            <div class="help-item">
                <b>Breaking News:</b> A front-page story about big events in this different world.
            </div>
            <div class="help-item">
                <b>Personal Story:</b> A diary entry showing how ordinary people lived in this world.
            </div>
            <div class="help-item">
                <b>Research Summary:</b> A smart person's study about how things changed.
            </div>
            <div class="help-item">
                <b>Important Letter:</b> A formal message between leaders in this different world.
            </div>
            <div class="help-item">
                <b>Cool Ad:</b> An advertisement showing new products in this world.
            </div>
            <div class="help-item">
                <b>Official Announcement:</b> A new law or rule showing how the government changed.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Download options (only shown after generation)
    if st.session_state.generation_completed:
        st.subheader("Download Results")
        
        # Option to download everything as JSON
        if st.button("Download All Results (JSON)"):
            data = {
                "question": st.session_state.current_question,
                "narrative": st.session_state.narrative,
                "documents": st.session_state.documents,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            json_str = json.dumps(data, indent=2)
            filename = f"alternate_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            st.markdown(get_download_link(json_str, filename, "📥 Click here to download"), unsafe_allow_html=True)
            
        # Option to download just the narrative
        if st.button("Download Narrative Text"):
            filename = f"narrative_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            st.markdown(get_download_link(st.session_state.narrative, filename, "📥 Click here to download"), unsafe_allow_html=True)

# --- Main Content Area ---
col1, col2 = st.columns([4, 1])

# Add preset questions section
st.subheader("Try these fun questions or make up your own:")
preset_questions = [
    "What if Gandhi stopped Godse?",
    "What if the Library of Alexandria was saved?",
    "What if the Mongols took over Europe?",
    "What if the Byzantine Empire survived?",
    "What if America stayed British?",
    "What if China invented the printing press first?"
]

# Create preset buttons in 3 columns for better layout
preset_cols = st.columns(3)
for i, question in enumerate(preset_questions):
    with preset_cols[i % 3]:
        if st.button(question, key=f"preset_{i}", use_container_width=True, disabled=st.session_state.processing):
            # Set this preset as the current question
            what_if_question = question
            # Update the text area 
            st.session_state.question_input = question

with col1:
    what_if_question = st.text_area(
        "What's your 'what if' question?",
        height=80,
        placeholder="Example: What if Rome never fell? What if the Bronze Age never ended? What if Ada Lovelace worked with Babbage?",
        key="question_input",
        disabled=st.session_state.processing
    )

with col2:
    st.write("") # Add vertical space
    generate_button = st.button(
        "Create Alternate World!", 
        use_container_width=True,
        disabled=st.session_state.processing
    )

# --- Generation Logic ---
if generate_button and what_if_question:
    # Basic validation
    if len(what_if_question) < 10:
        st.error("Please enter a more detailed question (at least 10 characters)")
    elif not selected_docs:
        st.error("Please select at least one document type in the sidebar")
    else:
        # Set processing state
        st.session_state.processing = True
        st.session_state.generation_completed = False
        
        # Reset state if a new question is asked
        if what_if_question != st.session_state.current_question:
            st.session_state.narrative = None
            st.session_state.documents = {}
            st.session_state.current_question = what_if_question
        
        # Create progress bar
        progress_bar = st.progress(0)
        
        # 1. Generate Narrative
        narrative_prompt = f"""
        You are a meticulous historian specializing in counterfactual reasoning. Analyze the following 'what if' scenario:

        '{what_if_question}'

        Generate a plausible and engaging narrative outlining the key consequences and divergences from our known history. Focus on the major political, technological, social, and cultural impacts in the first 50-100 years following the point of divergence. Be creative but maintain historical plausibility. Structure the output clearly, perhaps chronologically or thematically. Ensure the narrative provides enough detail to inspire the creation of specific documents later. End with a concise summary paragraph of the key changes.
        """
        
        with st.status("Stage 1: Reasoning about alternate timelines...") as status:
            st.session_state.narrative = generate_content_with_error_handling(
                narrative_prompt, 
                "Analyzing historical divergence patterns..."
            )
            progress_bar.progress(30)
            
            if st.session_state.narrative:
                status.update(label="Narrative generated successfully!", state="complete")
            else:
                status.update(label="Failed to generate narrative", state="error")
                st.session_state.processing = False
                st.error("Could not generate the alternate timeline narrative. Please try a different question or check API connectivity.")
                st.stop()
        
        # 2. Generate Documents
        if st.session_state.narrative:
            st.session_state.documents = {}  # Reset documents
            selected_doc_types = [doc for doc in DOCUMENT_TYPES if doc['id'] in selected_docs]
            total_docs = len(selected_doc_types)
            
            if total_docs > 0:
                with st.status("Stage 2: Forging historical documents...") as status:
                    for i, doc_type in enumerate(selected_doc_types):
                        status.update(label=f"Forging {doc_type['name']}...")
                        
                        doc_prompt = f"""
                        CONTEXT: The following narrative describes an alternate history based on the premise '{what_if_question}':
                        --- NARRATIVE START ---
                        {st.session_state.narrative}
                        --- NARRATIVE END ---

                        TASK: Based only on the context provided in the narrative above, {doc_type['prompt_modifier']}
                        Ensure the generated text is distinct from the narrative itself but clearly reflects the described alternate reality. Do not add any commentary about the task itself, just generate the document.
                        """
                        
                        generated_doc = generate_content_with_error_handling(
                            doc_prompt,
                            f"Creating {doc_type['name']}..."
                        )
                        
                        if generated_doc:
                            st.session_state.documents[doc_type['id']] = {
                                "name": doc_type['name'],
                                "content": generated_doc.strip(),
                                "description": doc_type['description']
                            }
                        
                        # Update progress
                        progress_value = 30 + (i + 1) * (70 / total_docs)
                        progress_bar.progress(int(progress_value))
                    
                    status.update(label="All documents generated!", state="complete")
            
            # Mark generation as complete
            st.session_state.generation_completed = True
            st.session_state.processing = False
            
            # Force a rerun to show results - fixed deprecated experimental_rerun
            st.rerun()

elif generate_button and not what_if_question:
    st.warning("Please enter a 'what if' question.")

# --- Display Results ---
if st.session_state.narrative and st.session_state.generation_completed:
    # Hide the progress bar if complete
    if 'progress_bar' in locals():
        progress_bar.empty()
    
    tab1, tab2 = st.tabs(["📜 The Story", "Cool Documents"])
    
    with tab1:
        st.markdown("### The Story")
        
        if st.session_state.narrative:
            # Generate and show the engaging summary
            summary = create_engaging_summary(st.session_state.narrative)
            
            if summary:
                st.markdown(f"""
                <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
                    <h3 style='color: #2c3e50;'>{summary}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Add expand button
                if st.button("✨ Show Full Story", key="expand_narrative"):
                    st.markdown("### Full Story")
                    st.markdown(st.session_state.narrative)
            else:
                # Fallback if summary generation fails
                st.markdown(st.session_state.narrative)
        else:
            st.info("No story generated yet. Ask a 'what if' question to create an alternate world!")
    
    with tab2:
        if st.session_state.documents:
            # Create a grid layout for documents
            doc_count = len(st.session_state.documents)
            
            if doc_count > 0:
                # Display each document with its template
                for doc_id, doc_data in st.session_state.documents.items():
                    st.subheader(doc_data['name'])
                    
                    # Get document content
                    content = doc_data['content']
                    
                    # Get template based on document type
                    if doc_id in DOCUMENT_TEMPLATES:
                        # Extract parts from content
                        parts = extract_document_parts(doc_id, content)
                        
                        # Fill template with extracted parts
                        template = DOCUMENT_TEMPLATES[doc_id]
                        try:
                            formatted_doc = template.format(**parts)
                            st.markdown(formatted_doc, unsafe_allow_html=True)
                        except KeyError as e:
                            # Fallback if template keys missing
                            st.markdown(f"""
                            <div class="historical-document">
                                <h3>{doc_data['name']}</h3>
                                <p>{content}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="historical-document">
                            <h3>{doc_data['name']}</h3>
                            <p>{content}</p>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("No documents have been generated yet. Select document types in the sidebar and generate the alternate history.")

# --- Footer ---
st.divider()
st.caption("Note: All stories and documents are made-up by AI based on your question. They're for fun and learning, not real history.")