# 基於 Python 3.10 映像
FROM python:3.10

# 設置工作目錄，對應 FastAPI 應用的目錄
WORKDIR /workspace/project/fastapi

# 複製項目相關文件夾到容器中
COPY ./project/fastapi /workspace/project/fastapi
COPY ./myproject /workspace/myproject
COPY ./requirements.txt /workspace/

# 安裝依賴，確保在正確目錄下
RUN pip install --no-cache-dir -r /workspace/requirements.txt

# 暴露端口
EXPOSE 8080

# 設置啟動命令，確保 FastAPI 應用路徑正確
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8080"]