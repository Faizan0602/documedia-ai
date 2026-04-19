import React, { useState, useRef } from "react";
import axios from "axios";
import { BASE_URL } from "../config";

function Timestamps({ docId }) {
  const [timestamps, setTimestamps] = useState([]);
  const videoRef = useRef(null);

  const fetchTimestamps = async () => {
    if (!docId) return;

    try {
      const res = await axios.post(`${BASE_URL}/api/v1/timestamps/`, {
        doc_id: docId
      });
      setTimestamps(res.data.timestamps || []);
    } catch (err) {
      console.error("Error fetching timestamps", err);
      // Fallback mock timestamps if transcription isn't real yet
      setTimestamps([
        { label: "Introduction", time: 2 },
        { label: "Main Topic", time: 10 }
      ]);
    }
  };

  const jumpTo = (time) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      videoRef.current.play();
    }
  };

  return (
    <div style={{ marginTop: "30px" }}>
      <h2>Media Analysis & Timestamps</h2>

      <button onClick={fetchTimestamps} disabled={!docId}>
        Get AI Timestamps
      </button>

      {/* 🔥 Video Player pointed at our backend static files */}
      <div style={{ marginTop: "10px" }}>
        {docId ? (
          <video
            ref={videoRef}
            width="600"
            controls
            // Serve the file directly out of the docker uploads folder
            src={`${BASE_URL}/uploads/${docId}`} 
          />
        ) : (
          <p>Please upload a video file first.</p>
        )}
      </div>

      {/* 🔥 Timestamp list */}
      {timestamps.length > 0 && (
        <ul style={{ marginTop: "20px" }}>
          {timestamps.map((t, index) => (
            <li key={index} style={{ marginBottom: "10px" }}>
              <strong>{t.label}</strong> at {t.time} seconds
              <button
                onClick={() => jumpTo(t.time)}
                style={{ marginLeft: "15px" }}
              >
                ▶ Jump to {t.time}s
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default Timestamps;