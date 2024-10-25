import os
from fastapi import FastAPI, HTTPException, Query
import json
from typing import List, Dict, Optional
from logger import app_logger

app = FastAPI()

# Mảng chứa các cặp từ khóa và tên file
keyword_file_mapping = [
    {"keywords": ["sản phẩm", "hàng hóa","hang_hoa","products", "san_pham","customer_data","sale_order"], "file": "test_data.json"},
    # Thêm các cặp khác tại đây
]

def read_json_data(file_path: str) -> List[Dict]:
    try:
        data_dir = "./data"
        full_path = os.path.join(data_dir, file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Không tìm thấy file: {full_path}")
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        app_logger.error(f"Lỗi: {e}")
        raise HTTPException(status_code=404, detail=f"Không tìm thấy file: {file_path}")
    except json.JSONDecodeError as e:
        app_logger.error(f"Lỗi khi đọc file JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi đọc file JSON: {file_path}")
    except Exception as e:
        app_logger.error(f"Lỗi không xác định: {e}")
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi khi đọc file")

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

def get_json_file_name(keyword: str) -> str:
    keyword = keyword.lower()
    for mapping in keyword_file_mapping:
        if any(kw == keyword for kw in mapping["keywords"]):
            return mapping["file"]
    return None

@app.get("/{file_keyword}")
async def search_data(file_keyword: str, filter_keyword: Optional[str] = Query(None)):
    json_file_name = get_json_file_name(file_keyword)
    
    if not json_file_name:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy file JSON phù hợp cho từ khóa '{file_keyword}'")
    
    data = read_json_data(json_file_name)
    filtered_data = filter_data_by_keyword(data, filter_keyword) if filter_keyword else data
    
    if filtered_data:
        return {
            "file_keyword": file_keyword,
            "filter_keyword": filter_keyword,
            "file": json_file_name,
            "results": filtered_data
        }
    else:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy dữ liệu trong file {json_file_name}")

# Ví dụ sử dụng: /nhóm a?filter_keyword=sản phẩm x
