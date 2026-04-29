export function InsightsPage({ devices, enforcement, blockedServices }) {
  const traffic = Object.values(devices).flatMap((d) => d.traffic || []);
  const topDomains = Object.entries(
    traffic.reduce((acc, entry) => {
      const key = entry.domain || 'unknown';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {})
  )
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  return (
    <div className="space-y-6">
      <div className="enterprise-card p-5">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">Top Visited Services</h2>
        <div className="mt-4 space-y-2">
          {topDomains.map(([domain, count]) => (
            <div key={domain} className="flex justify-between rounded-md border border-[var(--border)] bg-[var(--surface)] px-3 py-2">
              <span className="text-sm text-[var(--text-primary)]">{domain}</span>
              <span className="text-xs text-[var(--text-muted)]">{count} hits</span>
            </div>
          ))}
          {topDomains.length === 0 && (
            <p className="text-sm text-[var(--text-muted)]">Waiting for enough live traffic data.</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="enterprise-card p-5">
          <h3 className="text-base font-semibold text-[var(--text-primary)]">Policy Engine</h3>
          <p className="mt-2 text-sm text-[var(--text-muted)]">Status: {enforcement?.status || 'idle'}</p>
          <p className="mt-2 text-sm text-[var(--text-muted)]">{enforcement?.message || 'No recent engine activity.'}</p>
        </div>
        <div className="enterprise-card p-5">
          <h3 className="text-base font-semibold text-[var(--text-primary)]">Custom Blocks</h3>
          <p className="mt-2 text-3xl font-semibold text-[var(--text-primary)]">{blockedServices.length}</p>
          <p className="mt-2 text-sm text-[var(--text-muted)]">Domain rules managed by administrators.</p>
        </div>
      </div>
    </div>
  );
}
