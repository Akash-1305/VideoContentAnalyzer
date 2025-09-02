import os
import base64
import time
import io
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from moviepy import VideoFileClip
from PIL import Image
from google.generativeai import configure, GenerativeModel

# Configure Gemini
configure(api_key=os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE"))

# Flask setup
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

video_context_for_chat = ""  # Global chat context


# --- Helpers ---

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_audio_to_base64(audio_path):
    with open(audio_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode("utf-8")

def extract_key_frames(video_path, interval=2): # Reduced interval for more frames
    """
    Extract key frames every X seconds and return them as base64 JPEGs.
    The interval is now set to 2 seconds for a more detailed analysis.
    """
    clip = VideoFileClip(video_path)
    duration = int(clip.duration)
    frames = []

    for t in range(0, duration, interval):
        try:
            frame = clip.get_frame(t)
            img = Image.fromarray(frame)
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            frames.append(img_str)
        except Exception as e:
            print(f"Could not extract frame at time {t}: {e}")
    
    clip.close()
    return frames

def transcribe_audio_with_gemini(base64_audio):
    model = GenerativeModel("models/gemini-2.0-flash")
    prompt = "Please transcribe the following audio. Output only the spoken text."
    audio_data = {
        "inline_data": {
            "mime_type": "audio/wav",
            "data": base64_audio
        }
    }

    for i in range(5):
        try:
            response = model.generate_content([
                {"role": "user", "parts": [prompt, audio_data]}
            ])
            return response.text.strip()
        except Exception as e:
            time.sleep(2 ** i)
            if i == 4:
                raise

def generate_summary_with_gemini(prompt):
    model = GenerativeModel("models/gemini-2.0-flash")
    for i in range(5):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            time.sleep(2 ** i)
            if i == 4:
                raise

def analyze_video_visuals_with_gemini(base64_images, prompt):
    """
    Analyzes video visuals using a series of key frames.
    The prompt is more specific to encourage a detailed, sequential description.
    """
    model = GenerativeModel("models/gemini-2.0-flash")
    images = [
        {"inline_data": {"mime_type": "image/jpeg", "data": img}} for img in base64_images
    ]

    for i in range(5):
        try:
            response = model.generate_content([
                {"role": "user", "parts": [prompt] + images}
            ])
            return response.text.strip()
        except Exception as e:
            time.sleep(2 ** i)
            if i == 4:
                raise

def chat_with_gemini(chat_history):
    model = GenerativeModel("models/gemini-2.0-flash")
    for i in range(5):
        try:
            response = model.generate_content(chat_history)
            return response.text.strip()
        except Exception as e:
            time.sleep(2 ** i)
            if i == 4:
                raise

def split_into_segments(text, segment_duration=10):
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
    global video_context_for_chat

    if 'video' not in request.files:
        return jsonify({'error': 'No video file part in the request'}), 400

    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({'error': 'No selected video file'}), 400

    if not allowed_file(video_file.filename):
        return jsonify({'error': 'Invalid file type. Only MP4, AVI, MOV, MKV, WebM allowed.'}), 400

    filename = secure_filename(video_file.filename)
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{os.path.splitext(filename)[0]}.wav")

    try:
        # Save video
        video_file.save(video_path)
        print(f"Saved video to: {video_path}")

        has_audio = False
        try:
            with VideoFileClip(video_path) as video:
                has_audio = video.audio is not None
                if has_audio:
                    video.audio.write_audiofile(audio_path, fps=16000, codec='pcm_s16le')
        except Exception as e:
            print(f"Could not process audio: {e}")
            has_audio = False

        structured_transcript = []
        raw_transcript = ""
        video_summary = ""
        video_description = ""

        if has_audio:
            print("Transcribing audio...")
            base64_audio = encode_audio_to_base64(audio_path)
            raw_transcript = transcribe_audio_with_gemini(base64_audio)
            structured_transcript = split_into_segments(raw_transcript)

        # Extract frames for visual analysis
        print("Extracting key frames...")
        key_frames = extract_key_frames(video_path)
        
        # Only proceed with analysis if frames were extracted
        if not key_frames:
            return jsonify({'error': 'Failed to extract any frames from the video. The file may be corrupt.'}), 400

        print("Analyzing visual content (what’s happening)...")
        happening_prompt = (
            "Please describe the events and scenes in the video in a chronological, scene-by-scene manner "
            "based on the series of images provided. Focus on actions, people, objects, and the overall narrative. "
            "Do not just list objects, but describe what is happening over time."
        )
        video_description = analyze_video_visuals_with_gemini(key_frames, happening_prompt)

        # Generate summary based on both transcript and visual description
        if has_audio and raw_transcript:
            summary_prompt = (
                f"Here is an audio transcript and a visual description of a video:\n\n"
                f"Transcript: {raw_transcript}\n\n"
                f"Visual Description: {video_description}\n\n"
                f"Please provide a concise, comprehensive summary of the video based on both the text and visuals."
            )
            video_summary = generate_summary_with_gemini(summary_prompt)
        else:
            summary_prompt = (
                f"Provide a concise summary of the video based only on the visual description:\n\n"
                f"{video_description}"
            )
            video_summary = generate_summary_with_gemini(summary_prompt)

        # Store for chat
        video_context_for_chat = ""
        if raw_transcript:
            video_context_for_chat += f"Video Transcript:\n{raw_transcript}\n\n"
        video_context_for_chat += f"Video Description:\n{video_description}\n\n"
        video_context_for_chat += f"Video Summary:\n{video_summary}"

        # Cleanup
        if os.path.exists(video_path): os.remove(video_path)
        if os.path.exists(audio_path): os.remove(audio_path)

        return jsonify({
            'message': 'Video processed successfully',
            'summary': video_summary,
            'transcript': structured_transcript,
            'description': video_description
        }), 200

    except Exception as e:
        print("Processing Error:", str(e))
        # Ensure cleanup even on error
        if os.path.exists(video_path): os.remove(video_path)
        if os.path.exists(audio_path): os.remove(audio_path)
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500


@app.route('/chat_with_video', methods=['POST'])
def chat_with_video():
    user_query = request.json.get('query')

    if not user_query:
        return jsonify({'error': 'No query provided'}), 400

    if not video_context_for_chat:
        return jsonify({'error': 'No video has been processed yet. Please upload a video first.'}), 400

    try:
        chat_history = [
            {"role": "user", "parts": [
                "You are given a video transcript, summary, and description of what is happening in the video. "
                "Answer questions based only on this content. "
                f"\n\n{video_context_for_chat}"
            ]},
            {"role": "model", "parts": ["Understood. I'm ready to answer based on the provided video content."]},
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
    app.run(debug=True, port=5000)