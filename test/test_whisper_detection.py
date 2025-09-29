#!/usr/bin/env python3
"""
Whisper语音识别测试脚本
测试从视频文件中提取音频并进行语音识别
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from video_translator import separate_wav, whisper_detection
from logger import logger
from config import PROJECT_ROOT, OUTPUT_DIR


def test_whisper_detection(video_path: str):
    """
    测试Whisper语音识别功能
    
    Args:
        video_path: 视频文件路径
    """
    logger.info("=" * 60)
    logger.info("🧪 开始测试 Whisper 语音识别")
    logger.info("=" * 60)
    
    try:
        # 检查输入文件
        input_path = Path(video_path)
        if not input_path.exists():
            logger.error(f"视频文件不存在: {video_path}")
            return False
        
        logger.info(f"📁 输入视频: {input_path.name}")
        logger.info(f"📏 文件大小: {input_path.stat().st_size / (1024*1024):.2f} MB")
        
        # 步骤1: 音频分离
        logger.info("\n🎵 步骤1: 音频分离")
        logger.info("-" * 40)
        
        audio_success, audio_path, audio_duration, audio_error_code, audio_error_detail = separate_wav(video_path)
        
        if not audio_success:
            logger.error(f"音频分离失败: {audio_error_detail}")
            return False
        
        logger.info(f"✅ 音频分离成功")
        logger.info(f"🎵 音频文件: {Path(audio_path).name}")
        logger.info(f"⏰ 音频时长: {audio_duration:.2f} 秒")
        
        # 步骤2: Whisper语音识别
        logger.info("\n🎤 步骤2: Whisper语音识别")
        logger.info("-" * 40)
        
        whisper_success, whisper_result, whisper_error_code, whisper_error_detail = whisper_detection(audio_path)
        
        if not whisper_success:
            logger.error(f"Whisper识别失败: {whisper_error_detail}")
            return False
        
        logger.info(f"✅ Whisper识别成功")
        logger.info(f"📝 识别到 {len(whisper_result['segments'])} 个语音段")
        
        # 打印识别结果
        logger.info("\n📄 识别结果预览:")
        logger.info("-" * 40)
        
        for i, segment in enumerate(whisper_result['segments'][:5], 1):  # 只显示前5个
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text'].strip()
            
            print(f"段落 {i:2d}: [{start_time:6.1f}s - {end_time:6.1f}s] {text}")
        
        if len(whisper_result['segments']) > 5:
            print(f"... 还有 {len(whisper_result['segments']) - 5} 个语音段")
        
        # 保存完整结果到JSON文件
        output_file = OUTPUT_DIR / "whisper_detection_output.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(whisper_result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n💾 完整结果已保存到: {output_file}")
        
        # 打印完整的JSON格式结果（带换行）
        print("\n" + "="*60)
        print("📋 完整识别结果 (JSON格式)")
        print("="*60)
        print(json.dumps(whisper_result, ensure_ascii=False, indent=2))
        print("="*60)
        
        logger.info("🎉 Whisper语音识别测试完成")
        return True
        
    except Exception as e:
        logger.exception(f"测试过程异常: {str(e)}")
        return False


def main():
    """主函数"""
    print("🧪 Whisper语音识别测试工具")
    print("="*50)
    
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("使用方法: python test_whisper_detection.py <video_path>")
        print("示例: python test_whisper_detection.py ../video.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    # 如果是相对路径，转换为绝对路径
    if not Path(video_path).is_absolute():
        video_path = str(PROJECT_ROOT / video_path)
    
    # 执行测试
    success = test_whisper_detection(video_path)
    
    if success:
        print("\n✅ 测试成功完成！")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()