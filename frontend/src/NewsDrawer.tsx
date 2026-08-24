import { useState } from "react";
import { NewsItem } from "./types";
import { formatRelativeTime } from "./format";
import { usePolling } from "./usePolling";

export function NewsDrawer() {
  const [open, setOpen] = useState(false);
  const { data: news, error } = usePolling<NewsItem[]>("/api/news?limit=40", 120_000, open);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        title="Open the Bitcoin news drawer — latest headlines from Cointelegraph's Bitcoin feed."
        style={{
          position: "fixed",
          left: 20,
          bottom: 20,
          cursor: "pointer",
          fontSize: 13,
          fontWeight: 600,
          padding: "0.6rem 1rem",
          borderRadius: 999,
          border: "1px solid var(--border)",
          background: "var(--surface-1)",
          color: "var(--text-primary)",
          boxShadow: "0 4px 16px rgba(0,0,0,0.25)",
        }}
      >
        News
      </button>

      {open && (
        <>
          <div
            onClick={() => setOpen(false)}
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(0,0,0,0.4)",
              zIndex: 20,
            }}
          />
          <div
            style={{
              position: "fixed",
              top: 0,
              left: 0,
              bottom: 0,
              width: "min(420px, 100vw)",
              background: "var(--surface-1)",
              borderRight: "1px solid var(--border)",
              zIndex: 21,
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "1rem 1.1rem",
                borderBottom: "1px solid var(--gridline)",
              }}
            >
              <span style={{ fontWeight: 700, fontSize: 15 }}>Bitcoin news</span>
              <button
                onClick={() => setOpen(false)}
                aria-label="Close news drawer"
                title="Close news drawer"
                style={{
                  cursor: "pointer",
                  background: "none",
                  border: "none",
                  color: "var(--text-muted)",
                  fontSize: 18,
                  lineHeight: 1,
                }}
              >
                ×
              </button>
            </div>
            <div style={{ overflowY: "auto", flex: 1 }}>
              {error ? (
                <div style={{ padding: "1.25rem", color: "var(--critical)", fontSize: 13 }}>
                  Failed to load news: {error}
                </div>
              ) : !news ? (
                <div style={{ padding: "1.25rem", color: "var(--text-muted)", fontSize: 13 }}>
                  Loading headlines…
                </div>
              ) : news.length === 0 ? (
                <div style={{ padding: "1.25rem", color: "var(--text-muted)", fontSize: 13 }}>
                  No headlines yet — the feed is fetched on the next poll cycle.
                </div>
              ) : (
                news.map((item) => (
                  <a
                    key={item.url}
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: "block",
                      padding: "0.75rem 1.1rem",
                      borderBottom: "1px solid var(--gridline)",
                      textDecoration: "none",
                      color: "var(--text-primary)",
                    }}
                  >
                    <div style={{ display: "flex", gap: 8, marginBottom: 3, fontSize: 12 }}>
                      <span style={{ color: "var(--series-blue)" }}>{item.source}</span>
                      {item.published_at && (
                        <span style={{ color: "var(--text-muted)" }}>
                          {formatRelativeTime(item.published_at)}
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: 13.5, fontWeight: 500, lineHeight: 1.35 }}>
                      {item.title}
                    </div>
                    {item.summary && (
                      <div
                        style={{
                          marginTop: 4,
                          fontSize: 12.5,
                          lineHeight: 1.4,
                          color: "var(--text-secondary)",
                        }}
                      >
                        {item.summary}
                      </div>
                    )}
                  </a>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </>
  );
}
