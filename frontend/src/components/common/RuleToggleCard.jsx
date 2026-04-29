export function RuleToggleCard({ title, description, active, onToggle }) {
  return (
    <button
      onClick={onToggle}
      className={`w-full text-left enterprise-card p-4 border transition-colors ${
        active ? 'border-red-400/40 bg-red-400/8' : 'border-[var(--border)]'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className={`font-medium ${active ? 'text-red-300' : 'text-[var(--text-primary)]'}`}>{title}</p>
          <p className="text-xs mt-1 text-[var(--text-muted)]">{description}</p>
        </div>
        <div
          className={`w-10 h-6 rounded-full p-1 transition-colors ${
            active ? 'bg-red-500/80' : 'bg-[var(--surface)]'
          }`}
        >
          <div className={`h-4 w-4 rounded-full bg-white transition-transform ${active ? 'translate-x-4' : ''}`} />
        </div>
      </div>
    </button>
  );
}
