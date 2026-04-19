import React, { useState } from "react";
import Upload from "./components/Upload";
import Summary from "./components/Summary";
import Chat from "./components/Chat";
import Timestamps from "./components/Timestamps"; 

function App() {
  const [currentDocId, setCurrentDocId] = useState(null);
  const [fileType, setFileType] = useState(null); // 'pdf', 'video', etc.

  const handleUploadSuccess = (response) => {
    // response is whatever the backend returns.
    if (response && response.data && response.data.doc_id) {
      setCurrentDocId(response.data.doc_id);
      setFileType(response.data.file_type); 
    }
  };

  return (
    <div style={{ padding: "40px", maxWidth: "900px", margin: "0 auto" }}>
      <h1>AI Document Q&A</h1>
      
      <Upload onUploadSuccess={handleUploadSuccess} />
      
      {/* If it is a Document, show Summary and Chat */}
      {(fileType === 'pdf' || fileType === 'text' || fileType === 'docx') && (
        <>
           <Summary docId={currentDocId} />
           <Chat docId={currentDocId} />
        </>
      )}

      {/* If it is a Video or Audio, show the Timestamps player instead */}
      {(fileType === 'video' || fileType === 'audio') && (
         <Timestamps docId={currentDocId} />
      )}
      
    </div>
  );
}

export default App;