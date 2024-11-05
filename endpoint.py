import os
from fastapi import FastAPI, HTTPException, Query
import json
from typing import List, Dict, Optional
from logs.logger import app_logger
import re

app = FastAPI()

# Sử dụng /data làm thư mục dữ liệu mặc định
DATA_DIR = os.path.normpath(os.getenv("DATA_DIR", "/data"))

# Định nghĩa mapping giữa từ khóa và thư mục
FOLDER_KEYWORDS = {
    "sale": [
        "sale", "promotion", "customer", "donhang", "khachhang", "order", 
        "khuyenmai", "discount", "giaodich", "transaction", "hoadon", 
        "invoice", "bill", "daily", "doitac", "partner", "member", 
        "thanhvien", "voucher", "coupon", "giamgia", "tichdiem", 
        "loyalty", "doanhso", "sales", "dathang", "purchase", 
        "booking", "shipping", "vanchuyen"
    ],
    "product": [
        "sanpham", "hanghoa", "mathang", "donvi", "unit", "quy_cach",
        "danhmuc", "nhomhang", "loaihang", "category", "product", 
        "item", "goods", "commodity", "masanpham", "mahang", "sku", 
        "barcode", "thuonghieu", "brand", "thongso", "specification"
    ],
    "kpi": [
        "kpi", "doanhthu", "revenue", "target", "muctieu", "chitieu",
        "hieuqua", "performance", "productivity", "nangxuat", "chiso", 
        "metric", "benchmark", "indicator", "danhgia", "evaluation", 
        "assessment", "rating", "goal", "objective", "achievement", 
        "thanhqua", "baocao", "report", "dashboard", "bangdieukhien",
        "growth", "tangtruong", "progress", "tiendo"
    ],
}

def normalize_string(text: str) -> str:
    """
    Chuẩn hóa chuỗi:
    - Chuyển về chữ thường
    - Loại bỏ dấu tiếng Việt
    - Loại bỏ khoảng trắng và ký tự đặc biệt
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Mapping dấu tiếng Việt
    vietnamese_map = {
        'à':'a', 'á':'a', 'ả':'a', 'ã':'a', 'ạ':'a',
        'ă':'a', 'ằ':'a', 'ắ':'a', 'ẳ':'a', 'ẵ':'a', 'ặ':'a',
        'â':'a', 'ầ':'a', 'ấ':'a', 'ẩ':'a', 'ẫ':'a', 'ậ':'a',
        'è':'e', 'é':'e', 'ẻ':'e', 'ẽ':'e', 'ẹ':'e',
        'ê':'e', 'ề':'e', 'ế':'e', 'ể':'e', 'ễ':'e', 'ệ':'e',
        'ì':'i', 'í':'i', 'ỉ':'i', 'ĩ':'i', 'ị':'i',
        'ò':'o', 'ó':'o', 'ỏ':'o', 'õ':'o', 'ọ':'o',
        'ô':'o', 'ồ':'o', 'ố':'o', 'ổ':'o', 'ỗ':'o', 'ộ':'o',
        'ơ':'o', 'ờ':'o', 'ớ':'o', 'ở':'o', 'ỡ':'o', 'ợ':'o',
        'ù':'u', 'ú':'u', 'ủ':'u', 'ũ':'u', 'ụ':'u',
        'ư':'u', 'ừ':'u', 'ứ':'u', 'ử':'u', 'ữ':'u', 'ự':'u',
        'ỳ':'y', 'ý':'y', 'ỷ':'y', 'ỹ':'y', 'ỵ':'y',
        'đ':'d',
        # Thêm các ký tự đặc biệt khác nếu cần
        'Đ':'d',
        'ữ':'u',
        'ỹ':'y'
    }
    
    # Chuyển về chữ thường
    text = text.lower()
    
    # Loại bỏ dấu tiếng Việt
    for vietnamese, latin in vietnamese_map.items():
        text = text.replace(vietnamese, latin)
    
    # Chỉ giữ lại chữ cái và số, loại bỏ các ký tự đặc biệt và khoảng trắng
    text = ''.join(c for c in text if c.isalnum())
    
    return text

def get_folder_from_keyword(keyword: str) -> Optional[str]:
    """Xác định thư mục từ từ khóa"""
    keyword = keyword.lower()
    for folder, keywords in FOLDER_KEYWORDS.items():
        if keyword in keywords:
            return folder
    return None

def read_all_json_files(subfolder: Optional[str] = None) -> List[Dict]:
    """Đọc tất cả file JSON trong thư mục"""
    base_dir = os.path.join(DATA_DIR, subfolder) if subfolder else DATA_DIR
    
    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"Không tìm thấy thư mục: {base_dir}")
    
    all_data = []
    for filename in os.listdir(base_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(base_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    all_data.extend(data) if isinstance(data, list) else all_data.append(data)
            except Exception as e:
                app_logger.error(f"Lỗi khi đọc file {file_path}: {e}")
    return all_data

def filter_data_by_keyword(data: List[Dict], keyword: str) -> List[Dict]:
    """Lọc dữ liệu theo từ khóa"""
    if not keyword:
        return data
    
    normalized_keyword = normalize_string(keyword)
    return [
        item for item in data 
        if any(normalized_keyword in normalize_string(str(value)) 
              for value in item.values())
    ]

def parse_query(question: str):
    """
    Phân tích câu hỏi tự nhiên
    Ví dụ: 'KPI của Cửa Hàng Kim Khí Kim Phương (Phù Cát)'
    """
    # Lưu câu gốc trước khi chuẩn hóa để tìm kiếm pattern
    original_question = question.lower()
    params = {"folder": None, "filters": []}
    
    # Xác định folder từ câu gốc (chưa chuẩn hóa)
    for folder, keywords in FOLDER_KEYWORDS.items():
        if any(keyword in original_question for keyword in keywords):
            params["folder"] = folder
            break
    
    # Tìm thông tin thời gian từ câu gốc
    time_patterns = {
        "thang": r"th[aá]ng\s*(\d{1,2})",
        "quy": r"qu[yý]\s*(\d{1})",
        "nam": r"n[aă]m\s*(\d{4})"
    }
    
    for time_type, pattern in time_patterns.items():
        if match := re.search(pattern, original_question):
            time_value = normalize_string(f"{time_type}{match.group(1)}")
            params["filters"].append(time_value)
    
    # Tìm tên cửa hàng/người từ câu gốc
    for indicator in ["của", "cho", "về"]:
        if indicator in original_question:
            # Tách phần sau indicator
            name_part = original_question.split(indicator)[1].strip()
            # Loại bỏ phần thời gian và các dấu ngoặc
            name_part = re.sub(r"(tháng|quý|năm).*?(?=\(|\)|\Z)", "", name_part)
            name_part = re.sub(r"[\(\)]", "", name_part).strip()
            if name_part:
                normalized_name = normalize_string(name_part)
                if normalized_name:  # Chỉ thêm nếu tên không rỗng
                    params["filters"].append(normalized_name)
            break
    
    # Log để debug
    app_logger.info(f"Original question: {question}")
    app_logger.info(f"Parsed params: {params}")
    
    return params

@app.get("/api/query")
async def query_data(question: str = Query(..., description="Câu hỏi tự nhiên")):
    """Xử lý câu hỏi tự nhiên và trả về kết quả"""
    params = parse_query(question)
    
    if not params["folder"]:
        raise HTTPException(
            status_code=400,
            detail="Không thể xác định loại dữ liệu cần tìm từ câu hỏi"
        )
    
    try:
        all_data = read_all_json_files(params["folder"])
        filtered_data = all_data
        
        # Log để debug
        app_logger.info(f"Filters: {params['filters']}")
        
        for filter_keyword in params["filters"]:
            filtered_data = filter_data_by_keyword(filtered_data, filter_keyword)
            # Log số lượng kết quả sau mỗi lần lọc
            app_logger.info(f"Sau khi lọc '{filter_keyword}': {len(filtered_data)} kết quả")
        
        if not filtered_data:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy dữ liệu phù hợp với yêu cầu"
            )
            
        return {
            "folder": params["folder"],
            "original_question": question,
            "parsed_filters": params["filters"],
            "results": filtered_data
        }
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))