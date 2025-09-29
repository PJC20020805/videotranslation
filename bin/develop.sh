#!/bin/bash
# 开发环境启动脚本
# Development Environment Startup Script

set -e

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 视频翻译系统 - 开发环境"
echo "================================"
echo "📁 项目目录: $PROJECT_ROOT"

# 检查Python版本
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "🐍 Python版本: $python_version"

# 检查依赖
echo "📦 检查依赖包..."
if ! python3 -c "import openai" 2>/dev/null; then
    echo "⚠️  缺少openai包，正在安装..."
    pip3 install openai
fi

if ! python3 -c "import requests" 2>/dev/null; then
    echo "⚠️  缺少requests包，正在安装..."
    pip3 install requests
fi

# 检查FFmpeg
echo "🎬 检查FFmpeg..."
if command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg_version=$(ffmpeg -version 2>&1 | head -n1 | cut -d' ' -f3)
    echo "✅ FFmpeg版本: $ffmpeg_version"
else
    echo "❌ FFmpeg未安装，请先安装:"
    echo "   Ubuntu/Debian: sudo apt install ffmpeg"
    echo "   CentOS/RHEL: sudo yum install ffmpeg"
    exit 1
fi

# 创建必要目录
echo "📁 创建目录结构..."
mkdir -p output/{videos,subtitles,audio}
mkdir -p cache
mkdir -p logs
echo "✅ 目录结构创建完成"

# 检查测试视频
echo "🎥 检查测试视频..."
if [ -f "video.mp4" ]; then
    video_size=$(du -h video.mp4 | cut -f1)
    echo "✅ 找到测试视频: video.mp4 ($video_size)"
elif [ -f "video_test_2min.mp4" ]; then
    video_size=$(du -h video_test_2min.mp4 | cut -f1)
    echo "✅ 找到测试视频: video_test_2min.mp4 ($video_size)"
else
    echo "⚠️  未找到测试视频文件"
    echo "   请将MP4视频文件放在项目根目录"
fi

echo ""
echo "🎯 开发环境准备完成！"
echo ""
echo "📋 可用命令:"
echo "   python3 main.py video.mp4                    # 软嵌入模式"
echo "   python3 main.py video.mp4 hard_burned        # 硬烧录模式"
echo "   python3 test/test_whisper_detection.py video.mp4"
echo "   python3 test/test_LLM_translation.py output/whisper_detection_output.json"
echo ""
echo "📚 查看帮助:"
echo "   python3 main.py --help"
echo ""

# 如果有参数，直接执行
if [ $# -gt 0 ]; then
    echo "🚀 执行命令: python3 main.py $@"
    python3 main.py "$@"
fi
