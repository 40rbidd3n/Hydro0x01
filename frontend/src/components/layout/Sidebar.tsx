import { NavLink } from 'react-router-dom';
import { useSystemStore } from '../../store/useSystemStore';
import {
  LayoutDashboard,
  Monitor,
  Sliders,
  Settings,
  Upload,
  History,
  Thermometer,
  X,
  Gauge,
} from 'lucide-react';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', href: '/' },
  { icon: Monitor, label: 'Devices', href: '/devices' },
  { icon: Sliders, label: 'Controls', href: '/controls' },
  { icon: Thermometer, label: 'Environment', href: '/environment' },
  { icon: Settings, label: 'Configuration', href: '/configuration' },
  { icon: Gauge, label: 'Calibration', href: '/calibration' },
  { icon: Upload, label: 'OTA Update', href: '/ota' },
  { icon: History, label: 'History', href: '/history' },
];

export function Sidebar() {
  const { sidebarOpen, setSidebarOpen } = useSystemStore();

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        {/* Brand */}
        <div className="sidebar-brand">
          <div className="sidebar-logo">
            <img
              src="/assets/logo-white.png"
              alt="HydroponicOne Logo"
              style={{ height: '32px', width: 'auto', objectFit: 'contain' }}
            />
            <span className="sidebar-logo-text">HydroponicOne</span>
          </div>
          <button
            className="sidebar-close btn-icon"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={18} />
          </button>
        </div>

        {/* Nav */}
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.href}
              to={item.href}
              end={item.href === '/'}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'sidebar-link-active' : ''}`
              }
              onClick={() => setSidebarOpen(false)}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <span>HydroponicOne v1.0</span>
          <span>Professional Hydroponic Control</span>
        </div>
      </aside>

      <style>{`
        .sidebar-overlay {
          display: none;
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.6);
          backdrop-filter: blur(4px);
          z-index: 40;
        }

        .sidebar {
          width: var(--sidebar-width);
          height: 100vh;
          position: fixed;
          left: 0;
          top: 0;
          z-index: 50;
          display: flex;
          flex-direction: column;
          background: var(--bg-surface);
          border-right: 1px solid var(--border-default);
          transition: transform var(--transition-normal);
        }

        .sidebar-brand {
          height: var(--header-height);
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 20px;
          border-bottom: 1px solid var(--border-default);
          flex-shrink: 0;
        }

        .sidebar-logo {
          display: flex;
          align-items: center;
          gap: 10px;
          color: var(--accent);
        }

        .sidebar-logo-text {
          font-size: 17px;
          font-weight: 700;
          color: var(--text-primary);
          letter-spacing: -0.02em;
        }

        .sidebar-close {
          display: none;
        }

        .sidebar-nav {
          flex: 1;
          overflow-y: auto;
          padding: 16px 12px;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .sidebar-link {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 14px;
          border-radius: var(--radius-md);
          font-size: 14px;
          font-weight: 500;
          color: var(--text-muted);
          text-decoration: none;
          transition: all var(--transition-fast);
          border: 1px solid transparent;
        }

        .sidebar-link:hover {
          color: var(--text-primary);
          background: var(--bg-card);
        }

        .sidebar-link-active {
          color: var(--accent) !important;
          background: var(--accent-bg) !important;
          border-color: var(--accent-border) !important;
        }

        .sidebar-footer {
          padding: 16px 20px;
          border-top: 1px solid var(--border-default);
          display: flex;
          flex-direction: column;
          gap: 2px;
          font-size: 11px;
          color: var(--text-dimmed);
        }

        @media (max-width: 768px) {
          .sidebar-overlay {
            display: block;
          }

          .sidebar {
            width: 280px;
            transform: translateX(-100%);
          }

          .sidebar-open {
            transform: translateX(0);
          }

          .sidebar-close {
            display: flex;
          }
        }
      `}</style>
    </>
  );
}
