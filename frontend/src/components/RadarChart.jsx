// Radar chart minimal en SVG (aucune dépendance externe).
// Faute de pondération d'intérêt exposée par le profil, tous les axes sont
// tracés à rayon plein ; à enrichir quand le profil fournira des poids.

export default function RadarChart({ labels = [], size = 260 }) {
  if (!labels.length) {
    return <p className="muted">Aucun centre d'intérêt à afficher.</p>;
  }

  const center = size / 2;
  const radius = center - 46;
  const n = labels.length;
  const angle = (i) => (Math.PI * 2 * i) / n - Math.PI / 2;

  const point = (i, r) => [
    center + r * Math.cos(angle(i)),
    center + r * Math.sin(angle(i)),
  ];

  const polygon = labels.map((_, i) => point(i, radius).join(",")).join(" ");

  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="radar" role="img">
      {/* cercles de repère */}
      {[0.33, 0.66, 1].map((f) => (
        <circle
          key={f}
          cx={center}
          cy={center}
          r={radius * f}
          className="radar-grid"
        />
      ))}
      {/* rayons */}
      {labels.map((_, i) => {
        const [x, y] = point(i, radius);
        return (
          <line key={i} x1={center} y1={center} x2={x} y2={y} className="radar-grid" />
        );
      })}
      {/* aire du profil */}
      <polygon points={polygon} className="radar-area" />
      {/* sommets */}
      {labels.map((_, i) => {
        const [x, y] = point(i, radius);
        return <circle key={`d${i}`} cx={x} cy={y} r={3} className="radar-dot" />;
      })}
      {/* étiquettes */}
      {labels.map((label, i) => {
        const [x, y] = point(i, radius + 18);
        const anchor = Math.abs(x - center) < 6 ? "middle" : x < center ? "end" : "start";
        return (
          <text
            key={label + i}
            x={x}
            y={y}
            className="radar-label"
            textAnchor={anchor}
            dominantBaseline="middle"
          >
            {label.length > 14 ? `${label.slice(0, 13)}…` : label}
          </text>
        );
      })}
    </svg>
  );
}
