import { storage } from "@/src/utils/storage";

const BASE = process.env.EXPO_PUBLIC_BACKEND_URL as string;

let cachedToken: string | null = null;

export function setToken(t: string | null) {
  cachedToken = t;
}

export async function getToken(): Promise<string | null> {
  if (cachedToken) return cachedToken;
  const t = await storage.secureGet<string>("qa_token", "");
  cachedToken = t || null;
  return cachedToken;
}

export function wsUrl(token: string): string {
  const base = BASE.replace(/^http/, "ws");
  return `${base}/api/ws/game?token=${encodeURIComponent(token)}`;
}

export async function api<T = any>(
  path: string,
  opts: { method?: string; body?: any; headers?: Record<string, string> } = {},
): Promise<T> {
  const token = await getToken();
  const res = await fetch(`${BASE}/api${path}`, {
    method: opts.method || "GET",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers || {}),
    },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    let detail = "İstek başarısız";
    try {
      const j = await res.json();
      detail = j.detail || detail;
    } catch {}
    const err: any = new Error(detail);
    err.status = res.status;
    throw err;
  }
  if (res.status === 204) return {} as T;
  return res.json();
}
