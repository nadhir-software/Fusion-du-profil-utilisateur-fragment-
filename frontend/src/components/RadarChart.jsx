// Radar chart minimal en SVG (aucune dépendance externe).
// Faute de pondération d'intérêt exposée par le profil, tous les axes sont
// tracés à rayon plein ; à enrichir quand le profil fournira des poids.

export default function RadarChart({ labels = [], size = 260 }) {
  if (!labels.length) {
    return <p className="muted">Aucun centre d'intérêt à afficher.</p>;
  }

  const center = size / 2;
  const radius = center - 40;
  const n = labels.length;
  const angle = (i) => (Math.PI * 2 * i) / n - Math.PI / 2;

  const point = (i, r) => [
    center + r * Math.cos(angle(i)),
    center + r * Math.sin(angle(i)),
  ];

  const polygon = labels
    .map((_, i) => point(i, radius).join(","))
    .join(" ");

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
          <line
            key={i}
            x1={center}
            y1={center}
            x2={x}
            y2={y}
            className="radar-grid"
          />
        );
      })}
      {/* aire du profil */}
      <polygon points={polygon} className="radar-area" />
      {/* étiquettes */}
      {labels.map((label, i) => {
        const [x, y] = point(i, radius + 16);
        return (
          <text
            key={label + i}
            x={x}
            y={y}
            className="radar-label"
            textAnchor="middle"
            dominantBaseline="middle"
          >
            {label}
          </text>
        );
      })}
    </svg>
  );
}
