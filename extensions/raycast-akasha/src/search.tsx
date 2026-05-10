import {
  List,
  ActionPanel,
  Action,
  Icon,
  Color,
  showToast,
  Toast,
  getPreferenceValues,
} from "@raycast/api";
import { useState, useEffect, useRef } from "react";
import {
  isServerRunning,
  startServer,
  search,
  obsidianUrl,
  SearchResult,
} from "./api";

interface Preferences {
  akashaCoreDir: string;
}

function scoreColor(score: number): Color {
  if (score >= 0.7) return Color.Green;
  if (score >= 0.5) return Color.Yellow;
  return Color.SecondaryText;
}

function sourcePath(path: string): string {
  // e.g. "Books/Think Like a CTO/03 - Managing up.md" → "Books › Think Like a CTO"
  const parts = path.split("/");
  return parts.slice(0, -1).join(" › ");
}

function ResultDetail({ result, totalNotes }: { result: SearchResult; totalNotes: number }) {
  const scoreBar = "█".repeat(Math.round(result.score * 8)) + "░".repeat(8 - Math.round(result.score * 8));

  const markdown = `${result.snippet || "_No preview available._"}`;

  return (
    <List.Item.Detail
      markdown={markdown}
      metadata={
        <List.Item.Detail.Metadata>
          <List.Item.Detail.Metadata.Label
            title="Score"
            text={`${scoreBar}  ${Math.round(result.score * 100)}%`}
          />
          <List.Item.Detail.Metadata.Separator />
          <List.Item.Detail.Metadata.Label title="Path" text={result.path} />
          {result.modified && (
            <List.Item.Detail.Metadata.Label
              title="Modified"
              text={new Date(result.modified).toLocaleDateString()}
            />
          )}
          {result.tags.length > 0 && (
            <List.Item.Detail.Metadata.TagList title="Tags">
              {result.tags.map((t) => (
                <List.Item.Detail.Metadata.TagList.Item key={t} text={t} color={Color.Blue} />
              ))}
            </List.Item.Detail.Metadata.TagList>
          )}
          <List.Item.Detail.Metadata.Separator />
          <List.Item.Detail.Metadata.Label title="Vault notes" text={String(totalNotes)} />
        </List.Item.Detail.Metadata>
      }
    />
  );
}

export default function SearchAkasha() {
  const { akashaCoreDir } = getPreferenceValues<Preferences>();

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [serverReady, setServerReady] = useState(false);
  const [totalNotes, setTotalNotes] = useState(0);
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Ensure server is running on mount
  useEffect(() => {
    async function ensureServer() {
      setIsLoading(true);
      if (await isServerRunning()) {
        setServerReady(true);
        setIsLoading(false);
        return;
      }

      if (!akashaCoreDir) {
        await showToast({
          style: Toast.Style.Failure,
          title: "Akasha server not running",
          message: "Set 'Akasha Core Directory' in extension preferences to enable auto-start",
        });
        setIsLoading(false);
        return;
      }

      const toast = await showToast({
        style: Toast.Style.Animated,
        title: "Starting Akasha server…",
      });

      await startServer();

      if (await isServerRunning()) {
        toast.style = Toast.Style.Success;
        toast.title = "Akasha ready";
        setServerReady(true);
      } else {
        toast.style = Toast.Style.Failure;
        toast.title = "Could not start server";
        toast.message = "Run `poetry run akasha-serve` manually in akasha-core/";
      }

      setIsLoading(false);
    }

    ensureServer();
  }, []);

  // Debounced search on query change
  useEffect(() => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current);

    if (!serverReady || !query.trim()) {
      setResults([]);
      return;
    }

    debounceTimer.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const data = await search(query);
        setResults(data.results);
        setTotalNotes(data.total_notes);
      } catch (e) {
        await showToast({
          style: Toast.Style.Failure,
          title: "Search failed",
          message: String(e),
        });
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    };
  }, [query, serverReady]);

  return (
    <List
      isLoading={isLoading}
      onSearchTextChange={setQuery}
      searchBarPlaceholder="Search your knowledge base…"
      throttle={false}
      isShowingDetail={results.length > 0}
    >
      {results.length === 0 && !isLoading && (
        <List.EmptyView
          icon={{ source: "extension-icon.png" }}
          title={query ? `No results for "${query}"` : "Search your knowledge base"}
          description={query ? "Try different keywords or a broader phrase" : "Type to search"}
        />
      )}

      {results.map((result) => (
        <List.Item
          key={result.path}
          icon={{ source: Icon.Document, tintColor: scoreColor(result.score) }}
          title={result.title}
          subtitle={sourcePath(result.path)}
          accessories={[
            ...result.tags.slice(0, 2).map((t) => ({
              tag: { value: t, color: Color.Blue },
            })),
            {
              text: {
                value: `${Math.round(result.score * 100)}%`,
                color: scoreColor(result.score),
              },
              tooltip: "Similarity score",
            },
          ]}
          detail={<ResultDetail result={result} totalNotes={totalNotes} />}
          actions={
            <ActionPanel>
              <ActionPanel.Section>
                <Action.Open
                  title="Open in Obsidian"
                  icon={Icon.Document}
                  target={obsidianUrl(result.path)}
                />
              </ActionPanel.Section>
              <ActionPanel.Section>
                <Action.CopyToClipboard
                  title="Copy Obsidian URL"
                  content={obsidianUrl(result.path)}
                  shortcut={{ modifiers: ["cmd"], key: "u" }}
                />
                <Action.CopyToClipboard
                  title="Copy Note Path"
                  content={result.path}
                  shortcut={{ modifiers: ["cmd"], key: "." }}
                />
              </ActionPanel.Section>
            </ActionPanel>
          }
        />
      ))}
    </List>
  );
}
