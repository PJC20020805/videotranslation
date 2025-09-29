#!/bin/bash
# 生产环境启动脚本
# Production Environment Startup Script

set -e

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 视频翻译系统 - 生产环境"
echo "================================"

# 检查参数
if [ $# -lt 1 ]; then
    echo "使用方法: $0 <video_path> [output_mode]"
    echo "示例: $0 video.mp4 soft_subtitle"
    exit 1
fi

VIDEO_PATH="$1"
OUTPUT_MODE="${2:-soft_subtitle}"

# 检查视频文件
if [ ! -f "$VIDEO_PATH" ]; then
    echo "❌ 错误: 视频文件不存在: $VIDEO_PATH"
    exit 1
fi

# 生成日志文件名
LOG_FILE="logs/production_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs

echo "📁 输入视频: $VIDEO_PATH"
echo "🎯 输出模式: $OUTPUT_MODE"
echo "📝 日志文件: $LOG_FILE"
echo ""

# 后台运行并记录日志
echo "🔄 启动视频翻译任务..."
nohup python3 main.py "$VIDEO_PATH" "$OUTPUT_MODE" > "$LOG_FILE" 2>&1 &

PID=$!
echo "✅ 任务已启动 (PID: $PID)"
echo "📊 查看日志: tail -f $LOG_FILE"
echo "🛑 停止任务: kill $PID"
echo ""

# 等待几秒钟检查进程状态
sleep 3
if kill -0 $PID 2>/dev/null; then
    echo "✅ 任务正在运行中..."
    echo "💡 提示: 使用 'tail -f $LOG_FILE' 查看实时日志"
else
    echo "❌ 任务启动失败，请检查日志: $LOG_FILE"
    exit 1
fi
