import { NavLink } from 'react-router-dom';
import { Activity, BarChart3, Moon, Shield, Sun, TabletSmartphone } from 'lucide-react';
import { useTheme } from '../../theme/ThemeContext';

const navItems = [
  { to: '/', label: 'Overview', icon: Activity },
  { to: '/devices', label: 'Devices', icon: TabletSmartphone },
  { to: '/policies', label: 'Policies', icon: Shield },
  { to: '/insights', label: 'Insights', icon: BarChart3 },
];

export function AppShell({ children }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen enterprise-bg">
      <header className="sticky top-0 z-10 border-b border-[var(--border)] bg-[var(--panel)]/90 backdrop-blur-md">
        <div className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-xl p-2 bg-[var(--accent-soft)] border border-[var(--accent-border)]">
              <Shield className="text-[var(--accent)]" size={22} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-[var(--text-primary)]">SmartWall Enterprise</h1>
              <p className="text-xs text-[var(--text-muted)]">Network Governance Console</p>
            </div>
          </div>
          <button
            onClick={toggleTheme}
            className="rounded-lg px-3 py-2 text-sm border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] hover:border-[var(--accent-border)] flex items-center gap-2"
          >
            {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
            {theme === 'dark' ? 'Light' : 'Dark'} mode
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-6 grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-6">
        <aside className="enterprise-card p-3 h-fit">
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                      isActive
                        ? 'bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-border)]'
                        : 'text-[var(--text-muted)] hover:bg-[var(--surface)] hover:text-[var(--text-primary)]'
                    }`
                  }
                >
                  <Icon size={16} />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
        </aside>
        <main>{children}</main>
      </div>
    </div>
  );
}
