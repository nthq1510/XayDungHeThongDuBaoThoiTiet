import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { RefreshCw, AlertCircle, Award, CheckCircle, HelpCircle, Image as ImageIcon, TrendingUp, Building2, Calendar } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8001/api';

export default function Evaluation() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeImageTab, setActiveImageTab] = useState('loss'); // loss, comparison, distribution

  // State phục vụ theo dõi sai số thực tế hàng giờ
  const [errorHistory, setErrorHistory] = useState([]);
  const [selectedCity, setSelectedCity] = useState('Ha Noi');
  const [historyLimit, setHistoryLimit] = useState(24);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [historyError, setHistoryError] = useState(null);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/metrics`);
      if (!response.ok) {
        throw new Error('Không thể tải các chỉ số đánh giá từ API.');
      }
      const data = await response.json();
      setMetrics(data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Đã xảy ra lỗi.');
    } finally {
      setLoading(false);
    }
  };

  const fetchErrorHistory = async (city, limit) => {
    try {
      setLoadingHistory(true);
      setHistoryError(null);
      const response = await fetch(`${API_BASE_URL}/predictions/errors?city=${encodeURIComponent(city)}&limit=${limit}`);
      if (!response.ok) {
        throw new Error('Không thể tải lịch sử sai số từ API.');
      }
      const data = await response.json();
      
      const formatted = data.map(item => {
        const dt = new Date(item.time);
        const day = String(dt.getDate()).padStart(2, '0');
        const month = String(dt.getMonth() + 1).padStart(2, '0');
        const hour = String(dt.getHours()).padStart(2, '0');
        return {
          ...item,
          formattedTime: `${day}/${month} ${hour}:00`,
          err_lr: parseFloat(item.err_lr.toFixed(3)),
          err_xgb: parseFloat(item.err_xgb.toFixed(3)),
          err_lstm: parseFloat(item.err_lstm.toFixed(3)),
          actual_temp: parseFloat(item.actual_temp.toFixed(1))
        };
      });
      setErrorHistory(formatted);
    } catch (err) {
      console.error(err);
      setHistoryError(err.message || 'Đã xảy ra lỗi khi tải lịch sử sai số.');
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  useEffect(() => {
    fetchErrorHistory(selectedCity, historyLimit);
  }, [selectedCity, historyLimit]);

  if (loading) {
    return (
      <div className="tab-loading-container">
        <RefreshCw className="loading-spinner" />
        <p>Đang tải dữ liệu đánh giá mô hình...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="tab-error-container">
        <AlertCircle className="error-icon" />
        <p>Lỗi: {error}</p>
        <button onClick={fetchMetrics} className="btn-retry">
          Thử Lại <RefreshCw size={14} />
        </button>
      </div>
    );
  }

  // Định nghĩa các diễn giải cho các chỉ số
  const metricExplanations = {
    MAE: 'Mean Absolute Error (Sai số tuyệt đối trung bình): Cho biết mức độ lệch trung bình của nhiệt độ dự báo so với thực tế bằng độ C. Chỉ số càng nhỏ mô hình càng chính xác.',
    RMSE: 'Root Mean Squared Error (Sai số bình phương trung bình gốc): Đánh giá mức độ sai lệch lớn (phạt nặng các sai số lớn). Chỉ số nhỏ chứng tỏ mô hình dự báo ổn định, ít có sai số đột biến.',
    MAPE: 'Mean Absolute Percentage Error (Sai số phần trăm tuyệt đối trung bình): Sai lệch tương đối tính bằng %. Thể hiện sai số dưới dạng tỷ lệ phần trăm.'
  };

  return (
    <div className="evaluation-view-container">
      <div className="view-header">
        <div>
          <h2>Đánh Giá Hiệu Năng Mô Hình AI</h2>
          <p className="subtitle">Phân tích sai số thực nghiệm của 3 mô hình trên tập dữ liệu kiểm thử độc lập (Test Set)</p>
        </div>
      </div>

      <div className="evaluation-grid">
        {/* Phần 1: Bảng so sánh sai số */}
        <div className="metrics-panel-left glass-panel">
          <div className="panel-title-row">
            <Award className="text-amber" size={20} />
            <h3>Bảng Thống Kê Sai Số Đo Lường</h3>
          </div>
          
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Mô Hình</th>
                <th>MAE (degC)</th>
                <th>RMSE (degC)</th>
                <th>MAPE (%)</th>
              </tr>
            </thead>
            <tbody>
              {metrics && Object.entries(metrics).map(([modelName, values]) => {
                const isBest = modelName.includes('XGBoost');
                return (
                  <tr key={modelName} className={isBest ? 'best-row' : ''}>
                    <td className="td-model-name">
                      {modelName}
                      {isBest && <span className="winner-badge">Tốt Nhất</span>}
                    </td>
                    <td className="td-value font-mono">{values.MAE.toFixed(3)}</td>
                    <td className="td-value font-mono">{values.RMSE.toFixed(3)}</td>
                    <td className="td-value font-mono">{values.MAPE.toFixed(3)}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <div className="metrics-explanation">
            <h4><HelpCircle size={14} /> Ý nghĩa các chỉ số:</h4>
            <ul>
              <li><strong>MAE:</strong> {metricExplanations.MAE}</li>
              <li><strong>RMSE:</strong> {metricExplanations.RMSE}</li>
              <li><strong>MAPE:</strong> {metricExplanations.MAPE}</li>
            </ul>
          </div>
        </div>

        {/* Phần 2: Đồ thị trực quan sai số MAE */}
        <div className="metrics-panel-right glass-panel">
          <div className="panel-title-row">
            <CheckCircle className="text-emerald" size={20} />
            <h3>Trực Quan Hóa Độ Sai Lệch MAE</h3>
          </div>

          <div className="bar-comparison-container">
            {metrics && Object.entries(metrics).map(([modelName, values]) => {
              // Tính tỉ lệ phần trăm dựa trên giá trị MAE tối đa để vẽ thanh tiến trình
              const maxMae = 0.8;
              const percent = Math.min((values.MAE / maxMae) * 100, 100);
              
              let barColor = 'var(--primary)';
              if (modelName.includes('Linear')) barColor = 'var(--color-lr)';
              if (modelName.includes('XGBoost')) barColor = 'var(--color-xgb)';
              if (modelName.includes('LSTM')) barColor = 'var(--color-lstm)';

              return (
                <div key={modelName} className="bar-item">
                  <div className="bar-info-row">
                    <span className="bar-model-name">{modelName}</span>
                    <span className="bar-value" style={{ color: barColor }}>{values.MAE.toFixed(3)} °C</span>
                  </div>
                  <div className="bar-track">
                    <div 
                      className="bar-fill animate-grow" 
                      style={{ 
                        width: `${percent}%`, 
                        background: `linear-gradient(90deg, ${barColor}aa, ${barColor})`,
                        boxShadow: `0 0 10px ${barColor}40`
                      }} 
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="evaluation-summary-box">
            <p><strong>Nhận xét:</strong></p>
            <p className="summary-text">
              Trong các mô hình thử nghiệm, <strong>XGBoost Regressor</strong> đạt kết quả tối ưu nhất với sai số tuyệt đối trung bình 
              <strong> MAE = 0.316 °C</strong> và <strong>RMSE = 0.440 °C</strong>. 
              Mô hình <strong>Linear Regression</strong> (Baseline) đạt hiệu năng bám rất sát nhờ mối tương quan tuyến tính mạnh của nhiệt độ qua các giờ liền kề. 
              Mô hình <strong>LSTM</strong> tuy có cấu trúc Deep Learning phức tạp hơn nhưng đạt sai số cao hơn (MAE = 0.631 °C), 
              điều này có thể do kích thước tập huấn luyện hoặc quá trình tối ưu hóa các tham số LSTM cần cấu hình mạng sâu hơn và thời gian hội tụ dài hơn.
            </p>
          </div>
        </div>
      </div>

      {/* Phần 3: Biểu đồ học tập & So sánh phân phối (Images từ tập huấn luyện) */}
      <div className="charts-gallery-section glass-panel">
        <div className="gallery-header">
          <div className="panel-title-row">
            <ImageIcon className="text-purple" size={20} />
            <h3>Đồ Thị Kết Quả Huấn Luyện & Thực Nghiệm</h3>
          </div>
          <div className="gallery-tabs">
            <button 
              className={`gallery-tab-btn ${activeImageTab === 'loss' ? 'active' : ''}`}
              onClick={() => setActiveImageTab('loss')}
            >
              Lịch Sử Huấn Luyện (LSTM Loss)
            </button>
            <button 
              className={`gallery-tab-btn ${activeImageTab === 'comparison' ? 'active' : ''}`}
              onClick={() => setActiveImageTab('comparison')}
            >
              So Sánh Sai Số Mô Hình
            </button>
            <button 
              className={`gallery-tab-btn ${activeImageTab === 'distribution' ? 'active' : ''}`}
              onClick={() => setActiveImageTab('distribution')}
            >
              Phân Phối Dự Báo
            </button>
          </div>
        </div>

        <div className="gallery-body">
          {activeImageTab === 'loss' && (
            <div className="gallery-slide animate-fade-in">
              <div className="slide-image-container">
                <img 
                  src="/lstm_loss_curve.png" 
                  alt="Biểu đồ suy hao mô hình LSTM" 
                  className="gallery-image"
                  onError={(e) => {
                    e.target.onerror = null; 
                    e.target.src = "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=1000";
                  }}
                />
              </div>
              <div className="slide-description">
                <h4>Đồ thị Loss Curve của mô hình LSTM</h4>
                <p>Biểu diễn sự thay đổi của hàm mất mát (MSE) trên tập huấn luyện (Train Loss) và tập kiểm định (Val Loss) qua 30 Epochs. Sự hội tụ của hai đường chứng minh mô hình không bị quá khớp (overfitting).</p>
              </div>
            </div>
          )}

          {activeImageTab === 'comparison' && (
            <div className="gallery-slide animate-fade-in">
              <div className="slide-image-container">
                <img 
                  src="/model_comparison_metrics.png" 
                  alt="So sánh sai số giữa các mô hình" 
                  className="gallery-image"
                  onError={(e) => {
                    e.target.onerror = null; 
                    e.target.src = "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=1000";
                  }}
                />
              </div>
              <div className="slide-description">
                <h4>Biểu đồ cột so sánh sai số MAE và RMSE</h4>
                <p>Trực quan hóa sự khác biệt về độ lớn của sai số MAE và RMSE trên tập dữ liệu kiểm thử. XGBoost thể hiện sự vượt trội, theo sát sau đó là Baseline Linear Regression.</p>
              </div>
            </div>
          )}

          {activeImageTab === 'distribution' && (
            <div className="gallery-slide animate-fade-in">
              <div className="slide-image-container">
                <img 
                  src="/temp_prediction_comparison.png" 
                  alt="So sánh phân phối dự báo nhiệt độ" 
                  className="gallery-image"
                  onError={(e) => {
                    e.target.onerror = null; 
                    e.target.src = "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=1000";
                  }}
                />
              </div>
              <div className="slide-description">
                <h4>Phân phối dự báo so với thực tế</h4>
                <p>Biểu đồ chuỗi thời gian đối chiếu chi tiết trong một khoảng thời gian Test ngẫu nhiên. Cho thấy độ nhạy của các mô hình trong việc bám theo sự dao động hình sin ngày/đêm của nhiệt độ khí quyển.</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Phần 4: Lịch sử sai số thời gian thực */}
      <div className="error-history-section glass-panel" style={{ marginTop: '24px' }}>
        <div className="gallery-header" style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div className="panel-title-row" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp className="text-cyan" size={20} />
            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>Theo Dõi Sai Số Dự Báo Thực Tế (Thời Gian Thực)</h3>
          </div>
          
          <div className="control-bar-eval" style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            <div className="control-group" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ fontSize: '13px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Building2 size={14} /> Trạm:
              </label>
              <select 
                value={selectedCity} 
                onChange={(e) => setSelectedCity(e.target.value)} 
                className="select-input"
                style={{ padding: '4px 8px', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', color: 'var(--text-light)', border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer' }}
              >
                <option value="Ha Noi">Hà Nội</option>
                <option value="Da Nang">Đà Nẵng</option>
                <option value="TP HCM">TP. Hồ Chí Minh</option>
              </select>
            </div>

            <div className="control-group" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ fontSize: '13px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Calendar size={14} /> Số mốc:
              </label>
              <select 
                value={historyLimit} 
                onChange={(e) => setHistoryLimit(Number(e.target.value))} 
                className="select-input"
                style={{ padding: '4px 8px', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', color: 'var(--text-light)', border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer' }}
              >
                <option value={12}>12 Giờ</option>
                <option value={24}>24 Giờ</option>
                <option value={48}>48 Giờ</option>
                <option value={72}>72 Giờ</option>
              </select>
            </div>
            
            <button 
              onClick={() => fetchErrorHistory(selectedCity, historyLimit)} 
              className="btn-refresh-predict" 
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', padding: '6px', borderRadius: '6px', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              <RefreshCw size={14} className={loadingHistory ? "loading-spinner" : ""} />
            </button>
          </div>
        </div>

        <div className="error-history-body" style={{ marginTop: '20px' }}>
          {loadingHistory ? (
            <div className="tab-loading-container" style={{ padding: '40px 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
              <RefreshCw className="loading-spinner" />
              <p>Đang tải dữ liệu sai số thực tế...</p>
            </div>
          ) : historyError ? (
            <div className="tab-error-container" style={{ padding: '40px 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', color: 'var(--color-actual)' }}>
              <AlertCircle className="error-icon" />
              <p>{historyError}</p>
            </div>
          ) : errorHistory.length === 0 ? (
            <div className="tab-error-container" style={{ padding: '40px 0', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
              <HelpCircle className="error-icon" style={{ color: 'var(--text-muted)', width: '32px', height: '32px' }} />
              <p style={{ margin: 0 }}>Chưa có dữ liệu đối chiếu sai số thực tế cho trạm này.</p>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>
                Hệ thống cần chạy updater ít nhất một lần để đối chiếu dự báo với dữ liệu thực tế thu thập được sau đó.
              </p>
            </div>
          ) : (
            <>
              <div className="error-chart-container" style={{ height: '320px', marginTop: '10px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={errorHistory} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                    <XAxis 
                      dataKey="formattedTime" 
                      stroke="var(--text-muted)" 
                      fontSize={11}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis 
                      stroke="var(--text-muted)" 
                      fontSize={11}
                      tickLine={false}
                      axisLine={false}
                      unit="°C"
                      domain={[0, 'dataMax + 0.5']}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'rgba(20, 20, 20, 0.95)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '8px', color: '#fff' }}
                      labelStyle={{ color: 'var(--text-light)', fontWeight: 'bold' }}
                    />
                    <Legend verticalAlign="top" height={36} iconType="circle" />
                    
                    <Line 
                      type="monotone" 
                      dataKey="err_lr" 
                      name="Sai số Baseline LR" 
                      stroke="var(--color-lr)" 
                      strokeWidth={2}
                      dot={{ r: 2 }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="err_xgb" 
                      name="Sai số XGBoost" 
                      stroke="var(--color-xgb)" 
                      strokeWidth={2}
                      dot={{ r: 2 }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="err_lstm" 
                      name="Sai số LSTM" 
                      stroke="var(--color-lstm)" 
                      strokeWidth={2}
                      dot={{ r: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              
              <div className="evaluation-summary-box" style={{ marginTop: '20px', padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <p style={{ margin: '0 0 8px 0', fontWeight: 600 }}><strong>Giải thích biểu đồ:</strong></p>
                <p className="summary-text" style={{ fontSize: '13px', lineHeight: '1.6', color: 'var(--text-muted)', margin: 0 }}>
                  Biểu đồ này biểu diễn <strong>sai số tuyệt đối thực tế</strong> (|T_thực_tế - T_dự_báo|) tại các mốc thời gian gần đây sau khi thu thập được dữ liệu thực tế từ API Meteostat. 
                  Một mô hình dự báo hoạt động tốt trong thực tế sẽ duy trì đường sai số thấp ổn định gần mốc 0°C. 
                  Sự gia tăng sai số tại một số thời điểm phản ánh biến động khí hậu bất ngờ hoặc các chu kỳ thời tiết đặc biệt nằm ngoài phạm vi học của mô hình.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
