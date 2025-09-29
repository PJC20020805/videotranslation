#!/usr/bin/env python3
"""
视频翻译系统配置文件
包含常量参数、错误码和API密钥配置
"""

from pathlib import Path

# ==================== 项目路径配置 ====================
# 项目根目录
PROJECT_ROOT = Path("/root/video-translation")

# 各功能目录
OUTPUT_DIR = PROJECT_ROOT / "output"
TEST_DIR = PROJECT_ROOT / "test"
LOGS_DIR = PROJECT_ROOT / "logs"
BIN_DIR = PROJECT_ROOT / "bin"
CACHE_DIR = PROJECT_ROOT / "cache"

# 确保目录存在
for directory in [OUTPUT_DIR, TEST_DIR, LOGS_DIR, BIN_DIR, CACHE_DIR]:
    directory.mkdir(exist_ok=True)

# ==================== API 配置 ====================
# Whisper API 配置
WHISPER_API_KEY = "sk-6e7hQ3zBKFK8cQR_sE6231Vqkbk9ChDrar4W9SRX3RWgiKqrQ0kXxuxKiMQ"
WHISPER_BASE_URL = "https://api.uniapi.vip/v1"

# 阿里云百炼 API 配置
DASHSCOPE_API_KEY = "sk-3e9a31f74e6744c98662a7df5e33ffb4"
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# ==================== 模型配置 ====================
# Whisper 模型配置
WHISPER_MODEL = "whisper-1"
WHISPER_LANGUAGE = "auto"  # 自动检测语言

# LLM 模型配置
DEFAULT_LLM_MODEL = "qwen-plus"
LLM_TEMPERATURE = 1.3  # 翻译任务推荐温度

# ==================== 处理参数配置 ====================
# 音频处理参数
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1

# 视频处理参数
DEFAULT_SUBTITLE_STYLE = {
    "font_size": 55,
    "font_color": "black",     # 黑色字幕
    "font_family": "SimHei",   # 中文字体
    "outline_color": "white",  # 白色轮廓
    "outline_width": 2,
    "position": "bottom_center"
}

# 文件大小限制（字节）
MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
MAX_AUDIO_DURATION = 1800  # 30分钟

# ==================== 错误码定义 ====================
ERROR_CODES = {
    # 通用状态
    "SUCCESS": "SUCCESS",
    
    # 音频相关
    "AUDIO_EXTRACT_FAILED": "AUDIO_EXTRACT_FAILED",
    "AUDIO_CONVERSION_FAILED": "AUDIO_CONVERSION_FAILED",
    "AUDIO_EMPTY_ERROR": "AUDIO_EMPTY_ERROR",
    
    # Whisper相关
    "WHISPER_MODEL_LOAD_FAILED": "WHISPER_MODEL_LOAD_FAILED",
    "WHISPER_API_ERROR": "WHISPER_API_ERROR",
    "WHISPER_TIMEOUT_ERROR": "WHISPER_TIMEOUT_ERROR",
    
    # LLM相关
    "LLM_API_ERROR": "LLM_API_ERROR",
    "LLM_ERROR": "LLM_ERROR",     # 表示LLM输出格式不通过筛选
    "LLM_TIMEOUT_ERROR": "LLM_TIMEOUT_ERROR",  
    
    # 字幕相关
    "SUBTITLE_EXTRACT_FAILED": "SUBTITLE_EXTRACT_FAILED",
    "SUBTITLE_EMPTY_ERROR": "SUBTITLE_EMPTY_ERROR",
    "SRT_SAVE_FAILED": "SRT_SAVE_FAILED",
    "SRT_PARSE_ERROR": "SRT_PARSE_ERROR",
    
    # 视频相关
    "VIDEO_ENCODE_FAILED": "VIDEO_ENCODE_FAILED",
    "VIDEO_DECODE_FAILED": "VIDEO_DECODE_FAILED",
    "VIDEO_RESOLUTION_ERROR": "VIDEO_RESOLUTION_ERROR",
    "FFMPEG_ERROR": "FFMPEG_ERROR",
    
    # 文件相关
    "FILE_ERROR": "FILE_ERROR",  # 例如某个文件过大、某个文件不存在、不受支持的文件格式等
    "PERMISSION_DENIED": "PERMISSION_DENIED",  
    
    # 系统与网络相关
    "NETWORK_ERROR": "NETWORK_ERROR",
    "RESOURCE_LIMIT_ERROR": "RESOURCE_LIMIT_ERROR",
    "DEPENDENCY_MISSING": "DEPENDENCY_MISSING",
    "INVALID_INPUT_ERROR": "INVALID_INPUT_ERROR",
    "CONCURRENCY_ERROR": "CONCURRENCY_ERROR"
}

# ==================== 日志配置 ====================
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 日志文件配置
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# ==================== 其他配置 ====================
# 支持的视频格式
SUPPORTED_VIDEO_FORMATS = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"]

# 支持的音频格式
SUPPORTED_AUDIO_FORMATS = [".wav", ".mp3", ".m4a", ".flac", ".aac"]

# 字幕模式
SUBTITLE_MODES = {
    "SOFT": "soft_subtitle",
    "HARD": "hard_burned"
}
