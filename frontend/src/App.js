
import React, { useState } from "react";
import Upload from "./components/Upload";
import Summary from "./components/Summary";
import Chat from "./components/Chat";
import Timestamps from "./components/Timestamps";

function App() {
  const [currentDocId, setCurrentDocId] = useState(null);
  const [fileType, setFileType] = useState(null);

  const handleUploadSuccess = (response) => {
    console.log("UPLOAD RESPONSE:", response);

    if (response && response.doc_id) {
      setCurrentDocId(response.doc_id);

      if (response.filename) {
        const ext = response.filename.split(".").pop().toLowerCase();

        if (["pdf", "txt", "docx"].includes(ext)) {
          setFileType(ext === "txt" ? "text" : ext);
        } else if (["mp4", "avi", "mov"].includes(ext)) {
          setFileType("video");
        } else if (["mp3", "wav", "m4a"].includes(ext)) {
          setFileType("audio");
        } else {
          setFileType("other");
        }
      }
    }
  };

  return (
    <div style={{ padding: "40px", maxWidth: "900px", margin: "0 auto" }}>
      <h1>AI Document Q&A</h1>

      <Upload onUploadSuccess={handleUploadSuccess} />

      {(fileType === "pdf" || fileType === "text" || fileType === "docx") &&
        currentDocId && (
          <>
            <Summary docId={currentDocId} />
            <Chat docId={currentDocId} />
          </>
        )}

      {(fileType === "video" || fileType === "audio") &&
        currentDocId && <Timestamps docId={currentDocId} />}
    </div>
  );
}

export default App;

