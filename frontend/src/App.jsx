import { Routes, Route } from 'react-router-dom';
import { Activity } from 'lucide-react';
import { AppShell } from './components/layout/AppShell';
import { useSmartWallData } from './hooks/useSmartWallData';
import { DashboardPage } from './pages/DashboardPage';
import { DevicesPage } from './pages/DevicesPage';
import { PoliciesPage } from './pages/PoliciesPage';
import { InsightsPage } from './pages/InsightsPage';

function App() {
  const {
    devices,
    rules,
    blockedServices,
    strictMode,
    enforcement,
    runtime,
    loading,
    metrics,
    toggleRule,
    toggleStrictMode,
    addServiceBlock,
    removeServiceBlock,
  } = useSmartWallData();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center enterprise-bg">
        <div className="animate-spin text-[var(--accent)]">
          <Activity size={44} />
        </div>
      </div>
    );
  }

  return (
    <AppShell enforcement={enforcement} runtime={runtime}>
      <Routes>
        <Route path="/" element={<DashboardPage metrics={metrics} enforcement={enforcement} devices={devices} />} />
        <Route path="/devices" element={<DevicesPage devices={devices} />} />
        <Route
          path="/policies"
          element={
            <PoliciesPage
              rules={rules}
              blockedServices={blockedServices}
              strictMode={strictMode}
              toggleRule={toggleRule}
              toggleStrictMode={toggleStrictMode}
              addServiceBlock={addServiceBlock}
              removeServiceBlock={removeServiceBlock}
            />
          }
        />
        <Route
          path="/insights"
          element={<InsightsPage devices={devices} enforcement={enforcement} blockedServices={blockedServices} />}
        />
      </Routes>
    </AppShell>
  );
}

export default App;
