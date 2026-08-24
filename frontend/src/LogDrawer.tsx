import { useState } from "react";
import { AppEvent, EventLevel } from "./types";
import { usePolling } from "./usePolling";
import { formatClockTime } from "./format";

const LEVEL_COLOR: Record<EventLevel, string> = {
  info: "var(--text-secondary)",
  warning: "#fab219",
  error: "var(--critical)",
};

const LEVEL_LABEL: Record<EventLevel, string> = {
  info: "INFO",
  warning: "WARN",
  error: "ERROR",
};

export function LogDrawer() {
  const [open, setOpen] = useState(false);
  const { data: events } = usePolling<AppEvent[]>("/api/events?limit=150", 5000, open);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        title="Open the application log — every step of delphi's poll cycle (market discovery, price fetches, volatility calc, forecasting) as it happens, including failures."
        style={{
          position: "fixed",
          right: 20,
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
        Logs
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
              right: 0,
              bottom: 0,
              width: "min(420px, 100vw)",
              background: "var(--surface-1)",
              borderLeft: "1px solid var(--border)",
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
              <span style={{ fontWeight: 700, fontSize: 15 }}>Application log</span>
              <button
                onClick={() => setOpen(false)}
                aria-label="Close log drawer"
                title="Close log drawer"
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
              {!events || events.length === 0 ? (
                <div style={{ padding: "1.25rem", color: "var(--text-muted)", fontSize: 13 }}>
                  No log entries yet.
                </div>
              ) : (
                events.map((e) => (
                  <div
                    key={e.id}
                    style={{
                      padding: "0.6rem 1.1rem",
                      borderBottom: "1px solid var(--gridline)",
                      fontSize: 12.5,
                    }}
                  >
                    <div style={{ display: "flex", gap: 8, marginBottom: 2, alignItems: "baseline" }}>
                      <span style={{ color: "var(--text-muted)", fontVariantNumeric: "tabular-nums" }}>
                        {formatClockTime(e.ts)}
                      </span>
                      <span style={{ color: LEVEL_COLOR[e.level], fontWeight: 700 }}>
                        {LEVEL_LABEL[e.level]}
                      </span>
                      <span style={{ color: "var(--text-muted)" }}>{e.step}</span>
                      {e.api && <span style={{ color: "var(--series-blue)" }}>[{e.api}]</span>}
                    </div>
                    <div style={{ color: "var(--text-primary)" }}>{e.message}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </>
  );
}
