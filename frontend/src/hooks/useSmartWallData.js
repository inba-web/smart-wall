import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';

export function useSmartWallData() {
  const [devices, setDevices] = useState({});
  const [rules, setRules] = useState({});
  const [blockedServices, setBlockedServices] = useState([]);
  const [strictMode, setStrictMode] = useState(false);
  const [enforcement, setEnforcement] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [devicesRes, rulesRes] = await Promise.all([api.getDevices(), api.getRules()]);
      setDevices(devicesRes.data.devices || {});
      setRules(rulesRes.data.rules || {});
      setBlockedServices(rulesRes.data.blocked_services || []);
      setStrictMode(Boolean(rulesRes.data.strict_mode));
      setEnforcement(rulesRes.data.enforcement || null);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching SmartWall data:', error);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const toggleRule = async (category) => {
    const newValue = !rules[category];
    const res = await api.toggleRule(category, newValue);
    setRules(res.data.rules || {});
    setEnforcement(res.data.enforcement || null);
  };

  const addServiceBlock = async (domain) => {
    const res = await api.addBlockedService(domain);
    setBlockedServices(res.data.blocked_services || []);
    setEnforcement(res.data.enforcement || null);
  };

  const removeServiceBlock = async (domain) => {
    const res = await api.removeBlockedService(domain);
    setBlockedServices(res.data.blocked_services || []);
    setEnforcement(res.data.enforcement || null);
  };

  const toggleStrictMode = async () => {
    const next = !strictMode;
    const res = await api.setStrictMode(next);
    setStrictMode(Boolean(res.data.strict_mode));
    setEnforcement(res.data.enforcement || null);
  };

  const metrics = useMemo(() => {
    const deviceList = Object.values(devices);
    const totalDevices = deviceList.length;
    const trafficEvents = deviceList.flatMap((d) => d.traffic || []);
    const blockedEvents = trafficEvents.filter((t) => t.blocked).length;
    return {
      totalDevices,
      trafficEvents: trafficEvents.length,
      blockedEvents,
      activePolicies: Object.values(rules).filter(Boolean).length,
    };
  }, [devices, rules]);

  return {
    devices,
    rules,
    blockedServices,
    strictMode,
    enforcement,
    loading,
    metrics,
    toggleRule,
    toggleStrictMode,
    addServiceBlock,
    removeServiceBlock,
  };
}
