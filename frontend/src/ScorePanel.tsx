import type { CSSProperties } from "react";
import { Calibration } from "./types";
import { formatBrier, formatPct } from "./format";
import { usePolling } from "./usePolling";

const panel: CSSProperties = {
  background: "var(--surface-1)",
  border: "1px solid var(--border)",
  borderRadius: 12,
  padding: "1.25rem 1.4rem",
  marginBottom: "1.75rem",
};

const heading: CSSProperties = {
  fontSize: 12,
  textTransform: "uppercase",
  letterSpacing: "0.04em",
  color: "var(--text-muted)",
  margin: 0,
};

const scoreValue: CSSProperties = {
  fontSize: 22,
  fontWeight: 600,
  fontVariantNumeric: "tabular-nums",
};

function Score({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div style={{ flex: "1 1 140px", minWidth: 140 }}>
      <div style={{ ...heading, marginBottom: 6 }}>{label}</div>
      <div style={{ ...scoreValue, color: accent ?? "var(--text-primary)" }}>{value}</div>
    </div>
  );
}

export function ScorePanel() {
  const { data } = usePolling<Calibration>("/api/calibration", 30_000);

  if (!data) return null;

  if (data.resolved_markets === 0) {
    return (
      <div style={panel}>
        <h2 style={heading}>Model score</h2>
        <p style={{ margin: "0.6rem 0 0", fontSize: 13, color: "var(--text-secondary)" }}>
          No tracked market has settled yet. Brier scores appear here once markets resolve —
          until then <em>edge</em> is disagreement with the market, not measured skill.
        </p>
      </div>
    );
  }

  const skill = data.skill_vs_market;
  const skillAccent =
    skill === null ? undefined : skill > 0 ? "var(--good)" : "var(--critical)";
  const populated = data.buckets.filter((bucket) => bucket.count > 0);

  return (
    <div style={panel}>
      <h2 style={heading}>Model score</h2>
      <p style={{ margin: "0.5rem 0 1rem", fontSize: 13, color: "var(--text-secondary)" }}>
        Last forecast before settlement, scored against the outcome. Lower Brier is better;
        positive skill means the model beat the market on the same {data.compared_markets}{" "}
        market{data.compared_markets === 1 ? "" : "s"}.
      </p>

      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", marginBottom: "1.25rem" }}>
        <Score label="Settled markets" value={String(data.resolved_markets)} />
        <Score label="Model Brier" value={formatBrier(data.model_brier_compared)} />
        <Score label="Market Brier" value={formatBrier(data.market_brier_compared)} />
        <Score
          label="Skill vs market"
          value={skill === null ? "—" : `${skill >= 0 ? "+" : ""}${skill.toFixed(4)}`}
          accent={skillAccent}
        />
        <Score label="Base rate (YES)" value={formatPct(data.base_rate)} />
      </div>

      {populated.length > 0 && (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr>
              {["Forecast bucket", "N", "Mean forecast", "Observed"].map((label) => (
                <th
                  key={label}
                  style={{
                    textAlign: "left",
                    padding: "0.4rem 0.6rem",
                    fontSize: 11,
                    textTransform: "uppercase",
                    letterSpacing: "0.04em",
                    color: "var(--text-muted)",
                    fontWeight: 500,
                    borderBottom: "1px solid var(--gridline)",
                  }}
                >
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {populated.map((bucket) => (
              <tr key={bucket.lower}>
                <td style={{ padding: "0.4rem 0.6rem", borderBottom: "1px solid var(--gridline)" }}>
                  {formatPct(bucket.lower)}–{formatPct(bucket.upper)}
                </td>
                <td style={{ padding: "0.4rem 0.6rem", borderBottom: "1px solid var(--gridline)" }}>
                  {bucket.count}
                </td>
                <td style={{ padding: "0.4rem 0.6rem", borderBottom: "1px solid var(--gridline)" }}>
                  {formatPct(bucket.mean_forecast)}
                </td>
                <td style={{ padding: "0.4rem 0.6rem", borderBottom: "1px solid var(--gridline)" }}>
                  {formatPct(bucket.observed_frequency)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
