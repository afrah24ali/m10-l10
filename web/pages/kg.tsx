import { useState } from "react";
import { useRouter } from "next/router";
import { authFetch } from "../lib/api";
import type { KGResponse } from "../lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function KgPage() {
  const router = useRouter();

  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<KGResponse | null>(null);
  const [error, setError] = useState("");
  const [supportedPatterns, setSupportedPatterns] = useState<string[]>([]);

  async function submit() {
    setError("");
    setResult(null);
    setSupportedPatterns([]);

    const res = await authFetch(`${API_URL}/kg/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    if (res.status === 401) {
      router.push("/login");
      return;
    }

    if (res.status === 403) {
      setError("Insufficient scope");
      return;
    }

    if (res.status === 422) {
      const data = await res.json();

      setError("Unsupported question.");

      if (data.detail?.supported_patterns) {
        setSupportedPatterns(data.detail.supported_patterns);
      }

      return;
    }

    if (res.status === 503) {
      setError("Backend is not ready.");
      return;
    }

    if (!res.ok) {
      setError("Request failed.");
      return;
    }

    const data: KGResponse = await res.json();
    setResult(data);
  }

  const columns =
    result && result.rows.length > 0 ? Object.keys(result.rows[0]) : [];

  return (
    <main>
      <h1>Knowledge Graph — Recipe Query</h1>

      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="e.g. Find Sichuan recipes"
      />

      <button onClick={submit} disabled={!question}>
        Ask
      </button>

      {error && <p>{error}</p>}

      {supportedPatterns.length > 0 && (
        <section>
          <h2>Supported questions</h2>
          <ul>
            {supportedPatterns.map((pattern) => (
              <li key={pattern}>{pattern}</li>
            ))}
          </ul>
        </section>
      )}

      {result && (
        <section>
          <h2>Cypher</h2>
          <pre>{result.cypher}</pre>

          <h2>Rows</h2>

          {result.rows.length === 0 ? (
            <p>No rows found.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  {columns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {result.rows.map((row, index) => (
                  <tr key={index} data-testid="kg-row">
                    {columns.map((column) => (
                      <td key={column}>{String(row[column])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </main>
  );
}