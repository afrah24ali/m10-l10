import { useState } from "react";
import { RAGResponse } from "../lib/types";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RagPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<RAGResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    setErrorMsg(null);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/rag/answer`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question, k: 4 }),
      });

      if (response.status === 422) {
        const errorData = await response.json();
        if (errorData.detail) {
          setErrorMsg(
            typeof errorData.detail === "string"
              ? errorData.detail
              : JSON.stringify(errorData.detail)
          );
        } else {
          setErrorMsg("Validation Error (422)");
        }
      } else if (response.status === 503) {
        setErrorMsg("The backend is starting up — please try again in a moment.");
      } else if (!response.ok) {
        setErrorMsg(`Error ${response.status}: ${response.statusText}`);
      } else {
        const data: RAGResponse = await response.json();
        setResult(data);
      }
    } catch (err) {
      setErrorMsg("Could not reach the backend.");
    } finally {
      setLoading(false);
    }
  }

  function renderAnswerWithCitations(answer: string) {
    if (!answer) return null;

    const parts = [];
    const citationRegex = /\[(\d+)\]/g;
    let lastIndex = 0;
    let match;

    while ((match = citationRegex.exec(answer)) !== null) {
      const matchIndex = match.index;
      if (matchIndex > lastIndex) {
        parts.push(answer.substring(lastIndex, matchIndex));
      }

      const numStr = match[1];

      parts.push(
        <span
          key={matchIndex}
          data-testid="citation-marker"
          style={{
            display: "inline-block",
            color: "#38bdf8",
            fontWeight: "bold",
            cursor: "pointer",
            margin: "0 2px",
            padding: "0 4px",
            backgroundColor: "rgba(56, 189, 248, 0.15)",
            borderRadius: "4px",
            border: "1px solid rgba(56, 189, 248, 0.3)",
          }}
          title={`Citation Source [${numStr}]`}
        >
          [{numStr}]
        </span>
      );

      lastIndex = citationRegex.lastIndex;
    }

    if (lastIndex < answer.length) {
      parts.push(answer.substring(lastIndex));
    }

    return (
      <div style={{ fontSize: "1.125rem", lineHeight: "1.75", color: "#f1f5f9" }}>
        {parts.length > 0 ? parts : answer}
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#0f172a",
        color: "#f8fafc",
        fontFamily: "'Outfit', 'Inter', sans-serif",
        padding: "2rem 1.5rem",
      }}
    >
      <div style={{ maxWidth: "48rem", margin: "0 auto" }}>
        <header style={{ marginBottom: "2rem" }}>
          <Link
            href="/"
            style={{
              color: "#38bdf8",
              textDecoration: "none",
              fontSize: "0.875rem",
              fontWeight: "600",
            }}
          >
            &larr; Back to Home
          </Link>
          <h1
            style={{
              fontSize: "2.25rem",
              fontWeight: "800",
              marginTop: "0.5rem",
              background: "linear-gradient(to right, #f43f5e, #38bdf8)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Retrieval-Augmented Generation (RAG)
          </h1>
          <p style={{ color: "#94a3b8", marginTop: "0.25rem" }}>
            Ask questions about recipes. Responses are strictly grounded on the available vector index.
          </p>
        </header>

        <section
          style={{
            backgroundColor: "#1e293b",
            borderRadius: "0.75rem",
            padding: "1.5rem",
            boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.3)",
            border: "1px solid #334155",
            marginBottom: "2rem",
          }}
        >
          <div style={{ marginBottom: "1rem" }}>
            <label
              htmlFor="question-input"
              style={{
                display: "block",
                fontSize: "0.875rem",
                fontWeight: "600",
                color: "#cbd5e1",
                marginBottom: "0.5rem",
              }}
            >
              Ask a Recipe Question
            </label>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <input
                id="question-input"
                type="text"
                placeholder="e.g. How do I prep ginger for stir-fry?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                style={{
                  flex: 1,
                  backgroundColor: "#0f172a",
                  border: "1px solid #475569",
                  borderRadius: "0.375rem",
                  padding: "0.75rem",
                  color: "#f8fafc",
                  fontSize: "1rem",
                  boxSizing: "border-box",
                }}
              />
              <button
                onClick={submit}
                disabled={!question.trim() || loading}
                style={{
                  backgroundColor: !question.trim() || loading ? "#475569" : "#f43f5e",
                  color: "#ffffff",
                  fontWeight: "600",
                  padding: "0.75rem 2rem",
                  borderRadius: "0.375rem",
                  border: "none",
                  cursor: !question.trim() || loading ? "not-allowed" : "pointer",
                  transition: "background-color 0.2s",
                  fontSize: "1rem",
                }}
              >
                {loading ? "Asking..." : "Ask"}
              </button>
            </div>
          </div>
        </section>

        {errorMsg && (
          <div
            style={{
              backgroundColor: "#7f1d1d",
              border: "1px solid #dc2626",
              borderRadius: "0.5rem",
              padding: "1rem",
              color: "#fecaca",
              marginBottom: "2rem",
              fontSize: "0.95rem",
            }}
          >
            <strong style={{ display: "block", marginBottom: "0.25rem" }}>
              Error Encountered:
            </strong>
            <p style={{ margin: 0 }}>{errorMsg}</p>
          </div>
        )}

        {result && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <section
              style={{
                backgroundColor: "#1e293b",
                borderRadius: "0.75rem",
                padding: "1.5rem",
                boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.3)",
                border: "1px solid #334155",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "1rem",
                  borderBottom: "1px solid #334155",
                  paddingBottom: "0.5rem",
                }}
              >
                <h2
                  style={{
                    fontSize: "1.25rem",
                    fontWeight: "700",
                    color: "#f43f5e",
                    margin: 0,
                  }}
                >
                  Answer
                </h2>
                <div
                  style={{
                    fontSize: "0.875rem",
                    color: "#cbd5e1",
                    backgroundColor: "rgba(244, 63, 94, 0.15)",
                    border: "1px solid rgba(244, 63, 94, 0.3)",
                    padding: "0.25rem 0.75rem",
                    borderRadius: "1rem",
                  }}
                >
                  Confidence: <strong>{(result.confidence * 100).toFixed(1)}%</strong>
                </div>
              </div>
              
              {renderAnswerWithCitations(result.answer)}
            </section>

            {result.citations.length > 0 && (
              <section
                style={{
                  backgroundColor: "#1e293b",
                  borderRadius: "0.75rem",
                  padding: "1.5rem",
                  boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.3)",
                  border: "1px solid #334155",
                }}
              >
                <h2
                  style={{
                    fontSize: "1.125rem",
                    fontWeight: "700",
                    color: "#38bdf8",
                    marginBottom: "1rem",
                    borderBottom: "1px solid #334155",
                    paddingBottom: "0.5rem",
                  }}
                >
                  Citations Used
                </h2>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  {result.citations.map((citation, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        backgroundColor: "#0f172a",
                        padding: "0.75rem 1rem",
                        borderRadius: "0.5rem",
                        border: "1px solid #334155",
                      }}
                    >
                      <div>
                        Source Index: <strong>[{idx + 1}]</strong> &mdash; Chunk ID: <strong>{citation.chunk_id}</strong>
                      </div>
                      <div style={{ color: "#94a3b8" }}>
                        Retrieval Score: {(citation.score * 100).toFixed(1)}%
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
