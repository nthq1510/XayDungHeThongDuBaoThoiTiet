import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { Calendar, Building2, Eye, EyeOff, RefreshCw, AlertCircle, Table } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8001/api';

export default function Forecast() {
  const [city, setCity] = useState('Ha Noi');
  const [days, setDays] = useState(3); // 1, 3, hoặc 7 ngày
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rawData, setRawData] = useState([]); // Chứa toàn bộ 7 ngày
  const [filteredData, setFilteredData] = useState([]); // Lọc theo số ngày chọn

  // Trạng thái bật/tắt hiển thị các đường trên biểu đồ
  const [visibility, setVisibility] = useState({
    actual: true,
    lr: true,
    xgb: true,
    lstm: true
  });

  const fetchPredictions = async (selectedCity) => {
    try {
      setLoading(true);
      setError(null);
      
      // Gọi API predict (không truyền start/end date để mặc định lấy 7 ngày cuối cùng)
      const response = await fetch(`${API_BASE_URL}/predict?city=${encodeURIComponent(selectedCity)}`);
      if (!response.ok) {
        throw new Error(`Lỗi từ máy chủ: ${response.statusText}`);
      }
      
      const data = await response.json();
      setRawData(data.predictions || []);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Đã xảy ra lỗi khi tải dữ liệu dự báo.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions(city);
  }, [city]);

  // Lọc dữ liệu hiển thị khi số ngày thay đổi hoặc khi rawData thay đổi
  useEffect(() => {
    if (!rawData.length) {
      setFilteredData([]);
      return;
    }

    // Mỗi ngày có 24 bản ghi giờ. Lấy N ngày từ cuối danh sách lên đầu
    const limit = days * 24;
    const sliced = rawData.slice(-limit);
    
    // Format thời gian hiển thị ngắn gọn hơn trên trục X (ví dụ: "22/05 14h")
    const formatted = sliced.map(item => {
      const dt = new Date(item.time);
      const day = String(dt.getDate()).padStart(2, '0');
      const month = String(dt.getMonth() + 1).padStart(2, '0');
      const hour = String(dt.getHours()).padStart(2, '0');
      return {
        ...item,
        formattedTime: `${day}/${month} ${hour}:00`,
        // Làm tròn số thập phân để biểu đồ & tooltip hiển thị đẹp
        actual: parseFloat(item.actual.toFixed(1)),
        lr: parseFloat(item.lr.toFixed(1)),
        xgb: parseFloat(item.xgb.toFixed(1)),
        lstm: parseFloat(item.lstm.toFixed(1)),
        // Tính sai lệch tuyệt đối để hiển thị trong bảng
        err_lr: Math.abs(item.actual - item.lr),
        err_xgb: Math.abs(item.actual - item.xgb),
        err_lstm: Math.abs(item.actual - item.lstm)
      };
    });

    setFilteredData(formatted);
  }, [rawData, days]);

  const toggleLine = (model) => {
    setVisibility(prev => ({
      ...prev,
      [model]: !prev[model]
    }));
  };

  // Custom Tooltip cho Recharts để trông hiện đại hơn
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-chart-tooltip">
          <p className="tooltip-time">{label}</p>
          <div className="tooltip-divider" />
          {payload.map((entry, idx) => (
            <div key={idx} className="tooltip-item" style={{ color: entry.color }}>
              <span className="tooltip-dot" style={{ backgroundColor: entry.color }} />
              <span className="tooltip-name">{entry.name}:</span>
              <span className="tooltip-val">{entry.value} °C</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="forecast-view-container">
      <div className="view-header">
        <div>
          <h2>Biểu Đồ So Sánh Các Mô Hình Dự Báo</h2>
          <p className="subtitle">So sánh nhiệt độ thực tế với kết quả dự báo từ Baseline (LR), XGBoost và LSTM</p>
        </div>
      </div>

      {/* Thanh điều khiển chọn Thành phố & Khoảng thời gian */}
      <div className="control-bar glass-panel">
        <div className="control-group">
          <label><Building2 size={16} /> Thành phố:</label>
          <select value={city} onChange={(e) => setCity(e.target.value)} className="select-input">
            <option value="Ha Noi">Hà Nội</option>
            <option value="Da Nang">Đà Nẵng</option>
            <option value="TP HCM">TP. Hồ Chí Minh</option>
          </select>
        </div>

        <div className="control-group">
          <label><Calendar size={16} /> Phạm vi đối chiếu:</label>
          <div className="radio-group">
            {[1, 3, 7].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`btn-radio ${days === d ? 'active' : ''}`}
              >
                {d} Ngày ({d * 24} giờ)
              </button>
            ))}
          </div>
        </div>

        <button onClick={() => fetchPredictions(city)} className="btn-refresh-predict" title="Tải lại dữ liệu">
          <RefreshCw size={16} />
        </button>
      </div>

      {loading ? (
        <div className="tab-loading-container">
          <RefreshCw className="loading-spinner" />
          <p>Hệ thống AI đang tải các mô hình và suy luận dữ liệu khí hậu...</p>
        </div>
      ) : error ? (
        <div className="tab-error-container">
          <AlertCircle className="error-icon" />
          <p>Lỗi dự báo: {error}</p>
          <button onClick={() => fetchPredictions(city)} className="btn-retry">
            Thử Lại <RefreshCw size={14} />
          </button>
        </div>
      ) : (
        <>
          {/* Biểu đồ chính */}
          <div className="chart-wrapper glass-panel">
            <div className="chart-legend-custom">
              <button onClick={() => toggleLine('actual')} className={`legend-btn ${visibility.actual ? 'active' : 'inactive'}`}>
                <span className="legend-dot" style={{ backgroundColor: 'var(--color-actual)' }} />
                <span>Thực Tế</span>
                {visibility.actual ? <Eye size={14} /> : <EyeOff size={14} />}
              </button>
              <button onClick={() => toggleLine('lr')} className={`legend-btn ${visibility.lr ? 'active' : 'inactive'}`}>
                <span className="legend-dot" style={{ backgroundColor: 'var(--color-lr)' }} />
                <span>Linear Regression (Baseline)</span>
                {visibility.lr ? <Eye size={14} /> : <EyeOff size={14} />}
              </button>
              <button onClick={() => toggleLine('xgb')} className={`legend-btn ${visibility.xgb ? 'active' : 'inactive'}`}>
                <span className="legend-dot" style={{ backgroundColor: 'var(--color-xgb)' }} />
                <span>XGBoost Regressor</span>
                {visibility.xgb ? <Eye size={14} /> : <EyeOff size={14} />}
              </button>
              <button onClick={() => toggleLine('lstm')} className={`legend-btn ${visibility.lstm ? 'active' : 'inactive'}`}>
                <span className="legend-dot" style={{ backgroundColor: 'var(--color-lstm)' }} />
                <span>LSTM Network (Deep Learning)</span>
                {visibility.lstm ? <Eye size={14} /> : <EyeOff size={14} />}
              </button>
            </div>

            <div className="chart-container">
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={filteredData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                  <XAxis 
                    dataKey="formattedTime" 
                    stroke="var(--text-muted)" 
                    fontSize={12} 
                    tickLine={false}
                    axisLine={false}
                    minTickGap={30}
                  />
                  <YAxis 
                    stroke="var(--text-muted)" 
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                    unit="°C"
                    domain={['dataMin - 2', 'dataMax + 2']}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  
                  {visibility.actual && (
                    <Line 
                      type="monotone" 
                      dataKey="actual" 
                      name="Thực Tế" 
                      stroke="var(--color-actual)" 
                      strokeWidth={2.5}
                      dot={false}
                      activeDot={{ r: 6, strokeWidth: 0 }}
                    />
                  )}
                  {visibility.lr && (
                    <Line 
                      type="monotone" 
                      dataKey="lr" 
                      name="Linear Regression" 
                      stroke="var(--color-lr)" 
                      strokeWidth={1.5}
                      strokeDasharray="4 4"
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                  )}
                  {visibility.xgb && (
                    <Line 
                      type="monotone" 
                      dataKey="xgb" 
                      name="XGBoost" 
                      stroke="var(--color-xgb)" 
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 5 }}
                    />
                  )}
                  {visibility.lstm && (
                    <Line 
                      type="monotone" 
                      dataKey="lstm" 
                      name="LSTM Network" 
                      stroke="var(--color-lstm)" 
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 5 }}
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Bảng số liệu chi tiết */}
          <div className="table-wrapper glass-panel">
            <div className="table-header">
              <div className="table-title">
                <Table size={18} />
                <h3>Bảng Số Liệu Chi Tiết & Sai Số Dự Báo Theo Giờ</h3>
              </div>
              <span className="table-info-badge">Đang hiển thị {filteredData.length} giờ gần nhất</span>
            </div>

            <div className="table-scroll-container">
              <table className="forecast-table">
                <thead>
                  <tr>
                    <th>Thời Gian</th>
                    <th className="th-actual">Thực Tế (°C)</th>
                    <th className="th-lr">Baseline LR (°C)</th>
                    <th className="th-lr-err">Độ Lệch LR</th>
                    <th className="th-xgb">XGBoost (°C)</th>
                    <th className="th-xgb-err">Độ Lệch XGB</th>
                    <th className="th-lstm">LSTM (°C)</th>
                    <th className="th-lstm-err">Độ Lệch LSTM</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((row, index) => {
                    // Xác định mô hình có sai số nhỏ nhất dòng này
                    const minErr = Math.min(row.err_lr, row.err_xgb, row.err_lstm);
                    
                    return (
                      <tr key={index}>
                        <td className="td-time">{row.time}</td>
                        <td className="td-actual">{row.actual.toFixed(1)}</td>
                        <td>{row.lr.toFixed(1)}</td>
                        <td className="td-err text-red">
                          +{row.err_lr.toFixed(2)}
                        </td>
                        <td>{row.xgb.toFixed(1)}</td>
                        <td className={`td-err ${row.err_xgb === minErr ? 'text-best' : 'text-orange'}`}>
                          +{row.err_xgb.toFixed(2)}
                          {row.err_xgb === minErr && <span className="best-indicator">✔</span>}
                        </td>
                        <td>{row.lstm.toFixed(1)}</td>
                        <td className={`td-err ${row.err_lstm === minErr ? 'text-best' : 'text-purple'}`}>
                          +{row.err_lstm.toFixed(2)}
                          {row.err_lstm === minErr && <span className="best-indicator">✔</span>}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
