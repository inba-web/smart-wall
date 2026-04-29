import { ShieldAlert } from 'lucide-react';
import { StatCard } from '../components/common/StatCard';

export function DashboardPage({ metrics, enforcement, devices }) {
  const violations = Object.values(devices)
    .flatMap((d) => d.traffic || [])
    .filter((t) => t.blocked)
    .slice(0, 8);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard label="Connected Devices" value={metrics.totalDevices} />
        <StatCard label="Traffic Events" value={metrics.trafficEvents} />
        <StatCard label="Active Policies" value={metrics.activePolicies} />
        <StatCard label="Blocked Events" value={metrics.blockedEvents} tone={metrics.blockedEvents > 0 ? 'danger' : 'success'} />
      </div>

      <div className="enterprise-card p-5">
        <p className="text-sm text-[var(--text-muted)]">Enforcement status</p>
        <p className="text-lg mt-1 text-[var(--text-primary)]">{enforcement?.status || 'idle'}</p>
        <p className="text-sm mt-2 text-[var(--text-muted)]">{enforcement?.message || 'Policy engine standby.'}</p>
      </div>

      <div className="enterprise-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <ShieldAlert size={18} className="text-red-400" />
          <h3 className="text-[var(--text-primary)] font-semibold">Recent Violations</h3>
        </div>
        <div className="space-y-2">
          {violations.length === 0 && (
            <p className="text-sm text-[var(--text-muted)]">No recent violations detected.</p>
          )}
          {violations.map((entry, index) => (
            <div key={`${entry.domain}-${entry.time}-${index}`} className="rounded-lg border border-red-500/20 bg-red-500/8 px-3 py-2 flex justify-between">
              <span className="text-sm text-[var(--text-primary)]">{entry.domain}</span>
              <span className="text-xs text-[var(--text-muted)]">{entry.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
