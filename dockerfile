# 第一階段: 安裝依賴和準備環境，使用 slim 基礎映像
FROM python:3.10-slim AS builder

# 安裝必要的系統依賴，如 gdal 和構建工具
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    build-essential \
    && apt-get clean

# 設置工作目錄
WORKDIR /workspace/project/map_application

# 複製 requirements.txt
COPY ./requirements.txt /workspace/

# 安裝所有依賴
RUN pip install --no-cache-dir -r /workspace/requirements.txt

# 第二階段: 建立最小化的最終映像
FROM python:3.10-slim

# 複製第一階段已經安裝好的依賴
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 設置工作目錄
WORKDIR /workspace/project/map_application

# 複製剩餘的項目文件
COPY ./project /workspace/project
COPY ./function /workspace/function
COPY ./warehouse /workspace/warehouse

# 設置 PYTHONPATH
ENV PYTHONPATH=/workspace/project/map_application:/workspace/function

# 暴露端口
EXPOSE 8080

# 啟動服務
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
