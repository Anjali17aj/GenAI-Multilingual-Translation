# 🌐 Multi-Language Translator Web Application

A GenAI-powered multilingual translator web application that enables users to input content in any language and translate it into English, Hindi, or Telugu. It supports input from text, PDF, CSV, or URLs, and provides audio playback using Text-to-Speech (TTS).

## 🚀 Project Overview

This application allows users to:
- Detect the language of input automatically.
- Translate content to English, Hindi, or Telugu using Google Gemini (LLM).
- Convert translated text to speech using Google TTS (gTTS).
- Download both text and audio outputs.

### 📽️ Use Case Example
- Translate official notices to regional languages for radio announcements.
- Convert study material PDFs or CSVs into multiple languages for students.
- Translate blog posts into Indian languages with speech for accessibility.
- Extract text from web URLs and provide multilingual audio/text translations.

---

## 🧠 GenAI Pipeline Components

| Stage             | Tool/Library         | Function Implemented             |
|------------------|----------------------|----------------------------------|
| Language Detection| Google Gemini LLM    | `detect_language_gemini()`       |
| Translation       | Google Gemini LLM    | `translate_text_gemini()`        |
| Text-to-Speech    | gTTS                 | `text_to_speech_gtts()`          |

---

## 🛠 Features

✅ Accepts input from:
- 📄 Direct Text  
- 📘 PDF Upload  
- 📊 CSV Upload  
- 🌐 Web URL  

✅ Detects language automatically  
✅ Translates to selected target language(s)  
✅ Generates and plays speech for translated text  
✅ Allows downloading of audio as `.mp3`  
✅ Clean and interactive UI using Streamlit

---

## 🔧 Technologies & Libraries Used

| Technology         | Purpose                             |
|--------------------|-------------------------------------|
| Streamlit          | UI development                      |
| google-generativeai| Language detection & translation    |
| python-dotenv      | Environment variable management     |
| pandas             | CSV parsing                         |
| PyPDF2             | Text extraction from PDF            |
| requests + bs4     | Web scraping and HTML parsing       |
| gTTS               | Text-to-Speech generation           |

---

## 🧬 Machine Learning Models Used

### 🔹 Google Gemini LLM
- Model: `gemini-1.5-flash`
- Used for:
  - Language Detection (zero-shot prompt)
  - Text Translation (prompt-based, multilingual)

### 🔹 gTTS (Google Text-to-Speech)
- Converts translated text to audio
- Supports: English (`en`), Hindi (`hi`), Telugu (`te`)

---

## Acknowledgements
Google Gemini API
gTTS - Google Text-to-Speech
Streamlit
AI4Bharat Initiative (Indic NLP Research)
