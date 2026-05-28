from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from app.database import get_latest_weather, get_historical_weather, get_weather_for_inference
from app.inference import run_predictions

router = APIRouter()

@router.get("/cities")
def read_cities():
    """Danh sách các thành phố được hỗ trợ."""
    return ["Ha Noi", "Da Nang", "TP HCM"]

@router.get("/weather/current")
def read_current_weather():
    """Lấy thời tiết hiện tại của 3 thành phố."""
    try:
        data = get_latest_weather()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather/history")
def read_historical_weather(
    city: str = Query(..., description="Tên thành phố"),
    days: int = Query(7, description="Số ngày cần lấy dữ liệu")
):
    """Lấy lịch sử thời tiết thực tế của một thành phố."""
    try:
        data = get_historical_weather(city, days)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
def read_metrics():
    """Bảng sai số MAE, RMSE, MAPE của các mô hình đã huấn luyện."""
    return {
        "Linear Regression": {
            "MAE": 0.336,
            "RMSE": 0.452,
            "MAPE": 1.326
        },
        "XGBoost Regressor": {
            "MAE": 0.316,
            "RMSE": 0.440,
            "MAPE": 1.250
        },
        "LSTM Deep Learning": {
            "MAE": 0.631,
            "RMSE": 0.874,
            "MAPE": 2.510
        }
    }

@router.get("/predict")
def predict_weather(
    city: str = Query(..., description="Tên thành phố"),
    start_date: str = Query(None, description="Mốc bắt đầu (Y-m-d H:M:S)"),
    end_date: str = Query(None, description="Mốc kết thúc (Y-m-d H:M:S)")
):
    """
    Chạy dự báo nhiệt độ của 3 mô hình so với thực tế.
    Nếu không truyền ngày, backend sẽ tự động lấy dữ liệu 7 ngày cuối cùng trong database để đối chiếu.
    """
    try:
        from app.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Nếu không truyền ngày, tự động xác định 7 ngày cuối cùng trong database
        if not start_date or not end_date:
            cursor.execute("SELECT MAX(time) FROM processed_weather WHERE city = ?", (city,))
            max_time_str = cursor.fetchone()[0]
            if not max_time_str:
                raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu cho thành phố này.")
            
            max_dt = datetime.strptime(max_time_str, "%Y-%m-%d %H:%M:%S")
            start_dt = max_dt - timedelta(days=7)
            
            start_date = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            end_date = max_time_str
            
        # Lấy dữ liệu mở rộng (bao gồm cả 24 giờ trước để làm context cho LSTM)
        df_inference = get_weather_for_inference(city, start_date, end_date)
        
        if df_inference.empty or len(df_inference) <= 24:
            raise HTTPException(
                status_code=400, 
                detail=f"Không đủ dữ liệu cho thành phố {city} trong khoảng thời gian {start_date} -> {end_date}."
            )
            
        # Chạy suy diễn mô hình
        result_df = run_predictions(df_inference, start_date)
        
        # Format kết quả trả về
        result = []
        for _, row in result_df.iterrows():
            result.append({
                "time": row["time"].strftime("%Y-%m-%d %H:%M:%S"),
                "actual": float(row["temp"]),
                "lr": float(row["pred_lr"]),
                "xgb": float(row["pred_xgb"]),
                "lstm": float(row["pred_lstm"])
            })
            
        return {
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
            "predictions": result
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions/errors")
def read_predictions_errors(
    city: str = Query(..., description="Tên thành phố"),
    limit: int = Query(48, description="Số lượng bản ghi gần nhất")
):
    """Lấy lịch sử sai số dự báo thực tế để hiển thị trên frontend."""
    try:
        from app.database import get_error_history
        data = get_error_history(city, limit)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
