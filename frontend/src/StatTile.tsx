interface Props {
  label: string;
  value: string;
  accent?: string;
}

export function StatTile({ label, value, accent }: Props) {
  return (
    <div
      style={{
        background: "var(--surface-1)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        padding: "1rem 1.25rem",
        flex: "1 1 160px",
        minWidth: 160,
      }}
    >
      <div
        style={{
          fontSize: 12,
          textTransform: "uppercase",
          letterSpacing: "0.04em",
          color: "var(--text-muted)",
          marginBottom: 6,
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: 28,
          fontWeight: 600,
          color: accent ?? "var(--text-primary)",
          whiteSpace: "nowrap",
        }}
      >
        {value}
      </div>
    </div>
  );
}
