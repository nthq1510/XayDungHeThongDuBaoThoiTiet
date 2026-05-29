# Xây Dựng Hệ Thống Dự Báo Thời Tiết Thời Gian Thực Bằng Học Máy Và Học Sâu

Đề tài Đồ án Tốt nghiệp: **"Xây dựng hệ thống dự báo nhiệt độ thời gian thực dựa trên các mô hình Học máy và Học sâu chuỗi thời gian"**

Hệ thống được thiết kế theo kiến trúc Microservices hướng dịch vụ, container hóa hoàn chỉnh bằng Docker Compose, tự động hóa cập nhật dữ liệu khí tượng thực tế và suy luận dự báo nhiệt độ mỗi giờ, đồng thời trực quan hóa trên giao diện Web Dashboard tương tác.

---

## 🌟 Tính Năng Nổi Bật

1. **Thu thập dữ liệu chuỗi thời gian khí tượng:**
   - Sử dụng API Meteostat đồng bộ dữ liệu lịch sử 10 năm (2016-2026) của 3 trạm khí tượng đại diện 3 miền Việt Nam: Hà Nội (Mã: 48820), Đà Nẵng (Mã: 48855), và TP. Hồ Chí Minh (Mã: 48900).
   - Tổng quy mô tập dữ liệu thô: **273.010 bản ghi theo giờ**.

2. **Quy trình làm sạch dữ liệu & Kỹ nghệ đặc trưng:**
   - Điền khuyết thiếu bằng nội suy tuyến tính (Linear Interpolation) và xử lý ngoại lệ chuỗi thời gian.
   - Mã hóa chu kỳ thời gian (Cyclic Time Encoding) sang tọa độ Sin/Cos cho mốc Giờ và Tháng.
   - Xây dựng đặc trưng trễ (Lag features: 1h, 2h, 3h, 6h, 12h, 24h) và thống kê trượt (Rolling features: Mean, Std trong cửa sổ 6h và 24h).

3. **Huấn luyện và Đánh giá đối sánh 3 Mô hình AI:**
   - **Baseline (Linear Regression):** Mốc đối sánh tuyến tính cơ bản.
   - **XGBoost Regressor:** Học máy dạng Ensemble mạnh mẽ trên dữ liệu dạng bảng.
   - **LSTM Deep Learning (Long Short-Term Memory):** Học sâu mạng nơ-ron hồi quy chuỗi thời gian tự trích xuất đặc trưng với cửa sổ trượt 24 giờ.

4. **Tự động hóa luồng dữ liệu thời gian thực (Real-time Closed-loop):**
   - **Updater Daemon:** Script python chạy ngầm tự động gọi API lấy dữ liệu thực tế mỗi giờ.
   - **Tính toán sai số thực tế:** So sánh đối chiếu nhiệt độ thực tế vừa tải với các dự báo đã thực hiện ở chu kỳ trước để lưu vết lịch sử sai số thực tế.
   - **Suy luận $t+1$:** Chạy song song cả 3 mô hình dự báo nhiệt độ cho giờ tiếp theo và lưu vào SQLite.

5. **Giao diện Web Dashboard Hiện đại (Glassmorphism):**
   - Thiết kế kính mờ (Glassmorphism) sang trọng với giao diện Dark Mode sâu thẳm, đáp ứng tốt trên mọi thiết bị (Responsive).
   - Biểu đồ trực quan hóa dữ liệu lịch sử kết hợp đường dự báo của 3 mô hình (sử dụng Recharts).
   - Biểu đồ theo dõi lịch sử sai số tuyệt đối thực tế cập nhật liên tục theo giờ để đánh giá trực quan hiệu năng chạy thực tế của mô hình.

---

## 🛠️ Công Nghệ Sử Dụng

- **Core:** Python 3.11, Node.js (Vite + React)
- **AI/ML/DL:** TensorFlow/Keras, XGBoost, Scikit-Learn, Pandas, NumPy
- **Backend API:** FastAPI, Uvicorn, SQLite
- **Frontend UI:** ReactJS, Vanilla CSS (Glassmorphism), Recharts, Lucide React
- **DevOps:** Docker, Docker Compose, Nginx (Web Server)

---

## 📁 Cấu Trúc Thư Mục Dự Án

```text
.
├── backend/                    # Mã nguồn máy chủ Backend API
│   ├── app/
│   │   ├── api.py              # Định nghĩa endpoints REST API
│   │   ├── config.py           # Các cấu hình hệ thống
│   │   ├── database.py         # Kết nối & truy vấn SQLite
│   │   └── inference.py        # Tải mô hình & Động cơ suy luận dự báo
│   ├── main.py                 # File chạy chính của FastAPI
│   └── requirements.txt        # Thư viện Python phụ thuộc
├── data/                       # Dữ liệu của dự án
│   ├── database/               # Chứa file SQLite database (weather_data.db)
│   └── raw/                    # Dữ liệu thử nghiệm CSV ban đầu
├── frontend/                   # Mã nguồn ứng dụng Web ReactJS
│   ├── public/                 # Ảnh kết xuất đồ thị huấn luyện
│   ├── src/
│   │   ├── components/         # Các components Dashboard, Forecast, Evaluation
│   │   ├── App.css             # Vanilla CSS chứa design system Glassmorphic
│   │   ├── App.jsx             # Component điều hướng chính
│   │   └── main.jsx            # Khởi tạo React
│   ├── Dockerfile              # Build Nginx & React tĩnh
│   └── nginx.conf              # Cấu hình routing & cache Nginx
├── models/                     # Chứa các mô hình đã huấn luyện
│   ├── preprocessors/          # Scaler chuẩn hóa MinMaxScaler (.pkl)
│   └── trained/                # Linear Regression (.pkl), XGBoost (.json), LSTM (.keras)
├── notebooks/                  # Nghiên cứu & Huấn luyện (Jupyter Notebooks)
│   ├── data_collection.ipynb   # Quy trình thu thập dữ liệu
│   ├── data_preprocessing.ipynb# Quy trình tiền xử lý & kỹ nghệ đặc trưng
│   ├── model_training.ipynb    # Huấn luyện & đánh giá sai số mô hình AI
│   └── data_overview.ipynb     # Tổng quan dữ liệu & sửa lỗi KeyError
├── src/                        # Các script xử lý chạy ngầm
│   ├── collect_data.py         # Tải dữ liệu lịch sử lớn
│   └── cron_updater.py         # Updater Daemon cập nhật dữ liệu tự động mỗi giờ
├── tests/                      # Thư mục chứa các script test nhanh
├── Dockerfile                  # Dockerfile chung cho backend/updater
└── docker-compose.yml          # Tệp điều phối đa container dịch vụ
```

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### Cách 1: Chạy Bằng Docker Compose (Khuyên Dùng)

Yêu cầu máy tính cài đặt sẵn **Docker** và **Docker Desktop**.

1. **Khởi động Docker Desktop** trên máy của bạn.
2. Mở Terminal tại thư mục gốc của dự án và chạy lệnh sau để build và khởi chạy tất cả các dịch vụ:
   ```bash
   docker compose up --build -d
   ```
3. Lệnh này sẽ khởi động 3 container:
   - `weather-frontend` (Port `5174`)
   - `weather-backend` (Port `8001`)
   - `weather-updater` (Chạy daemon cập nhật tự động hàng giờ)
4. Mở trình duyệt và truy cập: **[http://localhost:5174](http://localhost:5174)** để trải nghiệm giao diện Web.

---

### Cách 2: Chạy Thủ Công (Local Development)

#### 1. Khởi chạy Backend API
1. Đi tới thư mục `backend/` và tạo môi trường ảo Python:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Chạy FastAPI server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

#### 2. Khởi chạy Frontend React
1. Mở một terminal mới, đi tới thư mục `frontend/`:
   ```bash
   cd frontend
   npm install
   npm run dev -- --port 5174
   ```
2. Truy cập giao diện tại: `http://localhost:5174`.

#### 3. Chạy Updater cập nhật dữ liệu thủ công
Để tải dữ liệu thực tế mới nhất và chạy suy luận dự báo ngay lập tức:
```bash
python3 src/cron_updater.py --once
```

---

## 📊 Kết Quả Thực Nghiệm Trên Tập Test (Nhiệt độ `temp`)

Kết quả đối sánh sai số chính thức của 3 mô hình trên tập kiểm thử độc lập (Test Set: 01/01/2025 - 05/2026):

| Mô hình | MAE (°C) | RMSE (°C) | MAPE (%) |
|---|---|---|---|
| **Linear Regression (Baseline)** | 0.336 | 0.452 | 1.326% |
| **XGBoost Regressor** | **0.316** | **0.440** | **1.250%** |
| **LSTM Deep Learning** | 0.631 | 0.874 | 2.510% |

**Nhận xét:**
- **XGBoost** cho độ chính xác cao nhất (MAE **0.316 °C**) nhờ khai thác triệt để các đặc trưng trễ cực ngắn hạn (như nhiệt độ cách đây 1 giờ `temp_lag_1h`).
- **LSTM** đạt kết quả ấn tượng (MAE **0.631 °C**) khi tự học hoàn toàn từ chuỗi dữ liệu 24 giờ quá khứ mà không cần các biến trễ được tính sẵn.

---

## 📝 Thông Tin Đồ Án

- **Sinh viên thực hiện:** Nguyễn Tâm Hữu Quảng
- **Đề tài:** Nghiên cứu và xây dựng hệ thống dự báo thời tiết dựa trên các mô hình Học máy và Học sâu chuỗi thời gian.
- **Giảng viên hướng dẫn:** [Tên Giảng Viên Hướng Dẫn]
- **Trường đào tạo:** Đại học Bách Khoa / Viện Công nghệ thông tin
