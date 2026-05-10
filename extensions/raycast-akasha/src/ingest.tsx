import {
  Form,
  ActionPanel,
  Action,
  Detail,
  Icon,
  Color,
  showToast,
  Toast,
  getPreferenceValues,
  useNavigation,
} from "@raycast/api";
import { useState, useEffect, useRef } from "react";
import { isServerRunning, startServer, obsidianUrl, prefs } from "./api";

// ── API helpers ──────────────────────────────────────────────────────────────

interface IngestJob {
  job_id: string;
  status: "running" | "done" | "error";
  messages: string[];
  result?: string;   // vault-relative path to the book index note
  error?: string;
}

async function startIngest(filePath: string): Promise<IngestJob> {
  const { apiUrl } = prefs();
  const res = await fetch(`${apiUrl}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: filePath }),
    signal: AbortSignal.timeout(10000),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText })) as { detail?: string };
    throw new Error(err.detail || res.statusText);
  }
  return res.json() as Promise<IngestJob>;
}

async function pollIngest(jobId: string): Promise<IngestJob> {
  const { apiUrl } = prefs();
  const res = await fetch(`${apiUrl}/ingest/${jobId}`, {
    signal: AbortSignal.timeout(5000),
  });
  if (!res.ok) throw new Error(`Poll failed: ${res.statusText}`);
  return res.json() as Promise<IngestJob>;
}

// ── Progress / result view ───────────────────────────────────────────────────

function ProgressView({ jobId, fileName }: { jobId: string; fileName: string }) {
  const [job, setJob] = useState<IngestJob | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    async function poll() {
      try {
        const updated = await pollIngest(jobId);
        setJob(updated);
        if (updated.status !== "running" && intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      } catch {
        // transient error — keep polling
      }
    }

    poll();
    intervalRef.current = setInterval(poll, 2000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [jobId]);

  const isRunning = !job || job.status === "running";
  const isDone = job?.status === "done";
  const isError = job?.status === "error";

  const messages = job?.messages ?? [];
  const progressLines = messages.map((m) => `- ${m}`).join("\n");

  let markdown = `# ${fileName}\n\n`;

  if (isRunning) {
    markdown += `*Processing…*\n\n${progressLines || "- Starting up…"}`;
  } else if (isDone) {
    markdown += `**Done!**\n\n${progressLines}`;
  } else if (isError) {
    markdown += `**❌ Failed**\n\n> ${job?.error}\n\n${progressLines}`;
  }

  const obsidianTarget = job?.result ? obsidianUrl(job.result) : undefined;

  return (
    <Detail
      isLoading={isRunning}
      navigationTitle={fileName}
      markdown={markdown}
      actions={
        isDone && obsidianTarget ? (
          <ActionPanel>
            <Action.Open
              title="Open Book Note in Obsidian"
              icon={Icon.Document}
              target={obsidianTarget}
            />
            <Action.CopyToClipboard
              title="Copy Obsidian URL"
              content={obsidianTarget}
              shortcut={{ modifiers: ["cmd"], key: "u" }}
            />
          </ActionPanel>
        ) : undefined
      }
    />
  );
}

// ── File picker form ─────────────────────────────────────────────────────────

export default function IngestBook() {
  const { akashaCoreDir } = getPreferenceValues<{ akashaCoreDir: string }>();
  const { push } = useNavigation();
  const [serverReady, setServerReady] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  async function handleSubmit(values: { file: string[] }) {
    const filePath = values.file?.[0];
    if (!filePath) return;

    setIsSubmitting(true);
    const fileName = filePath.split("/").pop() ?? filePath;

    try {
      const job = await startIngest(filePath);
      push(<ProgressView jobId={job.job_id} fileName={fileName} />);
    } catch (e) {
      await showToast({
        style: Toast.Style.Failure,
        title: "Failed to start ingestion",
        message: String(e),
      });
      setIsSubmitting(false);
    }
  }

  return (
    <Form
      isLoading={isSubmitting}
      actions={
        <ActionPanel>
          <Action.SubmitForm
            title="Ingest Book"
            icon={{ source: Icon.Book, tintColor: Color.Purple }}
            onSubmit={handleSubmit}
          />
        </ActionPanel>
      }
    >
      <Form.FilePicker
        id="file"
        title="Book File"
        allowMultipleSelection={false}
        canChooseDirectories={false}
        info="Select an EPUB or PDF file to ingest into your knowledge base"
      />
      <Form.Description
        title=""
        text={
          serverReady
            ? "Akasha server is ready. Select a file and press ⌘↵ to begin."
            : "Waiting for Akasha server…"
        }
      />
    </Form>
  );
}
