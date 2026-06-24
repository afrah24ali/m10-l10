import { useState } from "react";
import { KGResponse } from "../lib/types";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ValidationErrorDetail {
  reason?: string;
  supported_patterns?: string[];
}

export default function KgPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<KGResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [supportedPatterns, setSupportedPatterns] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    setErrorMsg(null);
    setResult(null);
    setSupportedPatterns([]);

    try {
      const response = await fetch(`${API_URL}/kg/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      if (response.status === 422) {
        const errorData = await response.json();
        const detail: string | ValidationErrorDetail | any = errorData.detail;
        
        if (detail && typeof detail === "object") {
          if (detail.reason === "unsupported_question") {
            setErrorMsg("Unsupported question shape. Please try a different query pattern.");
            setSupportedPatterns(detail.supported_patterns || []);
          } else {
            setErrorMsg(JSON.stringify(detail));
          }
        } else {
          setErrorMsg(detail || "Validation Error (422)");
        }
      } else if (response.status === 503) {
        setErrorMsg("The backend is starting up — please try again in a moment.");
      } else if (!response.ok) {
        setErrorMsg(`Error ${response.status}: ${response.statusText}`);
      } else {
        const data: KGResponse = await response.json();
        setResult(data);
      }
    } catch (err) {
      setErrorMsg("Could not reach the backend.");
    } finally {
      setLoading(false);
    }
  }

  // Helper to extract table headers
  const getHeaders = (rows: Record<string, unknown>[]) => {
    if (!rows || rows.length === 0) return [];
    return Object.keys(rows[0]);
  };

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
      <div style={{ maxWidth: "56rem", margin: "0 auto" }}>
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
              background: "linear-gradient(to right, #10b981, #3b82f6)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Knowledge Graph deterministic NL &rarr; Cypher
          </h1>
          <p style={{ color: "#94a3b8", marginTop: "0.25rem" }}>
            Translate natural language queries into exact Neo4j Cypher commands.
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
              Ask the Graph
            </label>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <input
                id="question-input"
                type="text"
                placeholder="e.g. Find Sichuan recipes"
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
                  backgroundColor: !question.trim() || loading ? "#475569" : "#10b981",
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
            <p style={{ margin: "0 0 1rem 0" }}>{errorMsg}</p>
            
            {supportedPatterns.length > 0 && (
              <div>
                <p style={{ fontWeight: "600", margin: "0 0 0.5rem 0" }}>Supported Patterns:</p>
                <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
                  {supportedPatterns.map((pat, idx) => (
                    <li key={idx} style={{ marginBottom: "0.25rem" }}>{pat}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {result && (
          <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
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
                  fontSize: "1.25rem",
                  fontWeight: "700",
                  color: "#10b981",
                  marginBottom: "1rem",
                  borderBottom: "1px solid #334155",
                  paddingBottom: "0.5rem",
                }}
              >
                Generated Cypher
              </h2>
              <pre
                style={{
                  backgroundColor: "#0f172a",
                  padding: "1rem",
                  borderRadius: "0.5rem",
                  overflowX: "auto",
                  color: "#34d399",
                  fontFamily: "monospace",
                  fontSize: "0.95rem",
                  border: "1px solid #1e293b",
                  margin: 0,
                }}
              >
                {result.cypher}
              </pre>
            </section>

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
                  fontSize: "1.25rem",
                  fontWeight: "700",
                  color: "#3b82f6",
                  marginBottom: "1rem",
                  borderBottom: "1px solid #334155",
                  paddingBottom: "0.5rem",
                }}
              >
                Query Results ({result.count} rows)
              </h2>
              
              {result.rows.length === 0 ? (
                <p style={{ color: "#cbd5e1", fontStyle: "italic", margin: 0 }}>
                  Query returned zero rows.
                </p>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table
                    style={{
                      width: "100%",
                      borderCollapse: "collapse",
                      textAlign: "left",
                    }}
                  >
                    <thead>
                      <tr style={{ borderBottom: "2px solid #334155" }}>
                        {getHeaders(result.rows).map((h, i) => (
                          <th
                            key={i}
                            style={{
                              padding: "0.75rem",
                              fontWeight: "600",
                              color: "#94a3b8",
                            }}
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.rows.map((row, idx) => (
                        <tr
                          key={idx}
                          data-testid="kg-row"
                          style={{
                            borderBottom: "1px solid #334155",
                            backgroundColor: idx % 2 === 0 ? "rgba(15, 23, 42, 0.2)" : "transparent",
                          }}
                        >
                          {getHeaders(result.rows).map((h, i) => (
                            <td
                              key={i}
                              style={{
                                padding: "0.75rem",
                                color: "#e2e8f0",
                              }}
                            >
                              {row[h] !== null && row[h] !== undefined ? String(row[h]) : ""}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
