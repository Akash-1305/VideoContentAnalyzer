import os
import base64
import ffmpeg
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from google.generativeai import configure, GenerativeModel
import time # Import time for exponential backoff

# Configure Gemini
# IMPORTANT: Replace "YOUR_GEMINI_API_KEY" with your actual Gemini 1.5 Flash API key
# If running in a Canvas environment, the API key might be automatically provided.
configure(api_key=os.environ.get("GEMINI_API_KEY", "Enter_Your_API_Key"))

# Flask setup
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

video_context_for_chat = ""  # Global context for chat

# --- Helpers ---

def allowed_file(filename):
    """Checks if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_audio_to_base64(audio_path):
    """Encodes an audio file to a base64 string."""
    with open(audio_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode("utf-8")

def transcribe_audio_with_gemini(base64_audio):
    """Transcribes audio using the Gemini 1.5 Flash model with exponential backoff."""
    model = GenerativeModel("models/gemini-1.5-flash")
    prompt = "Please transcribe the following audio. Output only the spoken text."
    audio_data = {
        "inline_data": {
            "mime_type": "audio/wav",
            "data": base64_audio
        }
    }
    
    max_retries = 5
    for i in range(max_retries):
        try:
            response = model.generate_content([
                {"role": "user", "parts": [prompt, audio_data]}
            ])
            return response.text.strip()
        except Exception as e:
            if i < max_retries - 1:
                sleep_time = 2 ** i # Exponential backoff
                print(f"Transcription failed, retrying in {sleep_time} seconds... ({e})")
                time.sleep(sleep_time)
            else:
                raise # Re-raise the last exception if all retries fail

def generate_summary_with_gemini(prompt):
    """Generates a summary using the Gemini 1.5 Flash model with exponential backoff."""
    model = GenerativeModel("models/gemini-1.5-flash")
    
    max_retries = 5
    for i in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            if i < max_retries - 1:
                sleep_time = 2 ** i # Exponential backoff
                print(f"Summary generation failed, retrying in {sleep_time} seconds... ({e})")
                time.sleep(sleep_time)
            else:
                raise # Re-raise the last exception if all retries fail

def chat_with_gemini(chat_history):
    """Handles chat interactions with the Gemini 1.5 Flash model with exponential backoff."""
    model = GenerativeModel("models/gemini-1.5-flash")
    
    max_retries = 5
    for i in range(max_retries):
        try:
            response = model.generate_content(chat_history)
            return response.text.strip()
        except Exception as e:
            if i < max_retries - 1:
                sleep_time = 2 ** i # Exponential backoff
                print(f"Chat generation failed, retrying in {sleep_time} seconds... ({e})")
                time.sleep(sleep_time)
            else:
                raise # Re-raise the last exception if all retries fail

def split_into_segments(text, segment_duration=10):
    """Fake segmenter: splits transcript into chunks with timestamps (10s apart).
    In a real application, this would use actual timestamping from the ASR output.
    """
    sentences = text.split('. ')
    segments = []
    time = 0
    for sentence in sentences:
        cleaned = sentence.strip()
        if cleaned:
            if not cleaned.endswith('.'):
                cleaned += '.'
            segments.append({ "start": time, "text": cleaned })
            time += segment_duration
    return segments

# --- Routes ---

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """
    Handles video uploads, extracts audio, transcribes it, summarizes the content,
    and stores the transcript/summary as global context for chat.
    """
    global video_context_for_chat

    if 'video' not in request.files:
        return jsonify({'error': 'No video file part in the request'}), 400

    video_file = request.files['video']
    # frame_rate = request.form.get('frame_rate', type=float) # Not used in this version

    if video_file.filename == '':
        return jsonify({'error': 'No selected video file'}), 400

    if video_file and allowed_file(video_file.filename):
        filename = secure_filename(video_file.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{os.path.splitext(filename)[0]}.wav")

        try:
            video_file.save(video_path)
            print(f"Saved video to: {video_path}")

            # Extract audio using FFmpeg
            print(f"Extracting audio to: {audio_path}")
            (
                ffmpeg
                .input(video_path)
                .output(audio_path, acodec='pcm_s16le', ar='16000')
                .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            )
            print("Audio extraction complete.")

            # Transcribe
            base64_audio = encode_audio_to_base64(audio_path)
            raw_transcript = transcribe_audio_with_gemini(base64_audio)
            print(f"Transcript: {raw_transcript[:200]}...")

            # Format with timestamps (using fake segmenter)
            structured_transcript = split_into_segments(raw_transcript)

            # Summary
            prompt = (
                f"Here is an audio transcript from a video:\n\n"
                f"Transcript: {raw_transcript}\n\n"
                f"Please provide a concise summary of the video based on this transcript."
            )
            video_summary = generate_summary_with_gemini(prompt)
            print(f"Summary: {video_summary[:200]}...")

            # Store context for chat
            video_context_for_chat = f"Video Transcript:\n{raw_transcript}\n\nVideo Summary:\n{video_summary}"
            print("Video context for chat updated.")

            # Cleanup
            os.remove(video_path)
            os.remove(audio_path)

            return jsonify({
                'message': 'Video processed successfully',
                'summary': video_summary,
                'transcript': structured_transcript
            }), 200

        except ffmpeg.Error as e:
            print("FFmpeg Error:", e.stderr.decode())
            return jsonify({'error': f'FFmpeg error: {e.stderr.decode()}'}), 500
        except Exception as e:
            print("Processing Error:", str(e))
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
            return jsonify({'error': f'Processing failed: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type. Only MP4, AVI, MOV, MKV, WebM allowed.'}), 400

@app.route('/chat_with_video', methods=['POST'])
def chat_with_video():
    """
    Allows users to ask questions about the uploaded video's content.
    Uses the stored video_context_for_chat to answer queries.
    """
    user_query = request.json.get('query')

    if not user_query:
        return jsonify({'error': 'No query provided'}), 400

    if not video_context_for_chat:
        return jsonify({'error': 'No video has been processed yet. Please upload a video first.'}), 400

    try:
        # Construct the chat history for the model
        # The model needs to understand the context of the video before answering the user's question.
        chat_history = [
            {"role": "user", "parts": [
                "I have provided you with the transcript and summary of a video. "
                "Please answer questions related to this video based on the context provided. "
                "If the question cannot be answered from the video content, state that. "
                f"Here is the video content:\n\n{video_context_for_chat}"
            ]},
            {"role": "model", "parts": ["Okay, I understand. I will answer your questions based on the video content you provided."]},
            {"role": "user", "parts": [user_query]}
        ]

        print(f"Sending query to Gemini: {user_query}")
        response_text = chat_with_gemini(chat_history)
        print(f"Gemini response: {response_text}")

        return jsonify({'answer': response_text}), 200

    except Exception as e:
        print("Chat processing error:", str(e))
        return jsonify({'error': f'Failed to process chat query: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) # Running on port 5000 for local testing
