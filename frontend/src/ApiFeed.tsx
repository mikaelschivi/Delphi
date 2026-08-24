import { useState } from "react";
import { AppEvent } from "./types";
import { usePolling } from "./usePolling";
import { formatClockTime } from "./format";

const APIS: { key: string; label: string; description: string }[] = [
  {
    key: "gamma",
    label: "Polymarket Gamma API",
    description:
      "Live feed of markets pulled from Polymarket's Gamma API (gamma-api.polymarket.com) — the source delphi scans for BTC price-target questions.",
  },
  {
    key: "coinbase",
    label: "Coinbase Public API",
    description:
      "Live feed of BTC-USD spot price and daily candle data pulled from Coinbase's public API — used to compute the model's spot price and volatility.",
  },
  {
    key: "news",
    label: "Cointelegraph News RSS",
    description:
      "Live feed of Bitcoin headlines pulled from Cointelegraph's Bitcoin RSS tag feed — the source behind the news drawer. Keyless and free.",
  },
];

export function ApiFeed() {
  const [active, setActive] = useState(APIS[0].key);
  const { data: events } = usePolling<AppEvent[]>(`/api/events?api=${active}&limit=30`, 5000);

  return (
    <div style={{ marginBottom: "1.75rem" }}>
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem" }}>
        {APIS.map((a) => {
          const isActive = a.key === active;
          return (
            <button
              key={a.key}
              onClick={() => setActive(a.key)}
              title={a.description}
              style={{
                cursor: "pointer",
                fontSize: 13,
                fontWeight: 600,
                padding: "0.5rem 1rem",
                borderRadius: 8,
                border: `1px solid ${isActive ? "var(--series-blue)" : "var(--border)"}`,
                background: isActive ? "color-mix(in srgb, var(--series-blue) 14%, transparent)" : "var(--surface-1)",
                color: isActive ? "var(--series-blue)" : "var(--text-secondary)",
              }}
            >
              {a.label}
            </button>
          );
        })}
      </div>

      <div
        style={{
          border: "1px solid var(--border)",
          borderRadius: 12,
          background: "var(--surface-1)",
          maxHeight: 260,
          overflowY: "auto",
        }}
      >
        {!events || events.length === 0 ? (
          <div style={{ padding: "1.25rem", color: "var(--text-muted)", fontSize: 13 }}>
            No data received yet.
          </div>
        ) : (
          events.map((e) => (
            <div
              key={e.id}
              style={{
                display: "flex",
                gap: 10,
                padding: "0.55rem 0.9rem",
                borderBottom: "1px solid var(--gridline)",
                fontSize: 13,
              }}
            >
              <span style={{ color: "var(--text-muted)", fontVariantNumeric: "tabular-nums", flexShrink: 0 }}>
                {formatClockTime(e.ts)}
              </span>
              <span style={{ color: "var(--text-muted)", flexShrink: 0 }}>{e.step}</span>
              <span style={{ color: "var(--text-primary)" }}>{e.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
