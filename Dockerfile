# 使用官方的Python基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制项目的依赖文件
COPY requirements.txt requirements.txt

# 安装项目的依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码到容器中
COPY src/ src/
COPY config/ config/

# 设置环境变量（如果需要）
ENV FLASK_APP=src/main.py

# 暴露应用程序的端口
EXPOSE 5005

# 启动应用程序
CMD ["flask", "run", "--host=0.0.0.0"]
