import { useState } from "react";
import { useRouter } from "next/router";
import { authFetch } from "../lib/api";
import type { ExtractResponse } from "../lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ExtractPage() {
  const router = useRouter();

  const [text, setText] = useState("");
  const [result, setResult] = useState<ExtractResponse | null>(null);
  const [error, setError] = useState("");

  async function submit() {
    setError("");
    setResult(null);

    const res = await authFetch(`${API_URL}/extract`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
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
      setError("Validation error: text is empty or too long.");
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

    const data: ExtractResponse = await res.json();
    setResult(data);
  }

  return (
    <main>
      <h1>Extract — Named Entity Recognition</h1>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <button onClick={submit} disabled={!text}>
        Extract
      </button>

      {error && <p>{error}</p>}

      {result && (
        <section>
          <h2>Entities</h2>

          {result.entities.length === 0 && <p>No entities found.</p>}

          {result.entities.map((entity) => (
            <span
              key={`${entity.start}-${entity.end}-${entity.text}`}
              data-testid="entity-span"
            >
              {entity.text} ({entity.label}){" "}
            </span>
          ))}
        </section>
      )}
    </main>
  );
}