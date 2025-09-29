#!/usr/bin/env python3
"""
视频切片工具 - 用于测试
从video.mp4切出2分钟的测试视频
"""

import os
import sys
import subprocess
from pathlib import Path

def cut_video_for_test():
    """
    从video.mp4切出前2分钟的视频用于测试
    """
    # 项目根目录
    project_root = Path(__file__).parent.parent
    
    # 输入和输出路径
    input_video = project_root / "video.mp4"
    output_video = project_root / "video_test_2min.mp4"
    
    print(f"🎬 视频切片工具")
    print(f"📁 项目根目录: {project_root}")
    print(f"📹 输入视频: {input_video}")
    print(f"🎯 输出视频: {output_video}")
    
    # 检查输入文件是否存在
    if not input_video.exists():
        print(f"❌ 错误: 输入视频文件不存在: {input_video}")
        print(f"💡 请确保在项目根目录下有 video.mp4 文件")
        return False
    
    # 检查ffmpeg是否可用
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg 检测成功")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ 错误: FFmpeg 未安装或不在PATH中")
        print("💡 请先安装FFmpeg: sudo apt install ffmpeg")
        return False
    
    # 如果输出文件已存在，询问是否覆盖
    if output_video.exists():
        response = input(f"⚠️  输出文件已存在: {output_video.name}\n是否覆盖? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("🚫 操作已取消")
            return False
        
        # 删除现有文件
        output_video.unlink()
        print("🗑️  已删除现有文件")
    
    print("🔄 开始切片处理...")
    
    # 构建ffmpeg命令
    # -i: 输入文件
    # -t 120: 截取前120秒(2分钟)
    # -c copy: 直接复制流，不重新编码，保持原质量
    # -avoid_negative_ts make_zero: 避免负时间戳
    cmd = [
        "ffmpeg",
        "-i", str(input_video),
        "-t", "120",  # 2分钟 = 120秒
        "-c", "copy",  # 直接复制，保持原质量
        "-avoid_negative_ts", "make_zero",
        "-y",  # 覆盖输出文件
        str(output_video)
    ]
    
    try:
        # 执行ffmpeg命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # 检查输出文件
        if output_video.exists():
            file_size_mb = output_video.stat().st_size / (1024 * 1024)
            print(f"✅ 切片成功!")
            print(f"📁 输出文件: {output_video}")
            print(f"📊 文件大小: {file_size_mb:.1f} MB")
            
            # 获取视频信息
            try:
                probe_cmd = [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    str(output_video)
                ]
                probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
                import json
                video_info = json.loads(probe_result.stdout)
                
                # 提取视频流信息
                video_stream = next((s for s in video_info['streams'] if s['codec_type'] == 'video'), None)
                if video_stream:
                    duration = float(video_info['format']['duration'])
                    width = video_stream.get('width', 'N/A')
                    height = video_stream.get('height', 'N/A')
                    codec = video_stream.get('codec_name', 'N/A')
                    
                    print(f"⏱️  视频时长: {duration:.1f}秒")
                    print(f"📐 分辨率: {width}x{height}")
                    print(f"🎞️  编码格式: {codec}")
                
            except Exception as e:
                print(f"⚠️  无法获取视频详细信息: {e}")
            
            print(f"🎉 测试视频已准备就绪，可用于大量测试而不消耗过多token!")
            return True
        else:
            print("❌ 错误: 输出文件未生成")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg处理失败:")
        print(f"返回码: {e.returncode}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🎬 视频切片工具 - 测试用途")
    print("=" * 60)
    
    success = cut_video_for_test()
    
    print("=" * 60)
    if success:
        print("✅ 处理完成!")
    else:
        print("❌ 处理失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()
