from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router
from app.inference import load_models
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi động: Tải tất cả các mô hình lên bộ nhớ
    print("=== ĐANG KHỞI ĐỘNG BACKEND API SYSTEM ===")
    load_models()
    yield
    # Tắt ứng dụng: giải phóng bộ nhớ nếu cần
    print("=== ĐANG TẮT HỆ THỐNG BACKEND API ===")

app = FastAPI(
    title="Hệ Thống Dự Báo Thời Tiết AI/ML API",
    description="Backend API phục vụ dự báo nhiệt độ bằng Linear Regression, XGBoost và LSTM",
    version="1.0.0",
    lifespan=lifespan
)

# Cấu hình CORS để React Frontend có thể gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hỗ trợ mọi nguồn gọi cho việc phát triển cục bộ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký router chính với tiền tố /api
app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {
        "message": "Chào mừng đến với API Hệ thống Dự báo Thời tiết AI/ML",
        "status": "online",
        "endpoints": [
            "/api/cities", 
            "/api/weather/current", 
            "/api/weather/history", 
            "/api/predict", 
            "/api/metrics"
        ]
    }
