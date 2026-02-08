import os
import asyncio
import io
import soundfile as sf
import numpy as np
from flask import Flask, render_template, request, jsonify, session
from groq import Groq
import edge_tts
import speech_recognition as sr

app = Flask(__name__)
app.secret_key = "language_learning_sphere"

# Initialize Groq Client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
recognizer = sr.Recognizer()

def generate_realistic_voice(text, filename):
    voice = "en-US-AvaNeural" 
    communicate = edge_tts.Communicate(text, voice)
    asyncio.run(communicate.save(filename))

@app.route('/')
def index():
    session['history'] = [{
        "role": "system", 
        "content": "You are the user's supportive, fun best friend. Your goal is a natural, warm conversation. NEVER act like a teacher or an assistant. Use casual talk. Keep responses medium (max 50 words). Always end with a tiny follow-up question."
    }]
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_text = ""
    
    if request.is_json:
        user_text = request.json.get('text')
    elif 'audio' in request.files:
        audio_file = request.files['audio']
        try:
            # 1. Read audio bytes directly into soundfile
            # Note: soundfile handles WAV and FLAC natively without ffmpeg
            audio_bytes = io.BytesIO(audio_file.read())
            data, samplerate = sf.read(audio_bytes)
            
            # 2. Convert to WAV in memory for SpeechRecognition
            wav_io = io.BytesIO()
            sf.write(wav_io, data, samplerate, format='WAV')
            wav_io.seek(0)
            
            with sr.AudioFile(wav_io) as source:
                recorded_audio = recognizer.record(source)
                user_text = recognizer.recognize_google(recorded_audio)
        except Exception as e:
            return jsonify({"error": f"Audio processing failed: {str(e)}"}), 400
    else:
        return jsonify({"error": "No input found"}), 400

    # AI Conversation Logic
    history = session.get('history', [])
    history.append({"role": "user", "content": user_text})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=history
        )
        assistant_text = response.choices[0].message.content
        history.append({"role": "assistant", "content": assistant_text})
        session['history'] = history
        session.modified = True

        audio_path = "static/response.mp3"
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
        generate_realistic_voice(assistant_text, audio_path)

        return jsonify({
            "user_text": user_text, 
            "text": assistant_text, 
            "audio_url": f"/static/response.mp3?v={os.urandom(2).hex()}"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)