import React from 'react';
import { LayoutDashboard, TrendingUp, BarChart3, CloudSun } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const menuItems = [
    { id: 'dashboard', label: 'Tổng Quan Thời Tiết', icon: LayoutDashboard },
    { id: 'forecast', label: 'So Sánh Dự Báo AI', icon: TrendingUp },
    { id: 'evaluation', label: 'Đánh Giá Hiệu Năng', icon: BarChart3 },
  ];

  return (
    <nav className="navbar-container">
      <div className="navbar-brand">
        <div className="brand-logo">
          <CloudSun className="logo-icon animate-pulse" />
        </div>
        <div className="brand-info">
          <h1>WeaPredict AI</h1>
          <p>Hệ thống Dự báo Thời tiết 3 Miền</p>
        </div>
      </div>
      
      <div className="navbar-menu">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              className={`menu-item-btn ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon className="menu-icon" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      <div className="navbar-footer">
        <p>© 2026 Đồ Án Tốt Nghiệp</p>
        <span>Xây dựng Hệ thống Dự báo AI</span>
      </div>
    </nav>
  );
}
