# 使用 Python 3.10 作為基礎映像
FROM python:3.10

# 設置工作目錄到項目根目錄
WORKDIR /workspace/project/map_application

# 複製項目文件夾到容器中
COPY ./project /workspace/project
COPY ./requirements.txt /workspace/
COPY ./function /workspace/function
COPY ./warehouse /workspace/warehouse

# 設置 PYTHONPATH 以包含 /workspace 目錄
ENV PYTHONPATH=/workspace/project/map_application:/workspace/function

# 安裝依賴，確保在正確目錄下
RUN pip install --no-cache-dir -r /workspace/requirements.txt

# 暴露端口
EXPOSE 8080

# 設置啟動命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]