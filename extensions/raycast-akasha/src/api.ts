import { getPreferenceValues } from "@raycast/api";
import { spawn } from "child_process";

interface Preferences {
  apiUrl: string;
  vaultName: string;
  akashaCoreDir: string;
}

export function prefs(): Preferences {
  return getPreferenceValues<Preferences>();
}

export interface SearchResult {
  title: string;
  path: string;
  snippet: string;
  score: number;
  tags: string[];
  modified: string | null;
}

export interface SearchResponse {
  results: SearchResult[];
  query_time_ms: number;
  total_notes: number;
}

export function obsidianUrl(path: string): string {
  const { vaultName } = prefs();
  return `obsidian://open?vault=${encodeURIComponent(vaultName)}&file=${encodeURIComponent(path)}`;
}

export async function isServerRunning(): Promise<boolean> {
  try {
    const res = await fetch(`${prefs().apiUrl}/health`, {
      signal: AbortSignal.timeout(2000),
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function startServer(): Promise<void> {
  const { akashaCoreDir } = prefs();
  if (!akashaCoreDir) return;

  const child = spawn("/opt/homebrew/bin/poetry", ["run", "akasha-serve"], {
    cwd: akashaCoreDir,
    detached: true,
    stdio: "ignore",
  });
  child.unref();

  // Poll until ready (up to 10s)
  for (let i = 0; i < 20; i++) {
    await new Promise((r) => setTimeout(r, 500));
    if (await isServerRunning()) return;
  }
}

export async function search(query: string, limit = 8): Promise<SearchResponse> {
  const res = await fetch(`${prefs().apiUrl}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit }),
    signal: AbortSignal.timeout(10000),
  });
  if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
  return res.json() as Promise<SearchResponse>;
}

export async function getStats(): Promise<{ total_notes: number }> {
  const res = await fetch(`${prefs().apiUrl}/stats`, {
    signal: AbortSignal.timeout(3000),
  });
  if (!res.ok) throw new Error("Stats failed");
  return res.json() as Promise<{ total_notes: number }>;
}
