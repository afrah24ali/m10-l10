import { FormEvent, useState } from "react";
import { useRouter } from "next/router";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();

  const [username, setUsername] = useState("demo");
  const [password, setPassword] = useState("demo");
  const [error, setError] = useState("");

 async function handleSubmit(event: FormEvent<HTMLFormElement>) {
  event.preventDefault();
  setError("");

  try {
    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
      setError("Login failed. Check username and password.");
      return;
    }

    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);

    router.push("/extract");
  } catch {
    setError(`Cannot connect to backend at ${API_URL}. Make sure FastAPI is running.`);
  }
}

  return (
    <main>
      <h1>Login</h1>

      <form onSubmit={handleSubmit}>
        <label>
          Username
          <input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>

        <button type="submit">Login</button>
      </form>

      {error && <p>{error}</p>}
    </main>
  );
}