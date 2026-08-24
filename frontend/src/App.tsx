import { ApiHealth, Forecast } from "./types";
import { StatTile } from "./StatTile";
import { ForecastTable } from "./ForecastTable";
import { HealthBar } from "./HealthBar";
import { ApiFeed } from "./ApiFeed";
import { LogDrawer } from "./LogDrawer";
import { ScorePanel } from "./ScorePanel";
import { NewsDrawer } from "./NewsDrawer";
import { usePolling } from "./usePolling";
import { formatPct, formatRelativeUpdatedAt, formatUsd } from "./format";

export default function App() {
  const { data: forecasts, error } = usePolling<Forecast[]>("/api/forecasts", 10_000);
  const { data: health } = usePolling<ApiHealth[]>("/api/health", 10_000);

  const sorted = forecasts
    ? [...forecasts].sort((a, b) => new Date(a.deadline).getTime() - new Date(b.deadline).getTime())
    : [];

  const spot = sorted[0]?.spot_price;
  const sigma = sorted[0]?.sigma;
  const lastUpdated = sorted[0]?.updated_at;
  const edges = sorted.map((f) => f.edge).filter((e): e is number => e !== null);
  const avgAbsEdge = edges.length ? edges.reduce((a, b) => a + Math.abs(b), 0) / edges.length : null;

  return (
    <div style={{ maxWidth: 1080, margin: "0 auto", padding: "2.5rem 1.5rem 6rem" }}>
      <header style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, margin: 0 }}>delphi</h1>
        <p style={{ color: "var(--text-secondary)", marginTop: 6, fontSize: 14 }}>
          Modelo de probabilidade vs. Polymarket para eventos do BTC.
	  Feito por: Mikael, Allan, Vinicius
        </p>
      </header>

      <HealthBar health={health} />

      <div
        style={{
          display: "flex",
          gap: "0.9rem",
          flexWrap: "wrap",
          marginBottom: "1.75rem",
        }}
      >
        <StatTile label="Tracked markets" value={forecasts ? String(forecasts.length) : "—"} />
        <StatTile label="BTC spot" value={spot ? formatUsd(spot) : "—"} accent="var(--series-blue)" />
        <StatTile label="Volatility (ann.)" value={sigma ? formatPct(sigma) : "—"} />
        <StatTile
          label="Avg |edge|"
          value={avgAbsEdge !== null ? formatPct(avgAbsEdge) : "—"}
          accent={avgAbsEdge !== null ? "var(--series-orange)" : undefined}
        />
      </div>

      {error && (
        <div
          style={{
            marginBottom: "1rem",
            padding: "0.75rem 1rem",
            borderRadius: 8,
            background: "color-mix(in srgb, var(--critical) 12%, transparent)",
            color: "var(--critical)",
            fontSize: 13,
          }}
        >
          Failed to load forecasts: {error}
        </div>
      )}

      <ForecastTable forecasts={sorted} />

      <div style={{ marginTop: "1.75rem" }}>
        <ScorePanel />
      </div>

      <footer
        style={{
          margin: "1.25rem 0 2rem",
          paddingTop: "1rem",
          borderTop: "1px solid var(--border)",
          fontSize: 12,
          color: "var(--text-muted)",
          display: "flex",
          flexWrap: "wrap",
          gap: "0.5rem 1.5rem",
          justifyContent: "space-between",
        }}
      >
        <span>
          {lastUpdated ? `Last updated ${formatRelativeUpdatedAt(lastUpdated)}` : " "} · refreshes
          every 10s
        </span>
        <span>
          Feito por: <strong style={{ color: "var(--text-primary)" }}>Mikael</strong>,{" "}
          <strong style={{ color: "var(--text-primary)" }}>Allan</strong> e{" "}
          <strong style={{ color: "var(--text-primary)" }}>Vinicius</strong> · Delphi ·{" "}
          <a
            href="https://pt.wikipedia.org/wiki/Movimento_browniano_geom%C3%A9trico"
            target="_blank"
            rel="noreferrer noopener"
            style={{ color: "var(--text-primary)", textDecoration: "underline" }}
          >
            modelo GBM
          </a>{" "}
          sobre mercados Polymarket, preço e volatilidade da Coinbase, notícias via Cointelegraph
          RSS
        </span>
      </footer>

      <ApiFeed />

      <NewsDrawer />

      <LogDrawer />
    </div>
  );
}
