import React, { useState, useEffect } from "react";
import "./VideoAnalyzer.css"; // Import the new CSS file

// TranscriptSegment component (defined here for completeness)
// In a real project, this would be in a separate file like TranscriptSegment.jsx
function TranscriptSegment({ number, text }) {
  return (
    <li className="transcript-segment-item">
      <span className="transcript-segment-time">{number}:</span> {text}
    </li>
  );
}

function VideoAnalyzer() {
  const [videoFile, setVideoFile] = useState(null);
  const [videoURL, setVideoURL] = useState(null);
  const [fps, setFps] = useState("0.1"); // Frames per second for analysis
  const [summary, setSummary] = useState(""); // Renamed from 'result' for clarity
  const [loading, setLoading] = useState(false);
  const [transcript, setTranscript] = useState([]);

  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState([]);

  // This useEffect hook handles creating and revoking the video URL
  useEffect(() => {
    if (videoFile) {
      const url = URL.createObjectURL(videoFile);
      setVideoURL(url);

      // Clean up the object URL when the component unmounts or videoFile changes
      return () => URL.revokeObjectURL(url);
    } else {
      setVideoURL(null);
    }
  }, [videoFile]); // Dependency array: re-run effect when videoFile changes

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setVideoFile(file);
    // The useEffect hook will now handle setting the videoURL
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!videoFile) {
      setSummary("Please select a video file to analyze.");
      return;
    }

    const formData = new FormData();
    formData.append("video", videoFile);
    formData.append("frame_rate", fps);

    try {
      setLoading(true);
      setTranscript([]);
      setChatHistory([]);
      setSummary("Analyzing video...");
      setTranscript([]);

      const res = await fetch("http://127.0.0.1:5000/upload_video", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "Failed to upload video.");
      }

      const data = await res.json();
      console.log("Transcript received:", data.transcript); // Debug log
      setSummary(data.summary || "No summary returned.");
      setTranscript(data.transcript || []);
      setChatHistory([
        {
          role: "ai",
          content: "Video processed! What would you like to know about it?",
        },
      ]);
    } catch (err) {
      console.error("Video upload error:", err);
      setSummary(`Error during analysis: ${err.message}`);
      setChatHistory([
        { role: "ai", content: `Error processing video: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const sendChat = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage = { role: "user", content: chatInput };
    // Optimistically update chat history with user's message
    setChatHistory((prevChat) => [...prevChat, userMessage]);
    setChatInput(""); // Clear input immediately

    try {
      const res = await fetch("http://127.0.0.1:5000/chat_with_video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // IMPORTANT: Backend expects 'query', not 'question'
        body: JSON.stringify({ query: userMessage.content }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "Failed to get AI response.");
      }

      const data = await res.json();
      const aiMessage = { role: "ai", content: data.answer || "No response" };
      setChatHistory((prevChat) => [...prevChat, aiMessage]);
    } catch (err) {
      console.error("Chat error:", err);
      setChatHistory((prevChat) => [
        ...prevChat,
        { role: "ai", content: `Error from assistant: ${err.message}` },
      ]);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <h1 className="header-title">Video Content Analyzer</h1>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        <div className="content-card">
          {/* Left Column: Upload and Analysis */}
          <div className="analysis-section">
            <h2 className="section-title">Analyze Video</h2>

            {/* Upload Form */}
            <form onSubmit={handleSubmit} className="upload-form">
              <div>
                <label htmlFor="video-upload" className="form-label">
                  Upload Video File
                </label>
                <div className="custom-upload-wrapper">
                  <input
                    type="file"
                    accept="video/*"
                    id="video-upload"
                    hidden
                    onChange={handleFileChange}
                  />
                  <label htmlFor="video-upload" className="choose-file-button">
                    {videoFile
                      ? "📁 Change Video File"
                      : "📁 Choose Video File"}
                  </label>

                  {/* The video preview section remains the same, but now `videoURL` will have a valid value */}
                  {videoFile && (
                    <div className="video-preview-container">
                      <p className="video-file-name">✅ {videoFile.name}</p>
                      <video src={videoURL} controls className="video-player" />
                    </div>
                  )}

                  {!videoFile && (
                    <p className="supported-formats-text">
                      Supported: MP4, AVI, MOV, MKV, WebM.
                    </p>
                  )}
                </div>
              </div>

              {/* FPS Input */}
              <div>
                <label htmlFor="fps-input" className="form-label">
                  Frames per Second for Analysis
                </label>
                <input
                  type="number"
                  step="0.1"
                  id="fps-input"
                  className="fps-input"
                  value={fps}
                  onChange={(e) => setFps(e.target.value)}
                  placeholder="e.g. 0.1"
                />
                <p className="fps-hint-text">
                  Lower value = less frequent frames (e.g., 0.1 = every 10s).
                </p>
              </div>

              {/* Analyze Button */}
              <button
                type="submit"
                className="analyze-button"
                disabled={loading}
              >
                {loading ? (
                  <span className="loading-spinner">
                    <svg
                      className="spinner-icon"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Analyzing...
                  </span>
                ) : (
                  "Analyze Video"
                )}
              </button>
            </form>
          </div>

          {/* Right Column: Chat */}
          <div className="chat-section">
            <h2 className="chat-title">Ask Questions About the Video</h2>
            <div className="chat-history-box">
              {chatHistory.length === 0 && (
                <div className="chat-placeholder-text">
                  Ask something after analyzing a video.
                </div>
              )}
              {chatHistory.map((msg, idx) => (
                <div
                  key={idx}
                  className={`chat-message-wrapper ${
                    msg.role === "user"
                      ? "user-message-wrapper"
                      : "ai-message-wrapper"
                  }`}
                >
                  <div
                    className={`chat-message-bubble ${
                      msg.role === "user"
                        ? "user-message-bubble"
                        : "ai-message-bubble"
                    }`}
                  >
                    <strong className="message-role">
                      {msg.role === "user" ? "You" : "AI"}:
                    </strong>{" "}
                    {msg.content}
                  </div>
                </div>
              ))}
            </div>

            <form onSubmit={sendChat} className="chat-input-form">
              <input
                type="text"
                className="chat-input"
                value={chatInput}
                placeholder="Type your question..."
                onChange={(e) => setChatInput(e.target.value)}
                disabled={
                  loading ||
                  !summary ||
                  summary === "Please select a video file to analyze." ||
                  summary === "Error during analysis: Failed to fetch"
                }
              />
              <button
                className="chat-send-button"
                type="submit"
                disabled={
                  loading ||
                  !summary ||
                  summary === "Please select a video file to analyze." ||
                  summary === "Error during analysis: Failed to fetch"
                }
              >
                Send
              </button>
            </form>
          </div>
          {/* Summary */}
          <div className="analysis-results-section">
            <h3 className="results-title">🧠 Analysis Summary:</h3>
            <div className="summary-box">
              {summary || "No summary yet. Upload a video to begin."}
            </div>
          </div>

          {/* Transcript */}
          <div className="transcript-section">
            <h3 className="transcript-title">🎙️ Transcript:</h3>
            <div className="transcript-box">
              {transcript.length > 0 ? (
                <ul>
                  {transcript.map((segment, idx) => (
                    <TranscriptSegment
                      key={idx}
                      number={idx + 1}
                      text={segment.text}
                    />
                  ))}
                </ul>
              ) : (
                <div className="no-transcript-text">
                  No transcript available yet.
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <small className="footer-text">
          &copy; {new Date().getFullYear()} Built by Busted Engine
        </small>
      </footer>
    </div>
  );
}

export default VideoAnalyzer;
