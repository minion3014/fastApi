import os
from fastapi import FastAPI, HTTPException, Query
import json
from typing import List, Dict, Optional
from logs.logger import app_logger

app = FastAPI()

# Sử dụng /data làm thư mục dữ liệu mặc định và đảm bảo không có dấu / ở cuối
DATA_DIR = os.path.normpath(os.getenv("DATA_DIR", "/data"))

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
    try:
        all_data = read_all_json_files(folder)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    filtered_data = filter_data_by_keyword(all_data, filter) if filter else all_data
    
    if filtered_data:
        return {
            "folder": folder,
            "filter": filter,
            "results": filtered_data
        }
    else:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu phù hợp")

# GET /api/sale để đọc dữ liệu từ thư mục /data/sale
# GET /api/sale?filter=example để tìm kiếm trong thư mục /data/sale
