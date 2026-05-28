# XayDungHeThongDuBaoThoiTiet

Du an du bao thoi tiet gom cac phan thu thap du lieu, tien xu ly du lieu va huan luyen mo hinh.

## Cau truc thu muc

```text
.
├── data/
│   ├── database/       # SQLite database
│   └── raw/            # CSV kiem tra/du lieu tho
├── models/
│   ├── preprocessors/  # Scaler, encoder va cac file tien xu ly
│   └── trained/        # Mo hinh da huan luyen
├── notebooks/          # Notebook thu thap, tien xu ly va training
├── src/                # Ma nguon chinh
└── tests/              # Script kiem tra nhanh
```

## Lenh hay dung

```bash
python src/collect_data.py
python tests/test_meteostat.py
```

Notebook tong quan du lieu: `notebooks/data_overview.ipynb`
