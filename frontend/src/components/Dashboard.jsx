import React, { useState, useEffect } from 'react';
import { Sun, Cloud, CloudRain, Wind, Droplets, Gauge, Compass, RefreshCw, AlertCircle } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8001/api';

// Ánh xạ mã thời tiết Meteostat (coco) sang tiếng Việt và Icon
export function getWeatherStatus(coco) {
  const code = parseInt(coco);
  if (isNaN(code)) return { text: 'Không rõ', icon: Cloud, color: '#9ca3af' };
  
  if (code === 1 || code === 2) {
    return { text: 'Quang đãng, Ít mây', icon: Sun, color: '#f59e0b' };
  } else if (code === 3 || code === 4) {
    return { text: 'Nhiều mây', icon: Cloud, color: '#a8a29e' };
  } else if (code >= 5 && code <= 6) {
    return { text: 'Sương mù', icon: Cloud, color: '#cbd5e1' };
  } else if (code >= 7 && code <= 11) {
    return { text: 'Có mưa', icon: CloudRain, color: '#3b82f6' };
  } else if (code >= 17 && code <= 18) {
    return { text: 'Có dông bão', icon: CloudRain, color: '#8b5cf6' };
  } else {
    return { text: 'Mây thay đổi', icon: Cloud, color: '#6b7280' };
  }
}

export default function Dashboard() {
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCurrentWeather = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/weather/current`);
      if (!response.ok) {
        throw new Error('Không thể kết nối đến máy chủ API.');
      }
      const data = await response.json();
      setWeatherData(data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Đã xảy ra lỗi khi tải dữ liệu.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentWeather();
  }, []);

  const getCityNameVN = (city) => {
    switch (city) {
      case 'Ha Noi': return 'Thủ Đô Hà Nội';
      case 'Da Nang': return 'Thành Phố Đà Nẵng';
      case 'TP HCM': return 'Thành Phố Hồ Chí Minh';
      default: return city;
    }
  };

  if (loading) {
    return (
      <div className="tab-loading-container">
        <RefreshCw className="loading-spinner" />
        <p>Đang tải dữ liệu thời tiết hiện tại từ các trạm khí tượng...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="tab-error-container">
        <AlertCircle className="error-icon" />
        <p>Lỗi kết nối API: {error}</p>
        <button onClick={fetchCurrentWeather} className="btn-retry">
          Thử Lại <RefreshCw className="btn-icon-spin" />
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard-view-container">
      <div className="view-header">
        <div>
          <h2>Tổng Quan Thời Tiết Hiện Tại</h2>
          <p className="subtitle">Thông tin thực tế ghi nhận trực tiếp từ các trạm khí tượng theo thời gian thực</p>
        </div>
        <button onClick={fetchCurrentWeather} className="btn-refresh">
          Cập nhật <RefreshCw size={16} />
        </button>
      </div>

      <div className="weather-cards-grid">
        {weatherData && Object.entries(weatherData).map(([cityKey, data]) => {
          const status = getWeatherStatus(data.coco);
          const WeatherIcon = status.icon;
          
          return (
            <div key={cityKey} className="weather-glass-card">
              <div className="card-glow" style={{ background: `radial-gradient(circle at 80% 20%, ${status.color}15 0%, transparent 60%)` }} />
              
              <div className="card-top">
                <div className="card-title">
                  <h3>{getCityNameVN(cityKey)}</h3>
                  <span className="station-code">Trạm: {data.city}</span>
                </div>
                <div className="card-main-icon-container" style={{ color: status.color }}>
                  <WeatherIcon className="card-weather-icon" />
                </div>
              </div>

              <div className="temp-section">
                <div className="temp-val-container">
                  <span className="temp-val">{data.temp !== null ? data.temp.toFixed(1) : '--'}</span>
                  <span className="temp-unit">°C</span>
                </div>
                <div className="weather-status-badge" style={{ borderColor: `${status.color}30`, backgroundColor: `${status.color}10`, color: status.color }}>
                  {status.text}
                </div>
              </div>

              <div className="card-divider" />

              <div className="details-grid">
                <div className="detail-item">
                  <div className="detail-icon-wrapper">
                    <Droplets className="detail-icon text-cyan" />
                  </div>
                  <div className="detail-info">
                    <span className="detail-label">Độ ẩm</span>
                    <span className="detail-value">{data.rhum !== null ? `${data.rhum.toFixed(0)}%` : '--'}</span>
                  </div>
                </div>

                <div className="detail-item">
                  <div className="detail-icon-wrapper">
                    <Wind className="detail-icon text-blue" />
                  </div>
                  <div className="detail-info">
                    <span className="detail-label">Tốc độ gió</span>
                    <span className="detail-value">{data.wspd !== null ? `${data.wspd.toFixed(1)} km/h` : '--'}</span>
                  </div>
                </div>

                <div className="detail-item">
                  <div className="detail-icon-wrapper">
                    <Gauge className="detail-icon text-emerald" />
                  </div>
                  <div className="detail-info">
                    <span className="detail-label">Áp suất</span>
                    <span className="detail-value">{data.pres !== null ? `${data.pres.toFixed(1)} hPa` : '--'}</span>
                  </div>
                </div>

                <div className="detail-item">
                  <div className="detail-icon-wrapper">
                    <Compass className="detail-icon text-amber" />
                  </div>
                  <div className="detail-info">
                    <span className="detail-label">Hướng gió</span>
                    <span className="detail-value">{data.wdir !== null ? `${data.wdir.toFixed(0)}°` : '--'}</span>
                  </div>
                </div>
              </div>

              <div className="card-bottom-info">
                <span className="update-label">Cập nhật lúc:</span>
                <span className="update-time">{data.time}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="dashboard-extra-info glass-panel">
        <h3>Giới thiệu về các Mô hình Dự báo Thời tiết AI</h3>
        <div className="info-cards-row">
          <div className="info-item-card">
            <span className="model-tag tag-lr">Linear Regression</span>
            <p>Mô hình hồi quy tuyến tính làm cơ sở so sánh (Baseline). Dự báo nhanh chóng dựa trên quan hệ tuyến tính của các biến khí tượng.</p>
          </div>
          <div className="info-item-card">
            <span className="model-tag tag-xgb">XGBoost Regressor</span>
            <p>Thuật toán học máy thúc đẩy độ dốc mạnh mẽ (Gradient Boosting). Học các mối quan hệ phi tuyến tính phức tạp của đặc trưng thời tiết.</p>
          </div>
          <div className="info-item-card">
            <span className="model-tag tag-lstm">LSTM Network</span>
            <p>Mạng thần kinh nhớ dài-ngắn (Deep Learning). Chuyên xử lý chuỗi thời gian, học các quy luật phụ thuộc thời gian trong 24 giờ trước đó.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
