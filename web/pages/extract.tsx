import { useState } from "react";
import { ExtractResponse } from "../lib/types";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ExtractPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<ExtractResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    setErrorMsg(null);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/extract`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
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
        const data: ExtractResponse = await response.json();
        setResult(data);
      }
    } catch (err) {
      setErrorMsg("Could not reach the backend.");
    } finally {
      setLoading(false);
    }
  }

  function renderHighlightedText() {
    if (!result || !result.entities || result.entities.length === 0) {
      return <p style={{ color: "#cbd5e1", fontStyle: "italic" }}>No entities extracted.</p>;
    }

    const elements: JSX.Element[] = [];
    let lastIndex = 0;

    result.entities.forEach((entity, index) => {
      if (entity.start > lastIndex) {
        elements.push(
          <span key={`text-${index}`} style={{ color: "#f1f5f9" }}>
            {text.substring(lastIndex, entity.start)}
          </span>
        );
      }
      elements.push(
        <span
          key={`ent-${index}`}
          data-testid="entity-span"
          style={{
            backgroundColor: "#fbbf24",
            color: "#000000",
            borderRadius: "0.25rem",
            padding: "2px 6px",
            margin: "0 2px",
            fontWeight: "600",
            borderBottom: "2px solid #d97706",
            display: "inline-block",
          }}
          title={entity.label}
        >
          {entity.text}
          <span
            style={{
              fontSize: "0.7em",
              color: "#78350f",
              marginLeft: "6px",
            }}
          >
            {entity.label}
          </span>
        </span>
      );
      lastIndex = entity.end;
    });

    if (lastIndex < text.length) {
      elements.push(
        <span key="text-end" style={{ color: "#f1f5f9" }}>
          {text.substring(lastIndex)}
        </span>
      );
    }

    return (
      <div
        style={{
          padding: "1rem",
          borderRadius: "0.5rem",
          backgroundColor: "rgba(17, 24, 39, 0.5)",
          border: "1px solid rgba(55, 65, 81, 0.5)",
          lineHeight: "1.625",
          fontSize: "1.125rem",
        }}
      >
        {elements}
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
              background: "linear-gradient(to right, #38bdf8, #818cf8)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            spaCy Named Entity Recognition
          </h1>
          <p style={{ color: "#94a3b8", marginTop: "0.25rem" }}>
            Extract person names, locations, organisations, and dates from recipes or general text.
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
              htmlFor="text-input"
              style={{
                display: "block",
                fontSize: "0.875rem",
                fontWeight: "600",
                color: "#cbd5e1",
                marginBottom: "0.5rem",
              }}
            >
              Input Text (Max 5,000 characters)
            </label>
            <textarea
              id="text-input"
              rows={5}
              placeholder="e.g. Akira Kurosawa directed Seven Samurai in 1954."
              value={text}
              onChange={(e) => setText(e.target.value)}
              style={{
                width: "100%",
                backgroundColor: "#0f172a",
                border: "1px solid #475569",
                borderRadius: "0.375rem",
                padding: "0.75rem",
                color: "#f8fafc",
                fontSize: "1rem",
                resize: "vertical",
                boxSizing: "border-box",
              }}
            />
          </div>

          <button
            onClick={submit}
            disabled={!text.trim() || loading}
            style={{
              backgroundColor: !text.trim() || loading ? "#475569" : "#3b82f6",
              color: "#ffffff",
              fontWeight: "600",
              padding: "0.75rem 1.5rem",
              borderRadius: "0.375rem",
              border: "none",
              cursor: !text.trim() || loading ? "not-allowed" : "pointer",
              transition: "background-color 0.2s",
              width: "100%",
              fontSize: "1rem",
            }}
          >
            {loading ? "Extracting..." : "Extract"}
          </button>
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
                color: "#38bdf8",
                marginBottom: "1rem",
                borderBottom: "1px solid #334155",
                paddingBottom: "0.5rem",
              }}
            >
              Extracted Results
            </h2>
            {renderHighlightedText()}
          </section>
        )}
      </div>
    </div>
  );
}
