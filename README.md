# Video Content Analyzer

This project provides a web application that allows you to upload a video, analyze its content by transcribing its audio, and then interact with a Gemini 2.0 Flash model to ask questions about the video's content. It's built with a **React** frontend and a **Python Flask** backend, leveraging the **Gemini 2.0 Flash API** for transcription and summarization.

---

## Features

- **Video Upload:** Upload video files in popular formats (MP4, AVI, MOV, MKV, WebM).
- **Audio Transcription:** The backend extracts the audio from the video and uses the Gemini API to generate a full transcript.
- **Video Summarization:** A concise summary of the video's content is created from the transcript.
- **Interactive Chat:** After analysis, you can ask the AI questions about the video, and it will respond based on the provided transcript and summary.
- **Customizable Analysis:** You can set the frame rate for analysis (though this is not fully implemented in the current version, the setting exists on the frontend).

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js and npm:** For the React frontend.
- **Python 3.8+:** For the Flask backend.
- **MoviePy:** For extracting audio from video files.
- **A Gemini 2.0 Flash API Key or any Gemini model API Key:** You'll need an API key from Google to use the Gemini model. You can get one from the [Google AI Studio](https://aistudio.google.com/app/apikey).

---

## Installation

### 1. Backend Setup (Python)

1.  **Clone the repository:**

    ```bash
    git clone <https://github.com/Akash-1305/VideoContentAnalyzer>
    cd <https://github.com/Akash-1305/VideoContentAnalyzer>/backend
    ```

2.  **Create a virtual environment and activate it:**

    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\Activate.ps1
    # On macOS/Linux
    source venv/bin/Activate.ps1
    ```

3.  **Install the required Python packages:**

    ```bash
    pip install flask flask-cors google-generativeai moviepy
    ```

4.  **Set your Gemini API Key:**
    Replace "Enter_Your_API_Key" in the `app.py` file with your actual API key, or set it as an environment variable.

    ```python
    # In backend/app.py
    configure(api_key=os.environ.get("GEMINI_API_KEY", "Enter_Your_API_Key"))
    ```

5.  **Run the Flask backend:**
    ```bash
    python app.py
    ```
    The backend server will start on `http://127.0.0.1:5000`.

### 2. Frontend Setup (React)

1.  **Navigate to the frontend directory:**

    ```bash
    cd ../frontend
    ```

2.  **Install the npm dependencies:**

    ```bash
    npm install
    ```

3.  **Run the React development server:**
    ```bash
    npm start
    ```
    The React application will open in your browser, usually at `http://localhost:3000`.

---

## Usage

1.  **Open the application** in your web browser at `http://localhost:3000`.
2.  In the "Analyze Video" section, click **"Choose Video File"** and select a video from your computer.
3.  Click the **"Analyze Video"** button. The application will upload the video, and the backend will start processing it. This may take some time depending on the video's length.
4.  Once the processing is complete, a summary and a full transcript will appear on the left side of the screen.
5.  On the right side, you can now **ask questions** about the video in the chat interface. The AI will use the generated summary and transcript to provide its answers.

---

## Customization and Future Improvements

- **Timestamping:** The current `split_into_segments` function is a placeholder. A more advanced implementation would use a model or library that provides accurate timestamping for each transcribed word or phrase.
- **UI/UX:** Enhance the user interface with better loading indicators, error messages, and a more polished design.
- **Security:** For a production environment, implement proper authentication, file size limits, and security measures.
- **Advanced Analysis:** Integrate more features like object detection, scene change analysis, or emotional tone detection to provide richer video insights.
- **Streamlined Architecture:** Consider using a message queue (like RabbitMQ or Redis) for long-running tasks like video processing to prevent timeouts and improve scalability.

---
