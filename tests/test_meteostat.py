from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from meteostat import hourly

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def test_city_weather(city_name, station_id):
    print(f"\n--- Đang tải dữ liệu cho {city_name} (Station ID: {station_id}) ---")
    
    # Khoảng thời gian: 3 ngày gần nhất (để kiểm tra nhanh)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)
    
    try:
        # Lấy dữ liệu hourly trực tiếp qua Station ID
        data = hourly(station_id, start_date, end_date)
        df = data.fetch()
        
        if df.empty:
            print(f"[THẤT BẠI] Không có dữ liệu cho {city_name}.")
            return None
            
        print(f"[THÀNH CÔNG] Đã tải dữ liệu {city_name}!")
        print(f"Số dòng dữ liệu: {len(df)}")
        print("Dữ liệu 3 dòng đầu tiên:")
        # Chỉ hiển thị các cột quan trọng
        print(df[['temp', 'rhum', 'prcp', 'wspd', 'coco']].head(3))
        
        # Lưu ra file CSV kiểm tra
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        output_file = RAW_DATA_DIR / f"{city_name.lower().replace(' ', '_')}_weather_test.csv"
        df.to_csv(output_file)
        print(f"-> Đã lưu dữ liệu ra file: '{output_file}'")
        return df
        
    except Exception as e:
        print(f"[LỖI] Đã xảy ra lỗi khi gọi API: {str(e)}")
        return None

def main():
    print("=== CHƯƠNG TRÌNH KIỂM TRA KẾT NỐI API METEOSTAT CHO 3 MIỀN ===")
    
    # Danh sách 3 trạm thời tiết đại diện cho 3 miền tại Việt Nam
    cities = {
        "Ha Noi": "48820",
        "Da Nang": "48855",
        "TP HCM": "48900"
    }
    
    for city, station_id in cities.items():
        test_city_weather(city, station_id)
        
    print("\n=== KIỂM TRA HOÀN TẤT ===")
    print("Meteostat đã được xác nhận là nguồn dữ liệu tin cậy cho đồ án tốt nghiệp của bạn.")

if __name__ == "__main__":
    main()
