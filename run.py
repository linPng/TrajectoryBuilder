import sys
import os

# 将 src 目录添加到 PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5005)