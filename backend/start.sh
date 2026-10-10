#!/bin/bash

# 职业金属复合暴露智能干预推荐与决策支持系统 - 后端启动脚本

echo "=========================================="
echo "  职业金属复合暴露智能干预推荐与决策支持系统"
echo "  后端API服务启动"
echo "=========================================="

# 检查Python版本
python_version=$(python3 --version 2>&1)
if [[ $? -ne 0 ]]; then
    echo "错误: 未找到Python3，请先安装Python 3.10+"
    exit 1
fi
echo "Python版本: $python_version"

# 检查依赖是否安装
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "正在安装依赖..."
    pip3 install -r requirements.txt
    if [[ $? -ne 0 ]]; then
        echo "错误: 依赖安装失败"
        exit 1
    fi
fi

# 创建上传目录
mkdir -p data/uploads

# 启动服务
echo ""
echo "正在启动API服务..."
echo "API文档地址: http://localhost:8000/docs"
echo "按 Ctrl+C 停止服务"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
