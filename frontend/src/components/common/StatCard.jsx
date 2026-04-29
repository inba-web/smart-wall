export function StatCard({ label, value, tone = 'default' }) {
  const toneClass =
    tone === 'danger'
      ? 'text-red-400'
      : tone === 'success'
        ? 'text-emerald-400'
        : 'text-[var(--text-primary)]';

  return (
    <div className="enterprise-card p-4">
      <p className="text-xs uppercase tracking-wide text-[var(--text-muted)]">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${toneClass}`}>{value}</p>
    </div>
  );
}
