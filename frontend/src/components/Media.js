import React, { useRef } from "react";

function Media({ mediaUrl, timestamps }) {
  const mediaRef = useRef(null);

  // 🔥 Jump to timestamp
  const jumpTo = (time) => {
    if (mediaRef.current) {
      mediaRef.current.pause();
      mediaRef.current.currentTime = time;
      mediaRef.current.play();
    }
  };

  if (!mediaUrl) {
    return <p>No media uploaded</p>;
  }

  // Detect type
  const isVideo = mediaUrl.endsWith(".mp4") || mediaUrl.endsWith(".webm");

  return (
    <div style={{ marginTop: "20px" }}>
      <h2>Media Player</h2>

      {/* 🎥 Video or Audio */}
      {isVideo ? (
        <video
          ref={mediaRef}
          width="400"
          controls
          src={mediaUrl}
        />
      ) : (
        <audio
          ref={mediaRef}
          controls
          src={mediaUrl}
        />
      )}

      {/* 🔥 Timestamp list */}
      <div style={{ marginTop: "10px" }}>
        <h3>Timestamps</h3>

        {timestamps && timestamps.length > 0 ? (
          <ul>
            {timestamps.map((t, index) => (
              <li key={index}>
                {t.label} - {t.time}s
                <button
                  onClick={() => jumpTo(t.time)}
                  style={{ marginLeft: "10px" }}
                >
                  ▶ Play
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p>No timestamps available</p>
        )}
      </div>
    </div>
  );
}

export default Media;