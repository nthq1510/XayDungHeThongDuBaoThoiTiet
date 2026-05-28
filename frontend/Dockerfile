# Bước 1: Build mã nguồn React sử dụng Node.js Alpine
FROM node:20-alpine AS build

WORKDIR /app

# Copy package.json và package-lock.json để cài đặt dependencies trước
COPY package.json package-lock.json ./

# Cài đặt các thư viện cần thiết
RUN npm ci

# Copy toàn bộ mã nguồn frontend để build
COPY . .

# Tiến hành build production dự án React (Vite sẽ tạo thư mục dist)
RUN npm run build

# Bước 2: Sử dụng image Nginx gọn nhẹ để phục vụ các file tĩnh
FROM nginx:stable-alpine

# Copy cấu hình nginx tùy chỉnh cho Single Page Application
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy toàn bộ các file static đã build từ layer 1 sang Nginx html directory
COPY --from=build /app/dist /usr/share/nginx/html

# Cổng lắng nghe mặc định của Nginx
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
