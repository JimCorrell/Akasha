import {
  Detail,
  ActionPanel,
  Action,
  Icon,
  Color,
  showToast,
  Toast,
  getPreferenceValues,
  List,
} from "@raycast/api";
import { useState } from "react";
import { isServerRunning, startServer, obsidianUrl } from "./api";
import { useEffect } from "react";

interface Preferences {
  akashaCoreDir: string;
}

interface NoteResult {
  title: string;
  path: string;
  snippet: string;
  score: number;
  tags: string[];
  modified: string | null;
}

interface AskResponse {
  answer: string;
  sources: NoteResult[];
  query_time_ms: number;
}

async function askQuestion(question: string): Promise<AskResponse> {
  const prefs = getPreferenceValues<{ apiUrl: string }>();
  const apiUrl = prefs.apiUrl || "http://localhost:8765";
  const res = await fetch(`${apiUrl}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, limit: 6 }),
    signal: AbortSignal.timeout(60000),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText })) as { detail?: string };
    throw new Error(err.detail || res.statusText);
  }
  return res.json() as Promise<AskResponse>;
}

function AnswerDetail({ question, response }: { question: string; response: AskResponse }) {
  const sourcesMarkdown = response.sources
    .map((s, i) => `${i + 1}. **${s.title}** — ${s.snippet}`)
    .join("\n");

  const markdown = `# ${question}\n\n${response.answer}\n\n---\n\n### Sources\n${sourcesMarkdown}`;

  return (
    <Detail
      markdown={markdown}
      navigationTitle={question}
      metadata={
        <Detail.Metadata>
          <Detail.Metadata.Label
            title="Sources"
            text={String(response.sources.length)}
          />
          <Detail.Metadata.Label
            title="Query time"
            text={`${(response.query_time_ms / 1000).toFixed(1)}s`}
          />
          <Detail.Metadata.Separator />
          {response.sources.map((s) => (
            <Detail.Metadata.Link
              key={s.path}
              title={`${Math.round(s.score * 100)}%`}
              text={s.title}
              target={obsidianUrl(s.path)}
            />
          ))}
        </Detail.Metadata>
      }
      actions={
        <ActionPanel>
          <ActionPanel.Section title="Sources">
            {response.sources.map((s) => (
              <Action.Open
                key={s.path}
                title={`Open "${s.title}"`}
                icon={Icon.Document}
                target={obsidianUrl(s.path)}
              />
            ))}
          </ActionPanel.Section>
          <ActionPanel.Section>
            <Action.CopyToClipboard
              title="Copy Answer"
              content={response.answer}
              shortcut={{ modifiers: ["cmd"], key: "c" }}
            />
            <Action.CopyToClipboard
              title="Copy Answer + Sources"
              content={markdown}
              shortcut={{ modifiers: ["cmd", "shift"], key: "c" }}
            />
          </ActionPanel.Section>
        </ActionPanel>
      }
    />
  );
}

export default function AskAkasha() {
  const { akashaCoreDir } = getPreferenceValues<Preferences>();

  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [serverReady, setServerReady] = useState(false);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    async function ensureServer() {
      if (await isServerRunning()) {
        setServerReady(true);
        return;
      }
      if (!akashaCoreDir) {
        await showToast({
          style: Toast.Style.Failure,
          title: "Akasha server not running",
          message: "Set 'Akasha Core Directory' in preferences to enable auto-start",
        });
        return;
      }
      const toast = await showToast({ style: Toast.Style.Animated, title: "Starting Akasha…" });
      await startServer();
      if (await isServerRunning()) {
        toast.style = Toast.Style.Success;
        toast.title = "Akasha ready";
        setServerReady(true);
      } else {
        toast.style = Toast.Style.Failure;
        toast.title = "Could not start server";
      }
    }
    ensureServer();
  }, []);

  async function handleSubmit() {
    if (!question.trim() || !serverReady || isLoading) return;
    setIsLoading(true);
    setSubmitted(true);
    const toast = await showToast({ style: Toast.Style.Animated, title: "Thinking…" });
    try {
      const data = await askQuestion(question);
      setResponse(data);
      toast.style = Toast.Style.Success;
      toast.title = "Done";
    } catch (e) {
      toast.style = Toast.Style.Failure;
      toast.title = "Failed";
      toast.message = String(e);
      setSubmitted(false);
    } finally {
      setIsLoading(false);
    }
  }

  if (submitted && response) {
    return <AnswerDetail question={question} response={response} />;
  }

  return (
    <List
      isLoading={isLoading}
      onSearchTextChange={setQuestion}
      searchBarPlaceholder="Ask a question about your knowledge base…"
      throttle={false}
    >
      {!submitted && (
        <List.Item
          icon={{ source: Icon.QuestionMark, tintColor: Color.Blue }}
          title={question ? `Ask: "${question}"` : "Type your question above"}
          subtitle={question ? "Press Enter to ask" : ""}
          actions={
            <ActionPanel>
              <Action
                title="Ask"
                icon={Icon.QuestionMark}
                onAction={handleSubmit}
              />
            </ActionPanel>
          }
        />
      )}
    </List>
  );
}
