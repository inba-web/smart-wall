import { Globe, Monitor, Smartphone } from 'lucide-react';

export function DevicesPage({ devices }) {
  return (
    <div className="space-y-4">
      {Object.entries(devices).map(([ip, device]) => (
        <div key={ip} className="enterprise-card p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="rounded-lg p-2 bg-[var(--surface)] border border-[var(--border)]">
              {device.name?.toLowerCase().includes('iphone') ? <Smartphone size={18} /> : <Monitor size={18} />}
            </div>
            <div>
              <h3 className="font-semibold text-[var(--text-primary)]">{device.name}</h3>
              <p className="text-xs text-[var(--text-muted)]">{ip} | {device.mac}</p>
            </div>
          </div>
          <div className="space-y-2">
            <p className="text-xs uppercase tracking-wide text-[var(--text-muted)] flex items-center gap-2">
              <Globe size={12} />
              Recent Navigation
            </p>
            {(device.traffic || []).slice(0, 12).map((site, index) => (
              <div key={`${site.domain}-${site.time}-${index}`} className="rounded-md border border-[var(--border)] bg-[var(--surface)] px-3 py-2 flex justify-between items-center">
                <div>
                  <p className="text-sm text-[var(--text-primary)]">{site.domain}</p>
                  {site.remote_ip && <p className="text-[11px] text-[var(--text-muted)]">{site.remote_ip}</p>}
                </div>
                <div className="text-right">
                  <p className="text-xs text-[var(--text-muted)]">{site.time}</p>
                  <p className={`text-xs mt-1 ${site.blocked ? 'text-red-400' : 'text-emerald-400'}`}>
                    {site.blocked ? 'Blocked' : 'Allowed'}
                  </p>
                </div>
              </div>
            ))}
            {(!device.traffic || device.traffic.length === 0) && (
              <p className="text-sm text-[var(--text-muted)]">No traffic observed yet.</p>
            )}
          </div>
        </div>
      ))}
      {Object.keys(devices).length === 0 && (
        <div className="enterprise-card p-6 text-sm text-[var(--text-muted)]">No active hotspot devices found.</div>
      )}
    </div>
  );
}
