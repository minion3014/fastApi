import os
from fastapi import FastAPI, HTTPException, Query
import json
from typing import List, Dict, Optional
from logs.logger import app_logger

app = FastAPI()

# Sử dụng /data làm thư mục dữ liệu mặc định và đảm bảo không có dấu / ở cuối
DATA_DIR = os.path.normpath(os.getenv("DATA_DIR", "/data"))

# Định nghĩa mapping giữa từ khóa và thư mục
FOLDER_KEYWORDS = {
    "sale": [
        # Từ khóa về bán hàng cơ bản
        "sale", "promotion", "customer", "donhang", "khachhang", "order", "khuyenmai", "discount",
        # Từ khóa về giao dịch
        "giaodich", "transaction", "hoadon", "invoice", "bill",
        # Từ khóa về khách hàng
        "daily", "doitac", "partner", "member", "thanhvien",
        # Từ khóa về chương trình khuyến mãi
        "voucher", "coupon", "giamgia", "tichdiem", "loyalty",
        # Từ khóa về doanh số
        "doanhso", "sales",
        # Từ khóa về đơn hàng
        "dathang", "purchase", "booking", "shipping", "vanchuyen"
    ],
    "product": [
        # Từ khóa tiếng Việt cơ bản
        "sanpham", "hanghoa", "mathang", 
        # Từ khóa về đơn vị
        "donvi", "unit", "quy_cach",
        # Từ khóa về danh mục
        "danhmuc", "nhomhang", "loaihang", "category",
        # Từ khóa về thông tin sản phẩm
        "product", "item", "goods", "commodity",
        # Từ khóa về mã sản phẩm
        "masanpham", "mahang", "sku", "barcode",
        # Từ khóa về thương hiệu
        "thuonghieu", "brand",
        # Từ khóa về thông số kỹ thuật
        "thongso", "specification"
    ],
    "kpi": [
        # Từ khóa về KPI và doanh thu
        "kpi", "doanhthu", "revenue", "target", "muctieu", "chitieu",
        # Từ khóa về hiệu suất
        "hieuqua", "performance", "productivity", "nangxuat",
        # Từ khóa về chỉ số
        "chiso", "metric", "benchmark", "indicator",
        # Từ khóa về đánh giá
        "danhgia", "evaluation", "assessment", "rating",
        # Từ khóa về mục tiêu kinh doanh
        "goal", "objective", "achievement", "thanhqua",
        # Từ khóa về báo cáo hiệu suất
        "baocao", "report", "dashboard", "bangdieukhien",
        # Từ khóa về tăng trưởng
        "growth", "tangtruong", "progress", "tiendo"
    ],
}

def get_folder_from_keyword(keyword: str) -> Optional[str]:
    keyword = keyword.lower()
    for folder, keywords in FOLDER_KEYWORDS.items():
        if keyword in keywords:
            return folder
    return None

def read_all_json_files(subfolder: Optional[str] = None) -> List[Dict]:
    base_dir = DATA_DIR
    if subfolder:
        base_dir = os.path.join(DATA_DIR, subfolder)
    
    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"Không tìm thấy thư mục: {base_dir}")
    
    all_data = []
    for filename in os.listdir(base_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(base_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    else:
                        all_data.append(data)
            except json.JSONDecodeError as e:
                app_logger.error(f"Lỗi khi đọc file JSON {file_path}: {e}")
            except Exception as e:
                app_logger.error(f"Lỗi không xác định khi đọc file {file_path}: {e}")

    return all_data

def filter_data_by_keyword(data: List[Dict], keyword: str) -> List[Dict]:
    if not keyword:
        return data
    filtered_data = []
    for item in data:
        for key, value in item.items():
            if isinstance(value, str) and keyword.lower() in value.lower():
                filtered_data.append(item)
                break
            if isinstance(value, (int, float)) and keyword.lower() in str(value).lower():
                filtered_data.append(item)
                break
    return filtered_data

@app.get("/api/{folder}")
async def search_data(
    folder: str,
    filter: Optional[str] = Query(None, description="Từ khóa tìm kiếm trong dữ liệu")
):
    # Tìm thư mục tương ứng từ từ khóa
    actual_folder = get_folder_from_keyword(folder)
    if not actual_folder:
        raise HTTPException(
            status_code=400, 
            detail=f"Không tìm thấy thư mục phù hợp với từ khóa: {folder}"
        )
    
    try:
        all_data = read_all_json_files(actual_folder)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    filtered_data = filter_data_by_keyword(all_data, filter) if filter else all_data
    
    if filtered_data:
        return {
            "folder": actual_folder,
            "original_keyword": folder,
            "filter": filter,
            "results": filtered_data
        }
    else:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu phù hợp")

# GET /api/sale để đọc dữ liệu từ thư mục /data/sale
# GET /api/sale?filter=example để tìm kiếm trong thư mục /data/sale
