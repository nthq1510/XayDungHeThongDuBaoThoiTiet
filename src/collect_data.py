import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
from meteostat import hourly

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "database" / "weather_data.db"


def get_db_connection():
    """Tạo kết nối tới cơ sở dữ liệu SQLite."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    """Khởi tạo cấu trúc bảng trong Database."""
    print("-> Đang khởi tạo cơ sở dữ liệu SQLite...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tạo bảng hourly_weather nếu chưa tồn tại
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hourly_weather (
        city TEXT,
        station_id TEXT,
        time TEXT,
        temp REAL,
        dwpt REAL,
        rhum REAL,
        prcp REAL,
        snow REAL,
        wdir REAL,
        wspd REAL,
        wpgt REAL,
        pres REAL,
        tsun REAL,
        cldc REAL,
        coco INTEGER,
        PRIMARY KEY (station_id, time)
    )
    """)
    conn.commit()
    conn.close()
    print("-> Đã khởi tạo bảng 'hourly_weather' thành công.")

def download_data_for_city(city_name, station_id, start_year=2016, end_year=2026):
    """
    Tải dữ liệu khí tượng theo từng năm để tránh quá tải kết nối 
    và lưu trữ trực tiếp vào cơ sở dữ liệu.
    """
    print(f"\n==================================================")
    print(f"BẮT ĐẦU THU THẬP DỮ LIỆU: {city_name.upper()} (ID: {station_id})")
    print(f"==================================================")
    
    conn = get_db_connection()
    
    for year in range(start_year, end_year + 1):
        # Thiết lập khoảng thời gian theo từng năm
        start_date = datetime(year, 1, 1, 0, 0, 0)
        
        # Nếu là năm hiện tại (2026), giới hạn đến ngày hôm nay
        current_time = datetime.now()
        if year == current_time.year:
            end_date = current_time
        else:
            end_date = datetime(year, 12, 31, 23, 59, 59)
            
        print(f"Đang tải dữ liệu năm {year} (từ {start_date.strftime('%Y-%m-%d')} đến {end_date.strftime('%Y-%m-%d')})...")
        
        try:
            # Gọi API Meteostat lấy dữ liệu theo giờ
            data = hourly(station_id, start_date, end_date)
            df = data.fetch()
            
            if df.empty:
                print(f"  [CẢNH BÁO] Không có dữ liệu cho năm {year}.")
                continue
                
            # Đưa cột index 'time' thành cột dữ liệu bình thường và định dạng chuỗi
            df = df.reset_index()
            df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Thêm cột thông tin thành phố và mã trạm
            df['city'] = city_name
            df['station_id'] = station_id
            
            # Đảm bảo thứ tự cột tương ứng với DB
            columns_order = [
                'city', 'station_id', 'time', 'temp', 'dwpt', 'rhum', 
                'prcp', 'snow', 'wdir', 'wspd', 'wpgt', 'pres', 'tsun', 'cldc', 'coco'
            ]
            # Nếu thiếu cột nào, điền NaN
            for col in columns_order:
                if col not in df.columns:
                    df[col] = None
                    
            df_to_save = df[columns_order]
            
            # Lưu dữ liệu vào DB (chèn đè nếu trùng khóa chính PRIMARY KEY)
            df_to_save.to_sql("hourly_weather", conn, if_exists="append", index=False, method="multi")
            
            # Thay thế câu lệnh REPLACE để tránh trùng khóa chính khi chạy lại
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM hourly_weather WHERE station_id = '{station_id}' AND time LIKE '{year}%'")
            saved_rows = cursor.fetchone()[0]
            
            print(f"  [OK] Đã lưu {len(df_to_save)} dòng dữ liệu của năm {year} vào database.")
            
        except Exception as e:
            print(f"  [LỖI] Lỗi khi tải dữ liệu năm {year}: {str(e)}")
            
    conn.close()
    print(f"Hoàn thành thu thập dữ liệu cho {city_name}.")

def export_summary():
    """Kiểm tra tổng số dòng đã lưu trữ và in ra thống kê."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n==================================================")
    print("THỐNG KÊ DỮ LIỆU ĐÃ THU THẬP ĐƯỢC TRONG DATABASE")
    print("==================================================")
    
    cursor.execute("SELECT city, COUNT(*), MIN(time), MAX(time) FROM hourly_weather GROUP BY city")
    rows = cursor.fetchall()
    
    for row in rows:
        print(f"Thành phố: {row[0]:<15} | Tổng số dòng: {row[1]:<8} | Từ ngày: {row[2]} -> Đến ngày: {row[3]}")
        
    cursor.execute("SELECT COUNT(*) FROM hourly_weather")
    total = cursor.fetchone()[0]
    print(f"\n=> TỔNG CỘNG HỆ THỐNG ĐÃ LƯU TRỮ: {total} dòng dữ liệu theo giờ.")
    conn.close()

if __name__ == "__main__":
    init_db()
    
    # Định nghĩa 3 thành phố mục tiêu
    cities = {
        "Ha Noi": "48820",
        "Da Nang": "48855",
        "TP HCM": "48900"
    }
    
    # Chạy thu thập dữ liệu từ 2016 đến 2026 (10 năm)
    for city, station_id in cities.items():
        download_data_for_city(city, station_id, start_year=2016, end_year=2026)
        
    export_summary()
