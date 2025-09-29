#!/usr/bin/env python3
"""
硬烧录字幕测试脚本
测试将SRT字幕文件硬烧录到视频中
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from video_translator import video_hardburn
from logger import logger
from config import PROJECT_ROOT, OUTPUT_DIR


def test_hard_burned(video_path: str, srt_path: str):
    """
    测试硬烧录字幕功能
    
    Args:
        video_path: 视频文件路径
        srt_path: SRT字幕文件路径
    """
    logger.info("=" * 60)
    logger.info("🧪 开始测试硬烧录字幕")
    logger.info("=" * 60)
    
    try:
        # 检查输入文件
        video_file = Path(video_path)
        srt_file = Path(srt_path)
        
        if not video_file.exists():
            logger.error(f"视频文件不存在: {video_path}")
            return False
        
        if not srt_file.exists():
            logger.error(f"SRT字幕文件不存在: {srt_path}")
            return False
        
        logger.info(f"📁 输入视频: {video_file.name}")
        logger.info(f"📏 视频大小: {video_file.stat().st_size / (1024*1024):.2f} MB")
        logger.info(f"📄 字幕文件: {srt_file.name}")
        logger.info(f"📏 字幕大小: {srt_file.stat().st_size / 1024:.2f} KB")
        
        # 设置测试输出目录
        test_output_dir = PROJECT_ROOT / "test/test_output"
        test_output_dir.mkdir(exist_ok=True)
        
        logger.info(f"📂 输出目录: {test_output_dir}")
        
        # 执行硬烧录测试
        logger.info("\n🎬 开始硬烧录测试")
        logger.info("-" * 40)
        
        success, output_video_path, video_resolution, error_code, error_detail = video_hardburn(
            input_video_path=str(video_file),
            srt_file_path=str(srt_file),
            output_video_dir=str(test_output_dir),
            output_video_name=f"test_hardburned_{video_file.stem}",
            subtitle_style=None  # 使用默认样式（黑色字幕+白色轮廓）
        )
        
        if not success:
            logger.error(f"硬烧录失败: {error_detail}")
            logger.error(f"错误代码: {error_code}")
            return False
        
        logger.info(f"✅ 硬烧录成功")
        logger.info(f"🎬 输出视频: {Path(output_video_path).name}")
        logger.info(f"📐 视频分辨率: {video_resolution}")
        
        # 检查输出文件
        output_file = Path(output_video_path)
        if output_file.exists():
            output_size_mb = output_file.stat().st_size / (1024 * 1024)
            logger.info(f"📏 输出文件大小: {output_size_mb:.2f} MB")
            
            print(f"\n✅ 硬烧录测试成功！")
            print(f"📁 输出文件: {output_video_path}")
            print(f"📐 分辨率: {video_resolution}")
            print(f"📏 文件大小: {output_size_mb:.2f} MB")
        else:
            logger.error("输出文件不存在")
            return False
        
        # 显示字幕样式信息
        print(f"\n🎨 字幕样式:")
        print(f"   - 字体颜色: 黑色")
        print(f"   - 轮廓颜色: 白色")
        print(f"   - 字体大小: 55px")
        print(f"   - 轮廓宽度: 2px")
        
        logger.info("🎉 硬烧录测试完成")
        return True
        
    except Exception as e:
        logger.exception(f"测试过程异常: {str(e)}")
        return False


def main():
    """主函数"""
    print("🧪 硬烧录字幕测试工具")
    print("="*50)
    
    # 使用固定的测试文件
    video_path = str(PROJECT_ROOT / "video_test_2min.mp4")
    srt_path = str(PROJECT_ROOT / "output/subtitles/subtitle_20250929_110805.srt")
    
    # 检查文件是否存在
    if not Path(video_path).exists():
        print(f"❌ 测试视频文件不存在: {video_path}")
        sys.exit(1)
    
    if not Path(srt_path).exists():
        print(f"❌ SRT字幕文件不存在: {srt_path}")
        sys.exit(1)
    
    print(f"📁 测试视频: video_test_2min.mp4")
    print(f"📄 字幕文件: subtitle_20250929_110805.srt")
    
    # 执行测试
    success = test_hard_burned(video_path, srt_path)
    
    if success:
        print("\n✅ 测试成功完成！")
        print("💡 提示: 输出文件保存在 test_output/ 目录下")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
