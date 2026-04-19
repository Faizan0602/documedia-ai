
import React, { useState } from "react";
import axios from "axios";
import { BASE_URL } from "../config";

function Upload({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      console.log("Uploading to:", `${BASE_URL}/api/v1/upload/`);

      const response = await axios.post(
        `${BASE_URL}/api/v1/upload/`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      console.log("Upload success:", response.data);

      if (onUploadSuccess) {
        onUploadSuccess(response.data);
      }

      setFile(null);
    } catch (err) {
      console.error("Upload error:", err);
      setError("Failed to upload file");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{ marginBottom: "20px" }}>
      <h2>Upload File</h2>

      <input
        type="file"
        onChange={handleFileChange}
        accept=".pdf,audio/*,video/*"
      />

      <button onClick={handleUpload} disabled={!file || isUploading}>
        {isUploading ? "Uploading..." : "Upload"}
      </button>

      {file && <p>Selected: {file.name}</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}

export default Upload;

