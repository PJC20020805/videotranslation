#!/usr/bin/env python3
"""
视频翻译系统日志记录器
提供彩色控制台输出、文件日志记录和函数调用装饰器
"""

import logging
import sys
import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Any, Callable, Optional

from config import LOGS_DIR, LOG_FORMAT, LOG_DATE_FORMAT, LOG_MAX_SIZE, LOG_BACKUP_COUNT


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }
    
    def format(self, record):
        # 添加颜色
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # 格式化消息
        formatted = super().format(record)
        return f"{log_color}{formatted}{reset_color}"


class VideoTranslationLogger:
    """视频翻译系统专用日志记录器"""
    
    def __init__(self, name: str = "VideoTranslation"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 控制台处理器 - 只显示 INFO 及以上级别
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(LOG_FORMAT, LOG_DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        
        # 文件处理器 - 记录所有级别，按大小滚动
        log_filename = f"video_translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_filepath = LOGS_DIR / log_filename
        
        file_handler = RotatingFileHandler(
            log_filepath,
            maxBytes=LOG_MAX_SIZE,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        
        # 添加处理器
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        self.logger.info(f"日志系统初始化完成，日志文件: {log_filepath}")
    
    def debug(self, message: str, **kwargs):
        """调试信息"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """一般信息"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """警告信息"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """错误信息"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """严重错误"""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """异常信息（包含堆栈跟踪）"""
        self.logger.exception(message, **kwargs)
    
    # ==================== 专用日志函数 ====================
    
    def log_audio_extraction(self, video_path: str, success: bool, duration: Optional[float] = None, error: str = ""):
        """音频提取日志"""
        if success:
            self.info(f"🎵 音频提取成功: {video_path} -> 时长: {duration:.2f}秒")
        else:
            self.error(f"❌ 音频提取失败: {video_path} - {error}")
    
    def log_whisper_recognition(self, audio_path: str, success: bool, segments_count: int = 0, error: str = ""):
        """Whisper 语音识别日志"""
        if success:
            self.info(f"🎤 语音识别成功: {audio_path} -> 识别到 {segments_count} 个语音段")
        else:
            self.error(f"❌ 语音识别失败: {audio_path} - {error}")
    
    def log_llm_translation(self, model: str, success: bool, segments_count: int = 0, error: str = ""):
        """LLM 翻译日志"""
        if success:
            self.info(f"🧠 LLM翻译成功: 模型={model} -> 翻译了 {segments_count} 个语音段")
        else:
            self.error(f"❌ LLM翻译失败: 模型={model} - {error}")
    
    def log_subtitle_generation(self, srt_path: str, success: bool, segments_count: int = 0, error: str = ""):
        """字幕生成日志"""
        if success:
            self.info(f"📝 字幕生成成功: {srt_path} -> 包含 {segments_count} 个字幕段")
        else:
            self.error(f"❌ 字幕生成失败: {srt_path} - {error}")
    
    def log_video_processing(self, input_path: str, output_path: str, success: bool, mode: str, error: str = ""):
        """视频处理日志"""
        if success:
            self.info(f"🎬 视频处理成功: {input_path} -> {output_path} (模式: {mode})")
        else:
            self.error(f"❌ 视频处理失败: {input_path} (模式: {mode}) - {error}")
    
    def log_task_summary(self, input_file: str, success: bool, processing_time: float, mode: str, error: str = ""):
        """整体翻译任务总结日志"""
        if success:
            self.info(f"✅ 翻译任务完成: {input_file} | 耗时: {processing_time:.2f}秒 | 模式: {mode}")
        else:
            self.critical(f"💥 翻译任务失败: {input_file} | 耗时: {processing_time:.2f}秒 | 模式: {mode} - {error}")


# 全局日志实例
logger = VideoTranslationLogger()


def log_function_call(func: Callable) -> Callable:
    """
    函数调用日志装饰器
    自动记录函数的调用、参数、返回值和异常
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        
        # 记录函数调用开始
        logger.debug(f"🔄 调用函数: {func_name}")
        logger.debug(f"📥 参数: args={args}, kwargs={kwargs}")
        
        try:
            # 执行函数
            start_time = datetime.now()
            result = func(*args, **kwargs)
            end_time = datetime.now()
            
            # 计算执行时间
            execution_time = (end_time - start_time).total_seconds()
            
            # 记录成功结果
            logger.debug(f"✅ 函数 {func_name} 执行成功，耗时: {execution_time:.3f}秒")
            logger.debug(f"📤 返回值: {result}")
            
            return result
            
        except Exception as e:
            # 记录异常信息
            logger.error(f"💥 函数 {func_name} 执行异常: {str(e)}")
            logger.debug(f"📋 异常堆栈:\n{traceback.format_exc()}")
            raise
    
    return wrapper


def log_cleanup_cache():
    """记录缓存清理日志"""
    logger.info("🧹 开始清理缓存文件...")


def log_cleanup_complete(cleaned_files: int, total_size: float):
    """记录缓存清理完成日志"""
    logger.info(f"✨ 缓存清理完成: 清理了 {cleaned_files} 个文件，释放 {total_size:.2f}MB 空间")


# ==================== 便捷函数 ====================

def get_logger() -> VideoTranslationLogger:
    """获取日志记录器实例"""
    return logger


def set_log_level(level: str):
    """设置日志级别"""
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    if level.upper() in level_map:
        logger.logger.setLevel(level_map[level.upper()])
        logger.info(f"日志级别已设置为: {level.upper()}")
    else:
        logger.warning(f"无效的日志级别: {level}")


if __name__ == "__main__":
    # 测试日志功能
    logger.info("测试日志系统")
    logger.debug("这是调试信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    
    # 测试装饰器
    @log_function_call
    def test_function(x, y):
        return x + y
    
    result = test_function(1, 2)
    logger.info(f"测试函数结果: {result}")
