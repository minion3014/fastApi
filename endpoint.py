import os
from fastapi import FastAPI, HTTPException, Query
import json
from typing import List, Dict, Optional
from logs.logger import app_logger

app = FastAPI()

# Mảng chứa các cặp từ khóa và tên thư mục
keyword_directory_mapping = [
    {"keywords": ["sản phẩm", "hàng hóa", "hang_hoa", "products", "san_pham","sanpham"], "directory": "products"},
    {"keywords": ["khách hàng", "customer", "khach_hang","khachang"], "directory": "customers"},
    {"keywords": ["Nhà cung cấp", "supplier","nha_cung_cap","nhacungcap"], "directory": "suppliers"},
    {"keywords": ["đơn hàng", "order", "don_hang","donhang"], "directory": "orders"},
    # Thêm các cặp khác tại đây
]

def read_json_files_in_directory(directory: str) -> List[Dict]:
    data_dir = "./data"  # Thư mục gốc chứa dữ liệu
    full_path = os.path.join(data_dir, directory)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Không tìm thấy thư mục: {full_path}")
    
    all_data = []
    for filename in os.listdir(full_path):
        if filename.endswith('.json'):
            file_path = os.path.join(full_path, filename)
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

def get_directory_for_keyword(keyword: str) -> Optional[str]:
    keyword = keyword.lower()
    for mapping in keyword_directory_mapping:
        if any(kw == keyword for kw in mapping["keywords"]):
            return mapping["directory"]
    return None

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

@app.get("/{file_keyword}")
async def search_data(file_keyword: str, filter_keyword: Optional[str] = Query(None)):
    directory = get_directory_for_keyword(file_keyword)
    
    if not directory:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy thư mục phù hợp cho từ khóa '{file_keyword}'")
    
    try:
        all_data = read_json_files_in_directory(directory)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    filtered_data = filter_data_by_keyword(all_data, filter_keyword) if filter_keyword else all_data
    
    if filtered_data:
        return {
            "file_keyword": file_keyword,
            "filter_keyword": filter_keyword,
            "directory": directory,
            "results": filtered_data
        }
    else:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy dữ liệu trong thư mục {directory}")

# Ví dụ sử dụng: /nhóm a?filter_keyword=sản phẩm x
