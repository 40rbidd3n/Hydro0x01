import { useState, useRef } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Server,
  Settings,
  Activity,
  X,
  Droplets,
  ThermometerSun,
  Database,
  LogOut,
  Gauge,
} from 'lucide-react';
import { useAuthStore } from '../../store/useAuthStore';
import { SystemAlertsBanner } from './SystemAlertsBanner';
import { DevMenu } from './DevMenu';
import { StatusHeader } from './StatusHeader';

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [devMenuOpen, setDevMenuOpen] = useState(false);
  const devClicksRef = useRef(0);

  const logout = useAuthStore(state => state.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleLogoClick = () => {
    devClicksRef.current += 1;
    if (devClicksRef.current >= 5) {
      setDevMenuOpen(true);
      devClicksRef.current = 0;
    }
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/devices', label: 'Devices', icon: Server },
    { path: '/controls', label: 'Water Controls', icon: Droplets },
    { path: '/environment', label: 'Environment', icon: ThermometerSun },
    { path: '/history', label: 'History', icon: Activity },
    { path: '/configuration', label: 'Configuration', icon: Settings },
    { path: '/calibration', label: 'Calibration', icon: Gauge },
    { path: '/ota', label: 'OTA Update', icon: Database },
  ];

  return (
    <div className="layout">
      {/* Sidebar */}
      <nav className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ color: 'var(--cyan)', cursor: 'pointer' }} onClick={handleLogoClick}>
              <img src="/assets/logo-white.png" alt="HydroponicOne Logo" style={{ height: '45px' /*'24px'*/, width: 'auto' }} />
            </div>
            {/*<span style={{ fontWeight: 600, fontSize: 18 }}>HydroponicOne</span>*/}
          </div>
          <button className="btn mobile-only" style={{ padding: 8 }} onClick={() => setSidebarOpen(false)}>
            <X size={20} />
          </button>
        </div>

        <div className="nav-links">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>

        <div style={{ padding: '20px', marginTop: 'auto' }}>
          <button onClick={handleLogout} className="btn" style={{ width: '100%', justifyContent: 'center' }}>
            <LogOut size={18} /> Logout
          </button>
        </div>
      </nav>

      {/* Overlay */}
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}

      {/* Main Content */}
      <main className="main-content">
        <StatusHeader onMenuClick={() => setSidebarOpen(true)} />
        <SystemAlertsBanner />
        <div className="page-scroll-area">
          <div className="animate-fade-in" style={{ maxWidth: '1400px', margin: '0 auto' }}>
            <Outlet />
          </div>
        </div>
        {devMenuOpen && <DevMenu onClose={() => setDevMenuOpen(false)} />}
      </main>
    </div>
  );
}
