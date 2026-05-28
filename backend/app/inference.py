import os
import joblib
import pandas as pd
import numpy as np
import xgboost as xgb
import tensorflow as tf
from app.config import (
    SCALER_FEATURES_PATH,
    SCALER_TARGET_PATH,
    SCALER_LSTM_PATH,
    XGB_MODEL_PATH,
    LSTM_MODEL_PATH,
    LR_MODEL_PATH
)

# Biến toàn cục lưu trữ các đối tượng mô hình đã tải
models = {}
scalers = {}

def load_models():
    """Tải tất cả các mô hình và bộ chuẩn hóa từ đĩa."""
    global models, scalers
    print("-> Đang tải các bộ chuẩn hóa...")
    scalers['features'] = joblib.load(SCALER_FEATURES_PATH)
    scalers['target'] = joblib.load(SCALER_TARGET_PATH)
    scalers['lstm'] = joblib.load(SCALER_LSTM_PATH)
    
    print("-> Đang tải mô hình Hồi quy tuyến tính...")
    models['lr'] = joblib.load(LR_MODEL_PATH)
    
    print("-> Đang tải mô hình XGBoost...")
    xgb_model = xgb.XGBRegressor()
    xgb_model.load_model(XGB_MODEL_PATH)
    models['xgb'] = xgb_model
    
    print("-> Đang tải mô hình LSTM...")
    models['lstm'] = tf.keras.models.load_model(LSTM_MODEL_PATH)
    
    print("-> Tất cả mô hình đã được tải thành công!")

def run_predictions(df: pd.DataFrame, start_date_str: str):
    """
    Chạy dự báo cho 3 mô hình trên dữ liệu đầu vào.
    df: DataFrame chứa dữ liệu thời tiết thô + đặc trưng tính sẵn (lag, rolling).
    start_date_str: Mốc thời gian bắt đầu cần lấy dự báo (dùng để lọc kết quả trả về).
    """
    global models, scalers
    
    if len(df) <= 24:
        raise ValueError("Dữ liệu không đủ 24 giờ để chạy dự báo chuỗi thời gian.")
        
    # 1. Trích xuất đặc trưng cho Linear Regression và XGBoost
    cac_dac_trung = list(scalers['features'].feature_names_in_)
    X_scaled = scalers['features'].transform(df[cac_dac_trung])
    
    # Chạy dự báo (kết quả trả về đang được chuẩn hóa [0, 1])
    y_pred_scaled_lr = models['lr'].predict(X_scaled)
    y_pred_scaled_xgb = models['xgb'].predict(X_scaled)
    
    # Chuyển đổi ngược lại (Inverse scale) sang nhiệt độ thực tế (°C)
    y_pred_lr = scalers['target'].inverse_transform(y_pred_scaled_lr.reshape(-1, 1)).flatten()
    y_pred_xgb = scalers['target'].inverse_transform(y_pred_scaled_xgb.reshape(-1, 1)).flatten()
    
    # 2. Chuẩn hóa đặc trưng cho LSTM (chuỗi 24 giờ)
    cac_dac_trung_lstm = list(scalers['lstm'].feature_names_in_)
    df_lstm_scaled = scalers['lstm'].transform(df[cac_dac_trung_lstm])
    
    # Tạo chuỗi dữ liệu 3D cho LSTM
    X_lstm_list = []
    # LSTM cần 24 dòng dữ liệu trước mốc t để dự báo cho mốc t
    for i in range(24, len(df)):
        X_lstm_list.append(df_lstm_scaled[i-24 : i])
        
    X_lstm_3d = np.array(X_lstm_list)
    
    # Dự báo bằng LSTM (mô hình dự báo trực tiếp nhiệt độ Celsius)
    y_pred_lstm = models['lstm'].predict(X_lstm_3d, verbose=0).flatten()
    
    # 3. Tạo DataFrame kết quả và lọc theo start_date
    # Vì LSTM bắt đầu có dự báo từ index 24 (bỏ qua 24 dòng context đầu tiên)
    result_df = df.iloc[24:].copy()
    
    result_df['pred_lr'] = y_pred_lr[24:]
    result_df['pred_xgb'] = y_pred_xgb[24:]
    result_df['pred_lstm'] = y_pred_lstm
    
    # Lọc lại đúng khoảng thời gian người dùng yêu cầu
    start_dt = pd.to_datetime(start_date_str)
    result_df['time'] = pd.to_datetime(result_df['time'])
    filtered_df = result_df[result_df['time'] >= start_dt]
    
    return filtered_df
