# TrajectoryBuilder
This project generates trajectory coordinates and provides API services for both Linux and Windows environments.
## 使用和运行
### 安装依赖
pip install -r requirements.txt
### 运行服务
python src/main.py
### 运行测试
python -m unittest discover -s tests
## 构建和运行Docker镜像
### 构建Docker镜像
docker build -t trajectorybuilder .
### 运行Docker容器
docker run -d -p 5000:5000 trajectorybuilder