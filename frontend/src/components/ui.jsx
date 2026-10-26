// Primitives UI réutilisables + icônes SVG (aucune dépendance externe).

const PATHS = {
  profile: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 8a7 7 0 0 1 14 0",
  reco: "M12 3l2.09 5.26L20 9l-4 3.34L17.18 19 12 15.9 6.82 19 8 12.34 4 9l5.91-.74L12 3Z",
  target:
    "M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0 M12 12m-5 0a5 5 0 1 0 10 0a5 5 0 1 0 -10 0 M12 12m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0",
  chart: "M4 20V10 M10 20V4 M16 20v-7 M22 20H2",
  search: "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm10 2-4.35-4.35",
  refresh:
    "M21 12a9 9 0 1 1-2.64-6.36M21 3v6h-6",
  check: "M20 6 9 17l-5-5",
  alert: "M12 9v4m0 4h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z",
  lock: "M19 11H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2Zm-3 0V7a4 4 0 0 0-8 0v4",
  database:
    "M12 8c4.42 0 8-1.34 8-3s-3.58-3-8-3-8 1.34-8 3 3.58 3 8 3Zm8-3v14c0 1.66-3.58 3-8 3s-8-1.34-8-3V5",
  box: "M21 8V16a2 2 0 0 1-1 1.73l-7 4a2 2 0 0 1-2 0l-7-4A2 2 0 0 1 3 16V8a2 2 0 0 1 1-1.73l7-4a2 2 0 0 1 2 0l7 4A2 2 0 0 1 21 8ZM3.27 7 12 12l8.73-5 M12 22V12",
  layers:
    "M12 2 2 7l10 5 10-5-10-5Z M2 17l10 5 10-5 M2 12l10 5 10-5",
  spark: "M9 3v4M7 5h4M17 11v4M15 13h4M12 8l1.6 3.4L17 13l-3.4 1.6L12 18l-1.6-3.4L7 13l3.4-1.6L12 8Z",
};

export function Icon({ name, size = 16, className = "" }) {
  const d = PATHS[name];
  if (!d) return null;
  return (
    <svg
      className={`ico ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={d} />
    </svg>
  );
}

export function Spinner() {
  return <span className="spinner" aria-label="chargement" />;
}

export function Notice({ kind = "info", children }) {
  const icon = kind === "error" ? "alert" : kind === "ok" ? "check" : "spark";
  return (
    <div className={`notice ${kind}`} role={kind === "error" ? "alert" : "status"}>
      <Icon name={icon} />
      <span>{children}</span>
    </div>
  );
}

export function EmptyState({ icon = "box", title, children }) {
  return (
    <div className="empty">
      <Icon name={icon} size={30} />
      {title && <strong>{title}</strong>}
      {children && <span>{children}</span>}
    </div>
  );
}

export function Chips({ items = [] }) {
  if (!items.length) return null;
  return (
    <div className="chips">
      {items.map((it, i) => (
        <span className="chip" key={`${it}-${i}`}>
          {it}
        </span>
      ))}
    </div>
  );
}
