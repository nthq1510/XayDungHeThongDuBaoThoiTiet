# Sử dụng python:3.11-slim làm base image để tối ưu dung lượng image
FROM python:3.11-slim

# Thiết lập các biến môi trường tối ưu cho Python và TensorFlow
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TF_CPP_MIN_LOG_LEVEL=3

# Cài đặt build-essential để hỗ trợ cài đặt các gói wheel nếu cần
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc chính trong container
WORKDIR /app

# Copy requirements.txt của backend vào để cài đặt trước (giúp tận dụng layer cache)
COPY backend/requirements.txt /app/backend/requirements.txt

# Cấu hình cài đặt: sử dụng tensorflow-cpu cho x86_64 và tensorflow mặc định cho aarch64 để giảm dung lượng image
RUN pip install --no-cache-dir --upgrade pip && \
    if [ "$(uname -m)" = "x86_64" ]; then \
        sed -i 's/tensorflow>=2.12.0/tensorflow-cpu>=2.12.0/g' /app/backend/requirements.txt; \
    fi && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Cài đặt thêm meteostat cho tiến trình cron_updater chạy cập nhật dữ liệu tự động
RUN pip install --no-cache-dir meteostat

# Copy mã nguồn backend và src của dự án vào container
COPY backend /app/backend
COPY src /app/src

# Port mặc định của FastAPI backend
EXPOSE 8001

# Command khởi chạy mặc định (sẽ được override đối với service updater)
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
