import os
import tempfile
import streamlit as st
import moviepy as mp
import whisper
from moviepy import VideoFileClip
from indicTrans.inference.engine import Model
from TTS.api import TTS
import ffmpeg
import srt

# Load AI models
@st.cache_resource
def load_models():
    # Load Whisper for Speech-to-Text
    whisper_model = whisper.load_model("base")
    
    # Load IndicTrans2 for Translation
    indic_trans_model = Model(expdir="indicTrans/model")
    
    # Load Vakyansh TTS for Text-to-Speech
    tts_model = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", progress_bar=False, gpu=False)
    
    return whisper_model, indic_trans_model, tts_model

# Detect source language using Whisper
def detect_language(audio_path, whisper_model):
    result = whisper_model.transcribe(audio_path)
    return result["language"]

# Extract audio from video
def extract_audio(video_path, audio_path):
    video = mp.VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)
    return audio_path

# Convert speech to text using Whisper
def speech_to_text(audio_path, whisper_model):
    result = whisper_model.transcribe(audio_path)
    return result["text"]

# Translate text using IndicTrans2
def translate_text(text, source_lang, target_lang, indic_trans_model):
    translation = indic_trans_model.translate_paragraph(text, source_lang, target_lang)
    return translation

# Generate speech from translated text using Vakyansh TTS
def text_to_speech(text, target_lang, tts_model, output_audio_path):
    tts_model.tts_to_file(text=text, file_path=output_audio_path, language=target_lang)
    return output_audio_path

# Replace original audio with translated speech
def replace_audio(video_path, new_audio_path, output_video_path):
    video = mp.VideoFileClip(video_path)
    new_audio = mp.AudioFileClip(new_audio_path)
    final_video = video.set_audio(new_audio)
    final_video.write_videofile(output_video_path, codec="libx264")
    return output_video_path

# Generate subtitles in SRT format
def generate_subtitles(text, output_srt_path):
    subtitles = []
    for i, line in enumerate(text.split("\n")):
        subtitles.append(srt.Subtitle(index=i, start=srt.timedelta(seconds=i * 2), end=srt.timedelta(seconds=(i + 1) * 2), content=line))
    with open(output_srt_path, "w") as f:
        f.write(srt.compose(subtitles))
    return output_srt_path

# Overlay subtitles onto the video
def overlay_subtitles(video_path, srt_path, output_video_path):
    video = mp.VideoFileClip(video_path)
    subtitles = mp.TextClip.list_from_srt(srt_path)
    final_video = mp.CompositeVideoClip([video] + subtitles)
    final_video.write_videofile(output_video_path, codec="libx264")
    return output_video_path

# Streamlit UI
def main():
    st.title("🚀 Multilingual Video Player")
    st.write("Upload a video in English, Hindi, or Telugu and translate it to your desired language!")

    # Upload video
    uploaded_file = st.file_uploader("Upload a video (.mp4)", type=["mp4"])
    if uploaded_file is not None:
        st.video(uploaded_file)

        # Select target language
        target_lang = st.selectbox("Select target language", ["English", "Hindi", "Telugu"])

        if st.button("Translate Video"):
            with st.spinner("Processing..."):
                # Save uploaded video to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
                    tmp_video.write(uploaded_file.read())
                    video_path = tmp_video.name

                # Load models
                whisper_model, indic_trans_model, tts_model = load_models()

                # Step 1: Extract audio
                audio_path = extract_audio(video_path, "temp_audio.wav")

                # Step 2: Detect source language
                source_lang = detect_language(audio_path, whisper_model)
                st.write(f"Detected source language: {source_lang}")

                # Step 3: Convert speech to text
                text = speech_to_text(audio_path, whisper_model)
                st.write("Original Text:", text)

                # Step 4: Translate text
                translated_text = translate_text(text, source_lang, target_lang, indic_trans_model)
                st.write("Translated Text:", translated_text)

                # Step 5: Generate speech from translated text
                translated_audio_path = text_to_speech(translated_text, target_lang, tts_model, "translated_audio.wav")

                # Step 6: Replace original audio with translated speech
                final_video_path = replace_audio(video_path, translated_audio_path, "final_video.mp4")

                # Step 7: Generate and overlay subtitles
                srt_path = generate_subtitles(translated_text, "subtitles.srt")
                final_video_with_subtitles = overlay_subtitles(final_video_path, srt_path, "final_video_with_subtitles.mp4")

                # Display final video
                st.success("Translation complete!")
                st.video(final_video_with_subtitles)

                # Clean up temporary files
                os.unlink(video_path)
                os.unlink(audio_path)
                os.unlink(translated_audio_path)
                os.unlink(final_video_path)
                os.unlink(srt_path)
                os.unlink(final_video_with_subtitles)

if __name__ == "__main__":
    main()
    