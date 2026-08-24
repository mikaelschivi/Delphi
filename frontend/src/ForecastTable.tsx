import type { CSSProperties } from "react";
import { Forecast } from "./types";
import { formatDeadline, formatPct, formatSignedPct, formatUsd } from "./format";

interface Props {
  forecasts: Forecast[];
}

const th: CSSProperties = {
  textAlign: "left",
  padding: "0.6rem 0.9rem",
  fontSize: 11,
  textTransform: "uppercase",
  letterSpacing: "0.04em",
  color: "var(--text-muted)",
  fontWeight: 500,
  borderBottom: `1px solid var(--gridline)`,
  whiteSpace: "nowrap",
};

const td: CSSProperties = {
  padding: "0.7rem 0.9rem",
  fontSize: 14,
  borderBottom: `1px solid var(--gridline)`,
  color: "var(--text-primary)",
};

function Badge({ text, color }: { text: string; color: string }) {
  return (
    <span
      style={{
        display: "inline-block",
        width: 128,
        textAlign: "center",
        fontSize: 11,
        fontWeight: 600,
        padding: "2px 0",
        borderRadius: 999,
        color,
        border: `1px solid ${color}`,
        textTransform: "uppercase",
        letterSpacing: "0.03em",
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </span>
  );
}

export function ForecastTable({ forecasts }: Props) {
  if (forecasts.length === 0) {
    return (
      <div
        style={{
          padding: "2.5rem",
          textAlign: "center",
          color: "var(--text-muted)",
          border: "1px dashed var(--border)",
          borderRadius: 12,
        }}
      >
        No crypto price-target markets tracked yet.
      </div>
    );
  }

  return (
    <div
      style={{
        overflowX: "auto",
        border: "1px solid var(--border)",
        borderRadius: 12,
        background: "var(--surface-1)",
      }}
    >
      <table style={{ borderCollapse: "collapse", width: "100%", minWidth: 820 }}>
        <thead>
          <tr>
            <th style={th} title="The Polymarket market question, verbatim.">
              Event
            </th>
            <th
              style={th}
              title="How the market resolves: 'barrier' pays out if BTC ever touches the target price before the deadline; 'terminal' only checks the price at the deadline. 'up'/'down' is which side of the target counts as YES."
            >
              Type
            </th>
            <th style={th} title="The BTC price threshold this market resolves against.">
              Target
            </th>
            <th style={th} title="When this market resolves (its Polymarket end date/time, UTC).">
              Deadline
            </th>
            <th style={th} title="BTC-USD spot price used for this forecast, pulled from Coinbase.">
              Spot
            </th>
            <th
              style={th}
              title="Annualized volatility of BTC, estimated from 90 days of Coinbase daily closes (std. dev. of log returns * sqrt(365))."
            >
              Vol (ANN.)
            </th>
            <th
              style={th}
              title="delphi's own probability of YES, from a driftless geometric Brownian motion model using the spot price and volatility above."
            >
              Delphi P
            </th>
            <th
              style={th}
              title="Polymarket's own implied probability of YES, taken from the order book's best-bid/best-ask midpoint."
            >
              Market P
            </th>
            <th
              style={th}
              title="Model P minus Market P. Positive (green) means the model thinks Polymarket is underpricing YES; negative (red) means overpricing."
            >
              Edge
            </th>
          </tr>
        </thead>
        <tbody>
          {forecasts.map((f) => {
            const edgeColor =
              f.edge === null
                ? "var(--text-muted)"
                : f.edge > 0
                  ? "var(--good)"
                  : f.edge < 0
                    ? "var(--critical)"
                    : "var(--text-secondary)";
            return (
              <tr key={f.condition_id}>
                <td style={{ ...td, maxWidth: 340 }}>{f.question}</td>
                <td style={td}>
                  <Badge
                    text={`${f.event_type} · ${f.direction}`}
                    color={f.event_type === "barrier" ? "var(--series-orange)" : "var(--series-blue)"}
                  />
                </td>
                <td style={{ ...td, fontVariantNumeric: "tabular-nums" }}>{formatUsd(f.target_price)}</td>
                <td style={{ ...td, color: "var(--text-secondary)", whiteSpace: "nowrap" }}>
                  {formatDeadline(f.deadline)}
                </td>
                <td style={{ ...td, fontVariantNumeric: "tabular-nums" }}>{formatUsd(f.spot_price)}</td>
                <td style={{ ...td, fontVariantNumeric: "tabular-nums", color: "var(--text-secondary)" }}>
                  {formatPct(f.sigma)}
                </td>
                <td style={{ ...td, fontVariantNumeric: "tabular-nums", fontWeight: 600 }}>
                  {formatPct(f.model_probability)}
                </td>
                <td style={{ ...td, fontVariantNumeric: "tabular-nums", color: "var(--text-secondary)" }}>
                  {formatPct(f.market_implied_probability)}
                </td>
                <td style={{ ...td, fontVariantNumeric: "tabular-nums", fontWeight: 700, color: edgeColor }}>
                  {formatSignedPct(f.edge)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
