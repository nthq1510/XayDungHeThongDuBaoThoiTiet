import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from app.config import DB_PATH

def get_connection():
    """Tạo kết nối tới cơ sở dữ liệu SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_latest_weather():
    """Lấy bản ghi thời tiết mới nhất của 3 thành phố."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cities = ["Ha Noi", "Da Nang", "TP HCM"]
    latest_data = {}
    
    for city in cities:
        cursor.execute(
            "SELECT * FROM processed_weather WHERE city = ? ORDER BY time DESC LIMIT 1",
            (city,)
        )
        row = cursor.fetchone()
        if row:
            latest_data[city] = dict(row)
            
    conn.close()
    return latest_data

def get_historical_weather(city: str, days: int = 7):
    """Lấy dữ liệu thời tiết thực tế trong N ngày gần nhất cho biểu đồ tổng quan."""
    conn = get_connection()
    
    # Tính mốc thời gian giới hạn
    latest_time_query = "SELECT MAX(time) FROM processed_weather WHERE city = ?"
    cursor = conn.cursor()
    cursor.execute(latest_time_query, (city,))
    max_time_str = cursor.fetchone()[0]
    
    if not max_time_str:
        conn.close()
        return []
        
    max_time = datetime.strptime(max_time_str, "%Y-%m-%d %H:%M:%S")
    start_time = max_time - timedelta(days=days)
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    
    df = pd.read_sql_query(
        "SELECT * FROM processed_weather WHERE city = ? AND time >= ? ORDER BY time ASC",
        conn,
        params=(city, start_time_str)
    )
    conn.close()
    return df.to_dict(orient="records")

def get_weather_for_inference(city: str, start_date_str: str, end_date_str: str):
    """
    Lấy dữ liệu phục vụ chạy suy diễn (Inference).
    Để chạy được LSTM với seq_len=24, ta cần lấy thêm dữ liệu của 24 giờ trước start_date.
    """
    conn = get_connection()
    
    # Định dạng mốc thời gian
    start_dt = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
    extended_start_dt = start_dt - timedelta(hours=24)
    extended_start_str = extended_start_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    df = pd.read_sql_query(
        "SELECT * FROM processed_weather WHERE city = ? AND time >= ? AND time <= ? ORDER BY time ASC",
        conn,
        params=(city, extended_start_str, end_date_str)
    )
    conn.close()
    return df

def get_error_history(city: str, limit: int = 48):
    """Lấy lịch sử sai số dự báo thực tế trong N mốc gần nhất cho thành phố."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM error_history WHERE city = ? ORDER BY time DESC LIMIT ?",
            conn,
            params=(city, limit)
        )
        conn.close()
        # Đảo ngược lại theo thứ tự thời gian tăng dần để vẽ biểu đồ
        return df.iloc[::-1].to_dict(orient="records")
    except Exception as e:
        conn.close()
        print(f"Lỗi khi truy vấn error_history: {e}")
        return []
