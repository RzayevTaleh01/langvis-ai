// Where the Python backend lives. Built, the page is served by the backend
// itself, so everything is on the same origin. In `next dev` (port 3000) the
// page talks to the backend on its own port.
//
// Every call carries the session cookie. A 401 {error: "auth"} means the
// account is signed out: the "langvis:auth" event makes the AuthProvider ask
// again, and the page falls back to the signed-out layout.

const DEV_BACKEND = "http://localhost:8765";
export const AUTH_EVENT = "langvis:auth";

function isDev(): boolean {
  return typeof window !== "undefined" && window.location.port === "3000";
}

export function apiUrl(path: string): string {
  return (isDev() ? DEV_BACKEND : "") + path;
}

export function wsUrl(): string {
  if (isDev()) return DEV_BACKEND.replace(/^http/, "ws") + "/ws";
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}/ws`;
}

async function read<T>(r: Response): Promise<T | null> {
  const data = await r.json();
  if (r.status === 401 && data && data.error === "auth") window.dispatchEvent(new Event(AUTH_EVENT));
  return data as T;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function getJson<T = any>(path: string): Promise<T | null> {
  try {
    return await read<T>(await fetch(apiUrl(path), { credentials: "include" }));
  } catch {
    return null;
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function postJson<T = any>(path: string, body: unknown): Promise<T | null> {
  try {
    return await read<T>(await fetch(apiUrl(path), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }));
  } catch {
    return null;
  }
}
