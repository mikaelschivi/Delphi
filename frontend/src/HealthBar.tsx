import { ApiHealth } from "./types";
import { formatRelativeUpdatedAt } from "./format";

const API_LABELS: Record<string, string> = {
  gamma: "Polymarket Gamma API",
  coinbase: "Coinbase Public API",
  news: "Cointelegraph News RSS",
};

interface Props {
  health: ApiHealth[] | null;
}

export function HealthBar({ health }: Props) {
  const rows = health ?? [];
  const known = Object.keys(API_LABELS).map(
    (name) => rows.find((r) => r.api_name === name) ?? { api_name: name, status: null }
  );

  return (
    <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap", marginBottom: "1.5rem" }}>
      {known.map((row) => {
        const status = (row as ApiHealth).status;
        const isUp = status === "up";
        const isDown = status === "down";
        const dotColor = isUp ? "var(--good)" : isDown ? "var(--critical)" : "var(--text-muted)";
        const label = API_LABELS[row.api_name] ?? row.api_name;
        const lastChecked = (row as ApiHealth).last_checked_at;
        const latency = (row as ApiHealth).latency_ms;
        const lastError = (row as ApiHealth).last_error;
        const tooltip = [
          `${label}: ${isUp ? "reachable" : isDown ? "unreachable" : "no data yet"}.`,
          latency != null ? `Last call took ${latency.toFixed(0)}ms.` : null,
          lastChecked ? `Last checked ${formatRelativeUpdatedAt(lastChecked)}.` : null,
          lastError ? `Last error: ${lastError}` : null,
        ]
          .filter(Boolean)
          .join(" ");
        return (
          <div
            key={row.api_name}
            title={tooltip}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "0.45rem 0.8rem",
              borderRadius: 999,
              border: "1px solid var(--border)",
              background: "var(--surface-1)",
              fontSize: 13,
            }}
          >
            <span
              aria-hidden
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: dotColor,
                flexShrink: 0,
              }}
            />
            <span style={{ fontWeight: 600 }}>{label}</span>
            <span style={{ color: "var(--text-muted)" }}>
              {isUp ? "up" : isDown ? "down" : "unknown"}
              {lastChecked ? ` · checked ${formatRelativeUpdatedAt(lastChecked)}` : ""}
            </span>
          </div>
        );
      })}
    </div>
  );
}
