import { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { RuleToggleCard } from '../components/common/RuleToggleCard';

const RULE_META = [
  { key: 'social_media', title: 'Social Media', description: 'Instagram, Facebook, TikTok and similar' },
  { key: 'streaming', title: 'Streaming', description: 'YouTube, Netflix, Prime Video and similar' },
  { key: 'gaming', title: 'Gaming', description: 'Roblox, Poki, PUBG and similar' },
];

export function PoliciesPage({
  rules,
  blockedServices,
  strictMode,
  toggleRule,
  toggleStrictMode,
  addServiceBlock,
  removeServiceBlock,
}) {
  const [input, setInput] = useState('');

  const onAdd = async () => {
    const domain = input.trim().toLowerCase();
    if (!domain) return;
    await addServiceBlock(domain);
    setInput('');
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <section className="enterprise-card p-5 space-y-3">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">Category Policies</h2>
        <RuleToggleCard
          title="Strict Mode"
          description="Block all hotspot client internet traffic (best effort, requires admin)."
          active={strictMode}
          onToggle={toggleStrictMode}
        />
        {RULE_META.map((rule) => (
          <RuleToggleCard
            key={rule.key}
            title={rule.title}
            description={rule.description}
            active={Boolean(rules[rule.key])}
            onToggle={() => toggleRule(rule.key)}
          />
        ))}
      </section>

      <section className="enterprise-card p-5">
        <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-3">Custom Service Blocking</h2>
        <div className="flex gap-2 mb-4">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onAdd()}
            placeholder="example.com"
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text-primary)]"
          />
          <button onClick={onAdd} className="rounded-lg px-3 bg-[var(--accent)] text-white">
            <Plus size={16} />
          </button>
        </div>

        <div className="space-y-2 max-h-80 overflow-auto">
          {blockedServices.map((domain) => (
            <div key={domain} className="flex justify-between rounded-md border border-[var(--border)] bg-[var(--surface)] px-3 py-2">
              <span className="text-sm text-[var(--text-primary)]">{domain}</span>
              <button onClick={() => removeServiceBlock(domain)} className="text-[var(--text-muted)] hover:text-red-400">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          {blockedServices.length === 0 && (
            <p className="text-sm text-[var(--text-muted)]">No custom services added yet.</p>
          )}
        </div>
      </section>
    </div>
  );
}
