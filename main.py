#!/usr/bin/env python3
"""
视频翻译系统主程序入口
支持命令行调用和参数解析
"""

import argparse
import sys
import json
from pathlib import Path

from video_translator import VideoTranslation
from logger import logger
from config import SUBTITLE_MODES


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="视频翻译系统 - 基于 Whisper + LLM 的智能视频字幕翻译",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py video.mp4                    # 软嵌入模式（默认）
  python main.py video.mp4 soft_subtitle      # 软嵌入模式
  python main.py video.mp4 hard_burned        # 硬烧录模式
  
支持的输出模式:
  soft_subtitle  - 生成SRT字幕文件（默认）
  hard_burned    - 字幕直接烧录到视频中
        """
    )
    
    parser.add_argument(
        "video_path",
        help="输入的MP4视频文件路径"
    )
    
    parser.add_argument(
        "output_mode",
        nargs="?",
        default="soft_subtitle",
        choices=["soft_subtitle", "hard_burned"],
        help="输出模式 (默认: soft_subtitle)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        help="输出目录路径（可选）"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="日志级别 (默认: INFO)"
    )
    
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="不清理缓存文件"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="视频翻译系统 v1.0.0"
    )
    
    return parser.parse_args()


def validate_arguments(args):
    """验证命令行参数"""
    errors = []
    
    # 检查视频文件路径
    video_path = Path(args.video_path)
    if not video_path.exists():
        errors.append(f"视频文件不存在: {args.video_path}")
    elif not video_path.is_file():
        errors.append(f"路径不是文件: {args.video_path}")
    elif video_path.suffix.lower() not in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']:
        errors.append(f"不支持的视频格式: {video_path.suffix}")
    
    # 检查输出目录（如果指定）
    if args.output_dir:
        output_dir = Path(args.output_dir)
        if output_dir.exists() and not output_dir.is_dir():
            errors.append(f"输出路径不是目录: {args.output_dir}")
    
    return errors


def print_banner():
    """打印程序横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                     视频翻译系统 v1.0.0                      ║
║                Video Translation System                      ║
║                                                              ║
║  🎵 音轨分离  🎤 语音识别  🧠 智能翻译  📝 字幕生成  🎬 视频处理  ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_result_summary(result: dict):
    """打印结果摘要"""
    print("\n" + "="*60)
    print("📊 处理结果摘要")
    print("="*60)
    
    # 基本信息
    print(f"📁 输入文件: {result['inputFile']}")
    print(f"⏱️  处理时间: {result['processingTime']:.2f} 秒")
    print(f"🎯 输出模式: {result['outputMode']}")
    
    # 处理状态
    status_icon = "✅" if result['success'] else "❌"
    print(f"{status_icon} 处理状态: {result['message']}")
    
    if result['success']:
        # 成功情况下的详细信息
        print(f"🎵 音频提取: {'✅' if result['audioExtracted'] else '❌'}")
        if result['audioDuration']:
            print(f"⏰ 音频时长: {result['audioDuration']:.2f} 秒")
        
        print(f"🎤 语音识别: {'✅' if result['whisperHandled'] else '❌'}")
        print(f"📝 字幕生成: {'✅' if result['subtitleExtracted'] else '❌'}")
        
        # 输出文件信息
        if result['outputMode'] == 'soft_subtitle' and 'translatedSubtitlePath' in result:
            print(f"📄 字幕文件: {result['translatedSubtitlePath']}")
        elif result['outputMode'] == 'hard_burned' and 'outputVideoPath' in result:
            print(f"🎬 输出视频: {result['outputVideoPath']}")
            if 'videoResolution' in result:
                print(f"📐 视频分辨率: {result['videoResolution']}")
    else:
        # 失败情况下的错误信息
        if 'errorCode' in result:
            print(f"💥 错误代码: {result['errorCode']}")
        if 'errorDetails' in result:
            print(f"📋 错误详情: {result['errorDetails']}")
    
    print("="*60)


def main():
    """主函数"""
    try:
        # 打印横幅
        print_banner()
        
        # 解析命令行参数
        args = parse_arguments()
        
        # 设置日志级别
        from logger import set_log_level
        set_log_level(args.log_level)
        
        logger.info("视频翻译系统启动")
        logger.info(f"命令行参数: {vars(args)}")
        
        # 验证参数
        validation_errors = validate_arguments(args)
        if validation_errors:
            logger.error("参数验证失败:")
            for error in validation_errors:
                logger.error(f"  - {error}")
                print(f"❌ 错误: {error}")
            sys.exit(1)
        
        # 创建翻译器实例
        logger.info("初始化视频翻译器...")
        translator = VideoTranslation()
        
        # 验证输入文件
        is_valid, validation_msg = translator.validate_input_file(args.video_path)
        if not is_valid:
            logger.error(f"输入文件验证失败: {validation_msg}")
            print(f"❌ 错误: {validation_msg}")
            sys.exit(1)
        
        # 显示文件信息
        video_path = Path(args.video_path)
        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        print(f"📁 输入文件: {video_path.name}")
        print(f"📏 文件大小: {file_size_mb:.2f} MB")
        print(f"🎯 输出模式: {args.output_mode}")
        print(f"📊 日志级别: {args.log_level}")
        print()
        
        # 开始翻译处理
        logger.info("开始视频翻译处理...")
        print("🚀 开始处理，请耐心等待...")
        print()
        
        result = translator.translation(
            mp4_file_path=args.video_path,
            output_mode=args.output_mode
        )
        
        # 打印结果摘要
        print_result_summary(result)
        
        # 根据处理结果设置退出码
        if result['success']:
            logger.info("视频翻译任务完成")
            print("🎉 翻译完成！")
            sys.exit(0)
        else:
            logger.error("视频翻译任务失败")
            print("💥 翻译失败！")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("用户中断程序执行")
        print("\n⚠️  程序被用户中断")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"程序执行异常: {str(e)}")
        print(f"\n💥 程序异常: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
