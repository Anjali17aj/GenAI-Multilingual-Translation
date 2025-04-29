import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import time
import pandas as pd
import PyPDF2
from io import BytesIO
import requests
from bs4 import BeautifulSoup
import base64
from gtts import gTTS  # Google's Text-to-Speech API

# Load environment variables
load_dotenv()

# Configure API key
GOOGLE_API_KEY = os.getenv("GEMINI_API")
genai.configure(api_key=GOOGLE_API_KEY)

# Set up Streamlit page config
st.set_page_config(
    page_title="Language Translator", 
    page_icon="🌐", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subheader {
        font-size: 1.2rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .language-card {
        background-color: #e8f4ff;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border-left: 5px solid #1E88E5;
        color: #333333;
        font-size: 1.1rem;
    }
    
    .language-title {
        color: #1E88E5;
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .footer {
        text-align: center;
        margin-top: 3rem;
        color: #757575;
        font-size: 0.9rem;
    }
    .stButton > button {
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
        width: 100%;
        border-radius: 5px;
    }
    .stTextArea > div > div > textarea {
        border-radius: 5px;
        border: 1px solid #1E88E5;
    }
    
    .audio-button {
        background-color: #FF9800;
        color: white;
    }
    .language-selector {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 0.5rem;
        margin-bottom: 1rem;
    }
    .success-message {
        color: #4CAF50;
        font-weight: bold;
        padding: 0.5rem;
        border-radius: 5px;
        background-color: #f0fff0;
    }
    .error-message {
        color: #f44336;
        font-weight: bold;
        padding: 0.5rem;
        border-radius: 5px;
        background-color: #fff0f0;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0 10px 10px 10px;
        border: 1px solid #e0e0e0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #0d4c94;
        border-radius: 10px 10px 0 0;
        border: 1px solid #e0e0e0;
        border-bottom: none;
        padding: 5px 15px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E88E5 !important;
        color: white !important;
    }
    .input-source {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 0.5rem;
        margin-bottom: 1rem;
        border: 1px solid #dfe1e5;
    }
    .url-input {
        border-radius: 5px;
        border: 1px solid #1E88E5;
    }
    .audio-controls {
        margin-top: 1rem;
        background-color: #f0f7ff;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 3px solid #FF9800;
    }
</style>
""", unsafe_allow_html=True)

# App title and description
st.markdown('<h1 class="main-header">🌐 Multi-Language Translator</h1>', unsafe_allow_html=True)
st.markdown('<p class="subheader">Translate your text between English, Hindi, and Telugu from various sources with audio support</p>', unsafe_allow_html=True)

# Initialize session state for storing translations
if 'translations' not in st.session_state:
    st.session_state.translations = {}
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""
if 'detected_language' not in st.session_state:
    st.session_state.detected_language = None
if 'input_source' not in st.session_state:
    st.session_state.input_source = "text"
if 'audio_files' not in st.session_state:
    st.session_state.audio_files = {}

# Function to generate a download link for an audio file
def get_audio_download_link(audio_bytes, filename="audio.mp3"):
    b64 = base64.b64encode(audio_bytes).decode()
    href = f'<a href="data:audio/mp3;base64,{b64}" download="{filename}">Download audio file</a>'
    return href

# Function to generate audio from text
def text_to_speech(text, language_code):
    try:
        # Map our language names to gTTS language codes
        language_map = {
            "English": "en",
            "Hindi": "hi",
            "Telugu": "te"
        }
        
        # Default to English if language not supported
        lang_code = language_map.get(language_code, "en")
        
        # Create gTTS object - removed length limitation
        tts = gTTS(text=text, lang=lang_code, slow=False)
        
        # Save to BytesIO object
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        
        return audio_bytes.read()
    except Exception as e:
        st.error(f"Error generating audio: {str(e)}")
        return None

# Function to detect language
def detect_language(text):
    try:
        if not text.strip():
            return None
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Identify the language of the following text. 
        Return ONLY ONE of these options: "English", "Hindi", "Telugu", or "Other".
        No explanation, just the language name.
        
        Text: {text}
        """
        
        response = model.generate_content(prompt)
        detected = response.text.strip()
        
        # Validate the response is one of our expected values
        valid_languages = ["English", "Hindi", "Telugu", "Other"]
        if detected not in valid_languages:
            return "Other"
        return detected
        
    except Exception as e:
        st.error(f"Error detecting language: {str(e)}")
        return "Other"

# Define enhanced translation function
def translate_text(text, target_language, source_language="Auto-detect"):
    try:
        if not text.strip():
            return "Please enter text to translate."
            
        # Configure Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Build a more specific prompt based on source and target languages
        if source_language == "Auto-detect":
            prompt = f"""
            Translate the following text to {target_language}.
            Return ONLY the translated text without any explanations or notes.
            
            Text to translate: {text}
            """
        else:
            prompt = f"""
            Translate the following {source_language} text to {target_language}.
            Return ONLY the translated text without any explanations or notes.
            
            Text to translate: {text}
            """
        
        # Generate translation with retry mechanism
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = model.generate_content(prompt)
                translation = response.text.strip()
                
                # Verify we got meaningful content back
                if len(translation) < 2 and len(text) > 10:
                    raise Exception("Translation unusually short, retrying...")
                    
                return translation
                
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    return f"Translation failed after {max_retries} attempts. Please try again."
                time.sleep(1)  # Short delay before retry
        
    except Exception as e:
        return f"Translation error: {str(e)}"

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file.read()))
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return ""

# Function to extract text from CSV
def extract_text_from_csv(csv_file):
    try:
        df = pd.read_csv(csv_file)
        text = ""
        for column in df.columns:
            # Add column name with its first few values
            text += f"{column}: "
            for idx, value in enumerate(df[column].astype(str)):
                if idx < 5:  # Limit to first 5 rows per column
                    text += f"{value}, "
            text += "\n"
        return text
    except Exception as e:
        st.error(f"Error extracting text from CSV: {str(e)}")
        return ""

# Function to extract text from URL - removed length limitation
def extract_text_from_url(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        # Extract text
        text = soup.get_text(separator=' ', strip=True)
        
        return text
    except Exception as e:
        st.error(f"Error extracting text from URL: {str(e)}")
        return ""
  
# Language selection UI with two columns
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="language-selector">', unsafe_allow_html=True)
    input_language = st.selectbox(
        "Input Language:",
        ["Auto-detect", "English", "Hindi", "Telugu", "Other"],
        help="Select the language of your input text"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="language-selector">', unsafe_allow_html=True)
    target_languages = st.multiselect(
        "Languages to translate to:",
        ["English", "Hindi", "Telugu"],
        default=["English", "Hindi", "Telugu"],
        help="Select one or more target languages"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Input source selection
st.markdown('<div class="input-source">', unsafe_allow_html=True)
input_source = st.radio(
    "Select input source:",
    ["Direct Text", "Upload PDF", "Upload CSV", "Enter URL"],
    horizontal=True
)
st.session_state.input_source = input_source
st.markdown('</div>', unsafe_allow_html=True)

# Input based on selected source
source_text = ""
if input_source == "Direct Text":
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    source_text = st.text_area(
        "Enter text to translate:",
        value=st.session_state.input_text if st.session_state.input_source == "Direct Text" else "",
        height=150,
        key="source_input_text",
        help="Type or paste the text you want to translate"
    )
    st.session_state.input_text = source_text
    st.markdown('</div>', unsafe_allow_html=True)
    
elif input_source == "Upload PDF":
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"], help="Upload a PDF file to extract text for translation")
    if pdf_file is not None:
        with st.spinner("Extracting text from PDF..."):
            source_text = extract_text_from_pdf(pdf_file)
            if source_text:
                st.success(f"Successfully extracted {len(source_text)} characters from PDF")
                with st.expander("Preview extracted text"):
                    st.text(source_text[:500] + ("..." if len(source_text) > 500 else ""))
            else:
                st.error("Failed to extract text from PDF")
    st.markdown('</div>', unsafe_allow_html=True)
    
elif input_source == "Upload CSV":
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    csv_file = st.file_uploader("Upload a CSV file", type=["csv"], help="Upload a CSV file to extract text for translation")
    if csv_file is not None:
        with st.spinner("Extracting text from CSV..."):
            source_text = extract_text_from_csv(csv_file)
            if source_text:
                st.success(f"Successfully extracted data from CSV")
                with st.expander("Preview extracted text"):
                    st.text(source_text)
            else:
                st.error("Failed to extract text from CSV")
    st.markdown('</div>', unsafe_allow_html=True)
    
elif input_source == "Enter URL":
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    url = st.text_input("Enter URL:", help="Enter a URL to extract text from the webpage")
    if url:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        with st.spinner("Extracting text from URL..."):
            source_text = extract_text_from_url(url)
            if source_text:
                st.success(f"Successfully extracted {len(source_text)} characters from URL")
                with st.expander("Preview extracted text"):
                    st.text(source_text[:500] + ("..." if len(source_text) > 500 else ""))
            else:
                st.error("Failed to extract text from URL")
    st.markdown('</div>', unsafe_allow_html=True)

# Create columns for the translate button
col_space1, col_btn, col_space2 = st.columns([1, 2, 1])
with col_btn:
    translate_button = st.button("Translate", use_container_width=True)

# Check if translation should be performed
if translate_button and source_text:
    with st.spinner("Processing..."):
        # Detect language if set to auto-detect
        if input_language == "Auto-detect":
            with st.spinner("Detecting language..."):
                # Removed length limitation for language detection
                detected = detect_language(source_text)
                st.session_state.detected_language = detected
                st.info(f"Detected language: {detected}")
        else:
            st.session_state.detected_language = input_language
        
        source_lang = st.session_state.detected_language
        
        # Filter out the source language from targets if it's one of our supported languages
        filtered_targets = [lang for lang in target_languages if lang != source_lang or source_lang == "Other"]
        
        if not filtered_targets:
            st.warning("Please select at least one target language different from your source language.")
        else:
            # Clear previous translations and audio files
            st.session_state.translations = {}
            st.session_state.audio_files = {}
            
            # Removed length limitation for translation
            translation_text = source_text
            
            # Translate to each selected language
            for lang in filtered_targets:
                with st.spinner(f"Translating to {lang}..."):
                    translation = translate_text(translation_text, lang, source_lang)
                    st.session_state.translations[lang] = translation
                    
                    # Generate audio for the translation
                    with st.spinner(f"Generating {lang} audio..."):
                        # Only generate audio for supported languages
                        if lang in ["English", "Hindi", "Telugu"]:
                            audio_bytes = text_to_speech(translation, lang)
                            if audio_bytes:
                                st.session_state.audio_files[lang] = audio_bytes

# Display translations if available
if st.session_state.translations:
    # Create tabs for each translation
    if len(st.session_state.translations) > 0:
        tabs = st.tabs(list(st.session_state.translations.keys()))
        
        for i, (lang, translation) in enumerate(st.session_state.translations.items()):
            with tabs[i]:
                st.markdown(f'<div class="language-title">{lang} Translation</div>', unsafe_allow_html=True)
                
                # Display the translation in a card with improved visibility
                st.markdown(f'<div class="language-card">{translation}</div>', unsafe_allow_html=True)
                
                # Add audio player if audio is available for this language
                if lang in st.session_state.audio_files:
                    st.markdown('<div class="audio-controls">', unsafe_allow_html=True)
                    st.audio(st.session_state.audio_files[lang], format="audio/mp3")
                    
                    # Add download button for audio
                    st.markdown(get_audio_download_link(st.session_state.audio_files[lang], f"{lang.lower()}_translation.mp3"), unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

# Display API key warning if not set
if not GOOGLE_API_KEY:
    st.error("⚠️ Google API Key is not set. Please set the GEMINI_API environment variable.")
    st.info("You can get an API key from https://makersuite.google.com/")
    
st.markdown('<div class="footer"> </div>', unsafe_allow_html=True)