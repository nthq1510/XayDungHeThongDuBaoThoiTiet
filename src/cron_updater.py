import os
import sys
import sqlite3
import argparse
import time
import joblib
import numpy as np
import pandas as pd
# Tắt bớt log cảnh báo của TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
import xgboost as xgb
from datetime import datetime, timedelta
from meteostat import hourly

# Xác định thư mục gốc của dự án
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "database", "weather_data.db")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Các đường dẫn bộ chuẩn hóa và mô hình
SCALER_FEATURES_PATH = os.path.join(MODELS_DIR, "preprocessors", "scaler_features.pkl")
SCALER_TARGET_PATH = os.path.join(MODELS_DIR, "preprocessors", "scaler_target.pkl")
SCALER_LSTM_PATH = os.path.join(MODELS_DIR, "preprocessors", "scaler_lstm_features.pkl")
XGB_MODEL_PATH = os.path.join(MODELS_DIR, "trained", "xgboost_weather_model.json")
LSTM_MODEL_PATH = os.path.join(MODELS_DIR, "trained", "lstm_weather_model.keras")
LR_MODEL_PATH = os.path.join(MODELS_DIR, "trained", "linear_regression_model.pkl")

# Thông tin 3 trạm khí tượng đại diện
CITIES = {
    "Ha Noi": {"station_id": "48820", "name_vn": "Hà Nội"},
    "Da Nang": {"station_id": "48855", "name_vn": "Đà Nẵng"},
    "TP HCM": {"station_id": "48900", "name_vn": "TP. Hồ Chí Minh"}
}

def get_connection():
    """Tạo kết nối tới cơ sở dữ liệu SQLite."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Không tìm thấy cơ sở dữ liệu tại: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_history_tables():
    """Khởi tạo các bảng ghi nhận dự báo và sai số thực tế nếu chưa có."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Bảng lưu trữ lịch sử các dự báo đã thực hiện (dùng để đối chiếu sau)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions_history (
        city TEXT,
        prediction_time TEXT,
        pred_lr REAL,
        pred_xgb REAL,
        pred_lstm REAL,
        created_at TEXT,
        PRIMARY KEY (city, prediction_time)
    )
    """)
    
    # Bảng lưu trữ kết quả sai số thực tế sau khi đối chiếu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS error_history (
        city TEXT,
        time TEXT,
        actual_temp REAL,
        pred_lr REAL,
        pred_xgb REAL,
        pred_lstm REAL,
        err_lr REAL,
        err_xgb REAL,
        err_lstm REAL,
        PRIMARY KEY (city, time)
    )
    """)
    
    conn.commit()
    conn.close()
    print("-> Đã khởi tạo/kiểm tra các bảng 'predictions_history' và 'error_history'.")

def get_last_history_time(city):
    """Lấy mốc thời gian cuối cùng có trong cơ sở dữ liệu processed_weather cho thành phố."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT MAX(time) FROM processed_weather WHERE city = ?", 
        (city,)
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row[0] else None

def calculate_features_for_new_row(city, station_id, new_time_str, raw_data):
    """
    Truy vấn 24 giờ dữ liệu trước đó từ DB, ghép nối với dòng mới 
    và tính toán các đặc trưng trễ/trượt cần thiết.
    """
    conn = get_connection()
    # Lấy 24 giờ dữ liệu gần nhất trước new_time_str
    query = """
        SELECT time, temp, rhum, prcp, snow, wdir, wspd, pres, coco 
        FROM processed_weather 
        WHERE city = ? AND time < ? 
        ORDER BY time DESC LIMIT 24
    """
    df_hist = pd.read_sql_query(query, conn, params=(city, new_time_str))
    conn.close()
    
    if len(df_hist) < 24:
        raise ValueError(f"Không đủ 24 giờ dữ liệu lịch sử trong DB để tính đặc trưng cho mốc {new_time_str} (Hiện có: {len(df_hist)} giờ).")
    
    # Đảo ngược thứ tự để chuỗi thời gian tăng dần
    df_hist = df_hist.iloc[::-1].reset_index(drop=True)
    
    # Tạo dòng dữ liệu mới
    new_row = {
        "time": new_time_str,
        "temp": raw_data.get("temp"),
        "rhum": raw_data.get("rhum"),
        "prcp": raw_data.get("prcp", 0.0),
        "snow": raw_data.get("snow", 0.0),
        "wdir": raw_data.get("wdir"),
        "wspd": raw_data.get("wspd"),
        "pres": raw_data.get("pres"),
        "coco": raw_data.get("coco", 3)
    }
    
    # Điền giá trị thiếu (NaN) cho dòng mới dựa trên dòng liền trước nếu cần
    last_row = df_hist.iloc[-1]
    for col in ["temp", "rhum", "wspd", "wdir", "pres"]:
        if new_row[col] is None or pd.isna(new_row[col]):
            new_row[col] = last_row[col]
            
    if new_row["prcp"] is None or pd.isna(new_row["prcp"]):
        new_row["prcp"] = 0.0
    if new_row["snow"] is None or pd.isna(new_row["snow"]):
        new_row["snow"] = 0.0
    if new_row["coco"] is None or pd.isna(new_row["coco"]):
        new_row["coco"] = 3
        
    df_new = pd.DataFrame([new_row])
    
    # Ghép dữ liệu: 24 dòng lịch sử + 1 dòng mới
    df_combined = pd.concat([df_hist, df_new], ignore_index=True)
    
    # 1. Tính toán các đặc trưng Cyclic Time
    dt = pd.to_datetime(new_time_str)
    hour = dt.hour
    month = dt.month
    
    df_combined['hour'] = df_combined['time'].apply(lambda x: pd.to_datetime(x).hour)
    df_combined['month'] = df_combined['time'].apply(lambda x: pd.to_datetime(x).month)
    
    df_combined['hour_sin'] = np.sin(df_combined['hour'] * (2 * np.pi / 24))
    df_combined['hour_cos'] = np.cos(df_combined['hour'] * (2 * np.pi / 24))
    df_combined['month_sin'] = np.sin((df_combined['month'] - 1) * (2 * np.pi / 12))
    df_combined['month_cos'] = np.cos((df_combined['month'] - 1) * (2 * np.pi / 12))
    
    # 2. Tính toán đặc trưng trễ (Lag) cho dòng cuối cùng (index 24)
    # Ta chỉ quan tâm tính toán cho dòng cuối cùng, nhưng dùng shift trên df_combined
    for col in ["temp", "rhum", "prcp", "wspd"]:
        for lag in [1, 2, 3, 6, 12, 24]:
            df_combined[f"{col}_lag_{lag}h"] = df_combined[col].shift(lag)
            
    # 3. Tính toán đặc trưng trung bình trượt (Rolling) cho dòng cuối cùng
    for col in ["temp", "rhum"]:
        # Rolling 6h
        df_combined[f"{col}_roll_mean_6h"] = df_combined[col].rolling(window=6).mean()
        df_combined[f"{col}_roll_std_6h"] = df_combined[col].rolling(window=6).std()
        # Rolling 24h
        df_combined[f"{col}_roll_mean_24h"] = df_combined[col].rolling(window=24).mean()
        df_combined[f"{col}_roll_std_24h"] = df_combined[col].rolling(window=24).std()
        
    # Trích xuất dòng cuối cùng (đầy đủ đặc trưng đã tính)
    final_row = df_combined.iloc[-1].copy()
    final_row["city"] = city
    final_row["station_id"] = station_id
    
    return final_row

def insert_processed_row(row_series):
    """Ghi dòng dữ liệu đã tiền xử lý vào bảng processed_weather."""
    conn = get_connection()
    cursor = conn.cursor()
    
    columns = list(row_series.index)
    placeholders = ", ".join(["?"] * len(columns))
    sql = f"INSERT OR REPLACE INTO processed_weather ({', '.join(columns)}) VALUES ({placeholders})"
    
    # Chuyển đổi kiểu dữ liệu numpy sang python chuẩn để SQLite nhận diện đúng
    values = [x.item() if hasattr(x, 'item') else x for x in row_series.values]
    
    cursor.execute(sql, values)
    conn.commit()
    conn.close()

def evaluate_predictions_error(city, time_str, actual_temp):
    """Đối chiếu nhiệt độ thực tế với dự báo trước đó để tính sai số và lưu vào error_history."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Kiểm tra xem có dự báo nào được thực hiện cho mốc time_str chưa
    cursor.execute(
        "SELECT pred_lr, pred_xgb, pred_lstm FROM predictions_history WHERE city = ? AND prediction_time = ?",
        (city, time_str)
    )
    row = cursor.fetchone()
    
    if row:
        pred_lr, pred_xgb, pred_lstm = row["pred_lr"], row["pred_xgb"], row["pred_lstm"]
        
        # Tính sai số tuyệt đối
        err_lr = abs(actual_temp - pred_lr)
        err_xgb = abs(actual_temp - pred_xgb)
        err_lstm = abs(actual_temp - pred_lstm)
        
        # Ghi nhận vào error_history
        cursor.execute("""
        INSERT OR REPLACE INTO error_history 
        (city, time, actual_temp, pred_lr, pred_xgb, pred_lstm, err_lr, err_xgb, err_lstm) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (city, time_str, actual_temp, pred_lr, pred_xgb, pred_lstm, err_lr, err_xgb, err_lstm))
        conn.commit()
        print(f"  [ĐỐI CHIẾU SAI SỐ] {city} lúc {time_str} -> Thực tế: {actual_temp}°C | LR: {pred_lr:.2f}°C (Err: {err_lr:.2f}) | XGB: {pred_xgb:.2f}°C (Err: {err_xgb:.2f}) | LSTM: {pred_lstm:.2f}°C (Err: {err_lstm:.2f})")
    
    conn.close()

# Biến toàn cục lưu trữ các mô hình để tránh load lại nhiều lần
_MODELS = {}
_SCALERS = {}

def load_inference_resources():
    """Tải toàn bộ mô hình và bộ chuẩn hóa lên bộ nhớ (chỉ tải một lần)."""
    global _MODELS, _SCALERS
    if _MODELS:
        return
        
    print("-> Đang tải tài nguyên mô hình AI phục vụ chạy suy luận...")
    _SCALERS['features'] = joblib.load(SCALER_FEATURES_PATH)
    _SCALERS['target'] = joblib.load(SCALER_TARGET_PATH)
    _SCALERS['lstm'] = joblib.load(SCALER_LSTM_PATH)
    
    _MODELS['lr'] = joblib.load(LR_MODEL_PATH)
    
    xgb_model = xgb.XGBRegressor()
    xgb_model.load_model(XGB_MODEL_PATH)
    _MODELS['xgb'] = xgb_model
    
    _MODELS['lstm'] = tf.keras.models.load_model(LSTM_MODEL_PATH)
    print("-> Đã tải tất cả các mô hình thành công.")

def predict_next_hour(city, last_time_str):
    """
    Lấy 24 giờ dữ liệu gần nhất, thiết lập dòng tiếp theo để dự báo,
    chạy 3 mô hình và lưu dự báo vào predictions_history.
    """
    load_inference_resources()
    
    # 1. Lấy dữ liệu 24 giờ cuối trong SQLite
    conn = get_connection()
    query = """
        SELECT * FROM processed_weather 
        WHERE city = ? AND time <= ? 
        ORDER BY time DESC LIMIT 24
    """
    df_hist = pd.read_sql_query(query, conn, params=(city, last_time_str))
    conn.close()
    
    if len(df_hist) < 24:
        print(f"  [BỎ QUA DỰ BÁO] Không đủ 24 giờ dữ liệu để chạy dự báo cho {city}.")
        return
        
    df_hist = df_hist.iloc[::-1].reset_index(drop=True)
    
    # Xác định mốc thời gian tiếp theo cần dự báo
    last_dt = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
    next_dt = last_dt + timedelta(hours=1)
    next_time_str = next_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # 2. Xây dựng dòng dữ liệu đầu vào cho LR & XGBoost tại mốc t+1
    # Mô hình sử dụng các biến trễ, vì vậy ta dịch chuyển dòng cuối cùng
    last_row = df_hist.iloc[-1]
    
    next_row = {
        # Giả lập các đặc trưng hiện tại bằng mốc cuối
        "rhum": last_row["rhum"],
        "prcp": 0.0, # Giả định giờ sau không mưa
        "snow": 0.0,
        "wdir": last_row["wdir"],
        "wspd": last_row["wspd"],
        "pres": last_row["pres"],
        "coco": last_row["coco"],
        # Cấu trúc thời gian thực của mốc t+1
        "hour": next_dt.hour,
        "month": next_dt.month,
        "hour_sin": np.sin(next_dt.hour * (2 * np.pi / 24)),
        "hour_cos": np.cos(next_dt.hour * (2 * np.pi / 24)),
        "month_sin": np.sin((next_dt.month - 1) * (2 * np.pi / 12)),
        "month_cos": np.cos((next_dt.month - 1) * (2 * np.pi / 12)),
    }
    
    # Tính các biến trễ (Lag) cho mốc t+1
    # Ví dụ: temp_lag_1h tại mốc t+1 chính là temp tại mốc t
    # Ta lấy trực tiếp từ lịch sử
    for lag in [1, 2, 3, 6, 12, 24]:
        next_row[f"temp_lag_{lag}h"] = df_hist.iloc[-lag]["temp"]
        next_row[f"rhum_lag_{lag}h"] = df_hist.iloc[-lag]["rhum"]
        next_row[f"prcp_lag_{lag}h"] = df_hist.iloc[-lag]["prcp"]
        next_row[f"wspd_lag_{lag}h"] = df_hist.iloc[-lag]["wspd"]
        
    # Tính các biến trung bình trượt (Rolling) cho mốc t+1
    # Ví dụ: temp_roll_mean_6h tại mốc t+1 tính dựa trên t-4 đến t (5 giờ qua) + mốc t+1 (xấp xỉ bằng mốc t)
    # Lấy nhanh các giá trị nhiệt độ trong 5 giờ qua cộng với giả định
    temp_vals_6 = list(df_hist.iloc[-5:]["temp"]) + [last_row["temp"]]
    next_row["temp_roll_mean_6h"] = np.mean(temp_vals_6)
    next_row["temp_roll_std_6h"] = np.std(temp_vals_6)
    
    temp_vals_24 = list(df_hist.iloc[-23:]["temp"]) + [last_row["temp"]]
    next_row["temp_roll_mean_24h"] = np.mean(temp_vals_24)
    next_row["temp_roll_std_24h"] = np.std(temp_vals_24)
    
    rhum_vals_6 = list(df_hist.iloc[-5:]["rhum"]) + [last_row["rhum"]]
    next_row["rhum_roll_mean_6h"] = np.mean(rhum_vals_6)
    next_row["rhum_roll_std_6h"] = np.std(rhum_vals_6)
    
    rhum_vals_24 = list(df_hist.iloc[-23:]["rhum"]) + [last_row["rhum"]]
    next_row["rhum_roll_mean_24h"] = np.mean(rhum_vals_24)
    next_row["rhum_roll_std_24h"] = np.std(rhum_vals_24)
    
    df_next_features = pd.DataFrame([next_row])
    
    # 3. Chạy suy luận Hồi quy tuyến tính & XGBoost
    feature_cols = list(_SCALERS['features'].feature_names_in_)
    X_scaled = _SCALERS['features'].transform(df_next_features[feature_cols])
    
    pred_scaled_lr = _MODELS['lr'].predict(X_scaled)
    pred_scaled_xgb = _MODELS['xgb'].predict(X_scaled)
    
    pred_lr = float(_SCALERS['target'].inverse_transform(pred_scaled_lr.reshape(-1, 1)).flatten()[0])
    pred_xgb = float(_SCALERS['target'].inverse_transform(pred_scaled_xgb.reshape(-1, 1)).flatten()[0])
    
    # 4. Chạy suy luận LSTM (Cần chuỗi 24 giờ từ t-23 đến t)
    lstm_feature_cols = list(_SCALERS['lstm'].feature_names_in_)
    df_lstm_scaled = _SCALERS['lstm'].transform(df_hist[lstm_feature_cols])
    X_lstm_3d = np.array([df_lstm_scaled]) # shape: (1, 24, num_features)
    
    pred_lstm = float(_MODELS['lstm'].predict(X_lstm_3d, verbose=0).flatten()[0])
    
    # 5. Lưu trữ kết quả dự báo
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT OR REPLACE INTO predictions_history (city, prediction_time, pred_lr, pred_xgb, pred_lstm, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (city, next_time_str, pred_lr, pred_xgb, pred_lstm, now_str))
    conn.commit()
    conn.close()
    
    print(f"  [DỰ BÁO HOÀN TẤT] {city} cho mốc tiếp theo {next_time_str} -> LR: {pred_lr:.2f}°C | XGB: {pred_xgb:.2f}°C | LSTM: {pred_lstm:.2f}°C")

def update_city_weather(city, station_id):
    """Tìm dữ liệu mới từ Meteostat, cập nhật đặc trưng, đối chiếu sai số và chạy dự báo."""
    print(f"\n-> Bắt đầu tiến trình cập nhật cho: {city} (Trạm: {station_id})")
    
    # 1. Xác định mốc thời gian cuối trong DB
    last_db_time_str = get_last_history_time(city)
    if not last_db_time_str:
        print(f"  [CẢNH BÁO] Không có dữ liệu lịch sử trong bảng processed_weather cho {city}. Vui lòng kiểm tra lại DB.")
        return
        
    last_db_time = datetime.strptime(last_db_time_str, "%Y-%m-%d %H:%M:%S")
    
    # Xác định khoảng thời gian cần cập nhật (Từ giờ sau của mốc cuối đến giờ hiện tại)
    start_fetch = last_db_time + timedelta(hours=1)
    # Làm tròn thời gian hiện tại về giờ chẵn gần nhất
    now = datetime.now()
    end_fetch = datetime(now.year, now.month, now.day, now.hour, 0, 0)
    
    if start_fetch > end_fetch:
        print(f"  [OK] Dữ liệu của {city} đã cập nhật mới nhất (Mốc DB: {last_db_time_str}). Không cần tải thêm.")
        # Vẫn chạy dự báo mốc tiếp theo phòng khi chưa chạy
        predict_next_hour(city, last_db_time_str)
        return
        
    print(f"  Đang tải dữ liệu từ API Meteostat: {start_fetch.strftime('%Y-%m-%d %H:%M:%S')} -> {end_fetch.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Gọi thư viện Meteostat tải dữ liệu
        data_fetcher = hourly(station_id, start_fetch, end_fetch)
        df_new = data_fetcher.fetch()
        
        if df_new.empty:
            print("  [CẢNH BÁO] API Meteostat không trả về dữ liệu mới cho khoảng thời gian này.")
            predict_next_hour(city, last_db_time_str)
            return
            
        df_new = df_new.reset_index()
        df_new['time'] = df_new['time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"  Tải thành công {len(df_new)} bản ghi giờ mới từ Meteostat.")
        
        # Chèn tuần tự từng giờ để tính toán đặc trưng chính xác
        df_new = df_new.sort_values(by="time")
        
        for _, row in df_new.iterrows():
            new_time = row["time"]
            raw_weather = {
                "temp": row.get("temp"),
                "rhum": row.get("rhum"),
                "prcp": row.get("prcp"),
                "snow": row.get("snow"),
                "wdir": row.get("wdir"),
                "wspd": row.get("wspd"),
                "pres": row.get("pres"),
                "coco": row.get("coco")
            }
            
            # Tính toán đặc trưng trễ/trượt dựa trên lịch sử
            processed_row = calculate_features_for_new_row(city, station_id, new_time, raw_weather)
            
            # Lưu vào processed_weather
            insert_processed_row(processed_row)
            
            # Đối chiếu sai số với dự báo đã thực hiện (nếu có)
            evaluate_predictions_error(city, new_time, processed_row["temp"])
            
        # Xác định mốc mới nhất vừa chèn
        updated_max_time = df_new["time"].max()
        print(f"  [OK] Đã cập nhật xong dữ liệu thực tế đến mốc: {updated_max_time}")
        
        # Chạy dự báo cho mốc giờ tiếp theo
        predict_next_hour(city, updated_max_time)
        
    except Exception as e:
        import traceback
        print(f"  [LỖI] Lỗi trong quá trình cập nhật {city}: {str(e)}")
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description="Script tự động cập nhật thời tiết và ghi nhận sai số dự báo AI.")
    parser.add_argument("--once", action="store_true", help="Chạy cập nhật một lần duy nhất rồi thoát.")
    parser.add_argument("--interval", type=int, default=3600, help="Khoảng thời gian lặp lại cập nhật (tính bằng giây, mặc định 3600 = 1 giờ).")
    
    args = parser.parse_args()
    
    print("=== KHỞI ĐỘNG HỆ THỐNG CẬP NHẬT TỰ ĐỘNG & GHI NHẬN SAI SỐ ===")
    init_history_tables()
    
    if args.once:
        print("\n=== BẮT ĐẦU CHẠY CẬP NHẬT (CHẾ ĐỘ MỘT LẦN) ===")
        for city, info in CITIES.items():
            update_city_weather(city, info["station_id"])
        print("\n=== TIẾN TRÌNH CẬP NHẬT HOÀN TẤT ===")
    else:
        print(f"\n=== BẮT ĐẦU CHẠY CẬP NHẬT LIÊN TỤC (MỖI {args.interval} GIÂY) ===")
        try:
            while True:
                for city, info in CITIES.items():
                    update_city_weather(city, info["station_id"])
                print(f"\nĐợi {args.interval} giây cho chu kỳ tiếp theo...")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nĐang dừng tiến trình cập nhật tự động...")

if __name__ == "__main__":
    main()
