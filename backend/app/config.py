import os

# Đường dẫn gốc của toàn bộ dự án (XayDungHeThongDuBaoThoiTiet)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Đường dẫn SQLite database
DB_PATH = os.path.join(BASE_DIR, "data", "database", "weather_data.db")

# Thư mục chứa các mô hình
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Đường dẫn các bộ chuẩn hóa (preprocessors)
SCALER_FEATURES_PATH = os.path.join(MODELS_DIR, "preprocessors", "scaler_features.pkl")
SCALER_TARGET_PATH = os.path.join(MODELS_DIR, "preprocessors", "scaler_target.pkl")
SCALER_LSTM_PATH = os.path.join(MODELS_DIR, "preprocessors", "scaler_lstm_features.pkl")

# Đường dẫn các mô hình huấn luyện
XGB_MODEL_PATH = os.path.join(MODELS_DIR, "trained", "xgboost_weather_model.json")
LSTM_MODEL_PATH = os.path.join(MODELS_DIR, "trained", "lstm_weather_model.keras")
LR_MODEL_PATH = os.path.join(MODELS_DIR, "trained", "linear_regression_model.pkl")
