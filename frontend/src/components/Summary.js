import React, { useState } from "react";
import axios from "axios";
import { BASE_URL } from "../config";

function Summary({ docId }) { // ✅ Add docId prop
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);

  const getSummary = async () => {
    if (!docId) {
      setSummary("Please upload a document first!");
      return;
    }

    setLoading(true);

    try {
      const res = await axios.post(`${BASE_URL}/api/v1/summary/`, {
        doc_id: docId // ✅ Send doc_id to backend
      });

      setSummary(res.data.summary);
    } catch (err) {
      console.error(err);
      setSummary("Error generating summary");
    }

    setLoading(false);
  };

  return (
    <div style={{ marginTop: "30px" }}>
      <h2>Summary</h2>
      <button onClick={getSummary} disabled={!docId}>
        Generate Summary
      </button>

      {loading && <p>Generating summary...</p>}

      {summary && (
        <pre style={{ whiteSpace: "pre-wrap", marginTop: "10px" }}>
          {summary}
        </pre>
      )}
    </div>
  );
}

export default Summary;