import { ApiResult } from "./types";

const DEFAULT_BASE = "http://127.0.0.1:8000";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || DEFAULT_BASE;

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { timeoutMs?: number } = {}
): Promise<ApiResult<T>> {
  const { timeoutMs = 30000, ...fetchOptions } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
    });
    const text = await res.text();
    let data: T | null = null;
    try {
      data = text ? (JSON.parse(text) as T) : null;
    } catch {
      data = null;
    }
    return {
      ok: res.ok,
      status: res.status,
      data,
      errorText: res.ok ? undefined : text || res.statusText,
    };
  } catch (err: any) {
    return {
      ok: false,
      status: 0,
      data: null,
      errorText: err?.message || "Network error",
    };
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchOpenApi() {
  return apiFetch<Record<string, any>>("/openapi.json", { timeoutMs: 5000 });
}
