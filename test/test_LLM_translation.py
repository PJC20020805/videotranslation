#!/usr/bin/env python3
"""
LLM翻译测试脚本
测试对Whisper识别结果进行中文翻译
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from video_translator import LLM_translation
from logger import logger
from config import PROJECT_ROOT, OUTPUT_DIR, DEFAULT_LLM_MODEL


def load_whisper_result(json_file_path: str) -> dict:
    """
    从JSON文件加载Whisper识别结果
    
    Args:
        json_file_path: JSON文件路径
        
    Returns:
        dict: Whisper识别结果
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载JSON文件失败: {str(e)}")
        return None


def compare_results(original_result: dict, translated_result: dict):
    """
    比较原始结果和翻译结果
    
    Args:
        original_result: 原始Whisper结果
        translated_result: LLM翻译结果
    """
    print("\n" + "="*80)
    print("📊 翻译结果对比")
    print("="*80)
    
    original_segments = original_result.get('segments', [])
    translated_segments = translated_result.get('segments', [])
    
    print(f"原始语音段数量: {len(original_segments)}")
    print(f"翻译语音段数量: {len(translated_segments)}")
    
    if len(original_segments) != len(translated_segments):
        print("⚠️  警告: 语音段数量不匹配！")
    
    print("\n📝 逐段对比:")
    print("-" * 80)
    
    for i, (orig, trans) in enumerate(zip(original_segments, translated_segments), 1):
        print(f"\n段落 {i:2d}:")
        print(f"  时间: [{orig['start']:6.1f}s - {orig['end']:6.1f}s]")
        print(f"  原文: {orig['text'].strip()}")
        print(f"  译文: {trans['text'].strip()}")
        
        # 检查时间戳是否一致
        if abs(orig['start'] - trans['start']) > 0.1 or abs(orig['end'] - trans['end']) > 0.1:
            print(f"  ⚠️  时间戳不匹配: 原始[{orig['start']:.1f}-{orig['end']:.1f}] vs 翻译[{trans['start']:.1f}-{trans['end']:.1f}]")
        
        # 只显示前10个段落，避免输出过长
        if i >= 10:
            remaining = len(original_segments) - 10
            if remaining > 0:
                print(f"\n... 还有 {remaining} 个段落未显示")
            break
    
    print("-" * 80)


def test_llm_translation(json_file_path: str):
    """
    测试LLM翻译功能
    
    Args:
        json_file_path: Whisper识别结果JSON文件路径
    """
    logger.info("=" * 60)
    logger.info("🧪 开始测试 LLM 翻译")
    logger.info("=" * 60)
    
    try:
        # 检查输入文件
        input_path = Path(json_file_path)
        if not input_path.exists():
            logger.error(f"JSON文件不存在: {json_file_path}")
            return False
        
        logger.info(f"📁 输入文件: {input_path.name}")
        logger.info(f"📏 文件大小: {input_path.stat().st_size / 1024:.2f} KB")
        
        # 加载Whisper识别结果
        logger.info("\n📥 步骤1: 加载Whisper识别结果")
        logger.info("-" * 40)
        
        whisper_result = load_whisper_result(json_file_path)
        if not whisper_result:
            logger.error("加载Whisper结果失败")
            return False
        
        segments_count = len(whisper_result.get('segments', []))
        logger.info(f"✅ 成功加载 {segments_count} 个语音段")
        
        # 显示原始内容预览
        logger.info("\n📄 原始内容预览:")
        logger.info("-" * 40)
        
        for i, segment in enumerate(whisper_result['segments'][:3], 1):  # 只显示前3个
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text'].strip()
            print(f"段落 {i}: [{start_time:6.1f}s - {end_time:6.1f}s] {text}")
        
        if segments_count > 3:
            print(f"... 还有 {segments_count - 3} 个语音段")
        
        # LLM翻译
        logger.info(f"\n🧠 步骤2: LLM翻译 (模型: {DEFAULT_LLM_MODEL})")
        logger.info("-" * 40)
        
        llm_success, translated_result, llm_error_code, llm_error_detail = LLM_translation(
            DEFAULT_LLM_MODEL, whisper_result
        )
        
        if not llm_success:
            logger.error(f"LLM翻译失败: {llm_error_detail}")
            logger.error(f"错误代码: {llm_error_code}")
            return False
        
        logger.info(f"✅ LLM翻译成功")
        logger.info(f"📝 翻译了 {len(translated_result['segments'])} 个语音段")
        
        # 显示翻译结果预览
        logger.info("\n📄 翻译结果预览:")
        logger.info("-" * 40)
        
        for i, segment in enumerate(translated_result['segments'][:3], 1):  # 只显示前3个
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text'].strip()
            print(f"段落 {i}: [{start_time:6.1f}s - {end_time:6.1f}s] {text}")
        
        # 保存翻译结果到JSON文件
        output_file = OUTPUT_DIR / "LLM_translation_output.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(translated_result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n💾 翻译结果已保存到: {output_file}")
        
        # 打印完整的翻译结果
        print("\n" + "="*60)
        print("📋 完整翻译结果 (JSON格式)")
        print("="*60)
        print(json.dumps(translated_result, ensure_ascii=False, indent=2))
        print("="*60)
        
        # 对比原始结果和翻译结果
        compare_results(whisper_result, translated_result)
        
        logger.info("🎉 LLM翻译测试完成")
        return True
        
    except Exception as e:
        logger.exception(f"测试过程异常: {str(e)}")
        return False


def main():
    """主函数"""
    print("🧪 LLM翻译测试工具")
    print("="*50)
    
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("使用方法: python test_LLM_translation.py <json_file_path>")
        print("示例: python test_LLM_translation.py ../output/whisper_detection_output.json")
        print("提示: 请先运行 test_whisper_detection.py 生成输入文件")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    
    # 如果是相对路径，转换为绝对路径
    if not Path(json_file_path).is_absolute():
        json_file_path = str(PROJECT_ROOT / json_file_path)
    
    # 执行测试
    success = test_llm_translation(json_file_path)
    
    if success:
        print("\n✅ 测试成功完成！")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
