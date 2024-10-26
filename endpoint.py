import os
from fastapi import FastAPI, HTTPException, Query
import json
from typing import List, Dict, Optional
from logs.logger import app_logger

app = FastAPI()

# Sử dụng /data làm thư mục dữ liệu mặc định
DATA_DIR = os.getenv("DATA_DIR", "/data")

def read_all_json_files() -> List[Dict]:
    if not os.path.exists(DATA_DIR):
        raise FileNotFoundError(f"Không tìm thấy thư mục: {DATA_DIR}")
    
    all_data = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(DATA_DIR, filename)
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

@app.get("/search")
async def search_data(filter_keyword: Optional[str] = Query(None)):
    try:
        all_data = read_all_json_files()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    filtered_data = filter_data_by_keyword(all_data, filter_keyword) if filter_keyword else all_data
    
    if filtered_data:
        return {
            "filter_keyword": filter_keyword,
            "results": filtered_data
        }
    else:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu phù hợp")

# GET /search để lấy tất cả dữ liệu
# GET /search?filter_keyword=example để tìm kiếm dữ liệu
