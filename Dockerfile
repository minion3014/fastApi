# Sử dụng image Python chính thức
FROM python:3.9-slim

# Đặt thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements (nếu có) vào thư mục hiện tại
COPY requirements.txt .

# Cài đặt các dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn ứng dụng vào container
COPY . .


# Mở cổng mà ứng dụng FastAPI sẽ chạy
EXPOSE 5400

# Chạy ứng dụng
CMD ["uvicorn", "endpoint:app", "--host", "0.0.0.0", "--port", "5400"]

