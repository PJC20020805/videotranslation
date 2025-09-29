#!/usr/bin/env python3
"""
视频翻译系统核心模块
包含音频分离、语音识别、LLM翻译、字幕生成和视频处理功能
"""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import re

from openai import OpenAI

from config import (
    PROJECT_ROOT, CACHE_DIR, OUTPUT_DIR, ERROR_CODES,
    WHISPER_API_KEY, WHISPER_BASE_URL, WHISPER_MODEL,
    DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, DEFAULT_LLM_MODEL,
    LLM_TEMPERATURE, DEFAULT_SUBTITLE_STYLE, MAX_AUDIO_DURATION
)
from logger import logger, log_function_call


def load_prompt_from_txt(prompt_file_path: str) -> str:
    """从txt文件加载prompt内容"""
    try:
        prompt_path = PROJECT_ROOT / prompt_file_path
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"加载prompt文件失败: {prompt_file_path} - {str(e)}")
        return ""


@log_function_call
def separate_wav(mp4_file_path: str) -> Tuple[bool, Optional[str], Optional[float], str, str]:
    """
    从MP4视频中分离音轨并转换为WAV格式
    
    Args:
        mp4_file_path: MP4文件路径
        
    Returns:
        Tuple[bool, Optional[str], Optional[float], str, str]:
        - is_success: 是否成功分离
        - audio_path: WAV文件路径（存储在CACHE_DIR）
        - audio_duration: 音频时长（秒）
        - error_code: 错误码
        - error_detail: 错误详情
    """
    try:
        # 检查输入文件
        input_path = Path(mp4_file_path)
        if not input_path.exists():
            error_msg = f"输入文件不存在: {mp4_file_path}"
            logger.error(error_msg)
            return False, None, None, ERROR_CODES["FILE_ERROR"], error_msg
        
        if not input_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']:
            error_msg = f"不支持的视频格式: {input_path.suffix}"
            logger.error(error_msg)
            return False, None, None, ERROR_CODES["FILE_ERROR"], error_msg
        
        # 生成输出文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f"audio_{timestamp}.wav"
        audio_path = CACHE_DIR / audio_filename
        
        logger.info(f"开始音频分离: {mp4_file_path} -> {audio_path}")
        
        # 检查ffmpeg是否可用
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            error_msg = "FFmpeg未安装或不在PATH中"
            logger.error(error_msg)
            return False, None, None, ERROR_CODES["DEPENDENCY_MISSING"], error_msg
        
        # 构建ffmpeg命令
        # -i: 输入文件
        # -vn: 不处理视频流
        # -acodec pcm_s16le: 使用PCM 16位编码
        # -ar 16000: 采样率16kHz
        # -ac 1: 单声道
        # -y: 覆盖输出文件
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-vn",  # 不处理视频
            "-acodec", "pcm_s16le",  # PCM 16位编码
            "-ar", "16000",  # 16kHz采样率
            "-ac", "1",  # 单声道
            "-y",  # 覆盖输出文件
            str(audio_path)
        ]
        
        # 执行ffmpeg命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode != 0:
            error_msg = f"FFmpeg执行失败: {result.stderr}"
            logger.error(error_msg)
            return False, None, None, ERROR_CODES["AUDIO_EXTRACT_FAILED"], error_msg
        
        # 检查输出文件是否生成
        if not audio_path.exists():
            error_msg = "音频文件未生成"
            logger.error(error_msg)
            return False, None, None, ERROR_CODES["AUDIO_EXTRACT_FAILED"], error_msg
        
        # 获取音频时长
        try:
            duration_cmd = [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(audio_path)
            ]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            audio_duration = float(duration_result.stdout.strip())
            
            # 检查音频时长限制
            if audio_duration > MAX_AUDIO_DURATION:
                error_msg = f"音频时长超过限制: {audio_duration:.2f}秒 > {MAX_AUDIO_DURATION}秒"
                logger.error(error_msg)
                # 清理文件
                audio_path.unlink(missing_ok=True)
                return False, None, None, ERROR_CODES["RESOURCE_LIMIT_ERROR"], error_msg
            
        except (subprocess.CalledProcessError, ValueError) as e:
            logger.warning(f"获取音频时长失败: {str(e)}")
            audio_duration = None
        
        logger.log_audio_extraction(str(input_path), True, audio_duration)
        return True, str(audio_path), audio_duration, ERROR_CODES["SUCCESS"], ""
        
    except subprocess.TimeoutExpired:
        error_msg = "音频分离超时"
        logger.error(error_msg)
        return False, None, None, ERROR_CODES["AUDIO_EXTRACT_FAILED"], error_msg
    except Exception as e:
        error_msg = f"音频分离异常: {str(e)}"
        logger.exception(error_msg)
        return False, None, None, ERROR_CODES["AUDIO_EXTRACT_FAILED"], error_msg


@log_function_call
def whisper_detection(audio_file_path: str, return_format: str = "json") -> Tuple[bool, Optional[Dict], str, str]:
    """
    使用Whisper API进行语音识别
    
    Args:
        audio_file_path: WAV音频文件路径
        return_format: 返回格式（默认json）
        
    Returns:
        Tuple[bool, Optional[Dict], str, str]:
        - is_success: 是否成功识别
        - recognition_result: 识别结果（Whisper格式的JSON字典）
        - error_code: 错误码
        - error_detail: 错误详情
    """
    try:
        # 检查输入文件
        audio_path = Path(audio_file_path)
        if not audio_path.exists():
            error_msg = f"音频文件不存在: {audio_file_path}"
            logger.error(error_msg)
            return False, None, ERROR_CODES["FILE_ERROR"], error_msg
        
        logger.info(f"开始语音识别: {audio_file_path}")
        
        # 初始化Whisper客户端
        client = OpenAI(
            base_url=WHISPER_BASE_URL,
            api_key=WHISPER_API_KEY
        )
        
        # 调用Whisper API
        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=WHISPER_MODEL,
                file=audio_file,
                response_format="verbose_json",  # 启用详细JSON输出（包含时间戳）
                language="en"  # 自动检测语言
            )
        
        # 处理响应为字典格式
        response_dict = response.model_dump()
        
        # 检查响应是否有效
        if not response_dict or "segments" not in response_dict:
            error_msg = "Whisper API返回无效响应"
            logger.error(error_msg)
            return False, None, ERROR_CODES["WHISPER_API_ERROR"], error_msg
        
        # 精简结果
        simplified = {
            "segments": []
        }
        
        # 处理每个片段，保留必要字段并简化时间戳
        for segment in response_dict.get("segments", []):
            simplified_segment = {
                "start": round(segment.get("start", 0.0), 1),  # 保留一位小数
                "end": round(segment.get("end", 0.0), 1),
                "text": segment.get("text", "").strip()  # 去除首尾空格
            }
            simplified["segments"].append(simplified_segment)
        
        # 检查是否识别到内容
        if not simplified["segments"]:
            error_msg = "未识别到任何语音内容"
            logger.warning(error_msg)
            return False, None, ERROR_CODES["AUDIO_EMPTY_ERROR"], error_msg
        
        segments_count = len(simplified["segments"])
        logger.log_whisper_recognition(audio_file_path, True, segments_count)
        
        return True, simplified, ERROR_CODES["SUCCESS"], ""
        
    except Exception as e:
        error_msg = f"Whisper识别异常: {str(e)}"
        logger.exception(error_msg)
        
        # 判断错误类型
        if "timeout" in str(e).lower():
            return False, None, ERROR_CODES["WHISPER_TIMEOUT_ERROR"], error_msg
        elif "api" in str(e).lower() or "network" in str(e).lower():
            return False, None, ERROR_CODES["WHISPER_API_ERROR"], error_msg
        else:
            return False, None, ERROR_CODES["WHISPER_MODEL_LOAD_FAILED"], error_msg


def validate_llm_output(input_segments: list, output_segments: list) -> bool:
    """
    验证LLM输出格式是否正确
    
    Args:
        input_segments: 输入的segments列表
        output_segments: LLM输出的segments列表
        
    Returns:
        bool: 是否通过验证
    """
    try:
        # 检查基本结构
        if not isinstance(output_segments, list):
            logger.error("LLM输出不是列表格式")
            return False
        
        # 检查长度是否一致
        if len(input_segments) != len(output_segments):
            logger.error(f"LLM输出长度不匹配: 输入{len(input_segments)}个，输出{len(output_segments)}个")
            return False
        
        # 检查每个segment的格式
        for i, (input_seg, output_seg) in enumerate(zip(input_segments, output_segments)):
            if not isinstance(output_seg, dict):
                logger.error(f"第{i+1}个segment不是字典格式")
                return False
            
            # 检查必要字段
            required_fields = ["start", "end", "text"]
            for field in required_fields:
                if field not in output_seg:
                    logger.error(f"第{i+1}个segment缺少字段: {field}")
                    return False
            
            # 检查时间戳是否一致
            if abs(input_seg["start"] - output_seg["start"]) > 0.1:
                logger.error(f"第{i+1}个segment开始时间不匹配: {input_seg['start']} vs {output_seg['start']}")
                return False
            
            if abs(input_seg["end"] - output_seg["end"]) > 0.1:
                logger.error(f"第{i+1}个segment结束时间不匹配: {input_seg['end']} vs {output_seg['end']}")
                return False
            
            # 检查文本是否为空
            if not output_seg["text"] or not output_seg["text"].strip():
                logger.error(f"第{i+1}个segment文本为空")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"LLM输出验证异常: {str(e)}")
        return False


@log_function_call
def LLM_translation(llm_model: str = DEFAULT_LLM_MODEL, whisper_result: Dict = None) -> Tuple[bool, Optional[Dict], str, str]:
    """
    使用LLM对Whisper识别结果进行中文翻译
    
    Args:
        llm_model: LLM模型名称
        whisper_result: Whisper识别结果
        
    Returns:
        Tuple[bool, Optional[Dict], str, str]:
        - is_success: 是否成功翻译
        - translated_result: 翻译结果
        - error_code: 错误码
        - error_detail: 错误详情
    """
    try:
        # 检查输入参数
        if not whisper_result or "segments" not in whisper_result:
            error_msg = "输入的Whisper结果无效"
            logger.error(error_msg)
            return False, None, ERROR_CODES["INVALID_INPUT_ERROR"], error_msg
        
        segments = whisper_result["segments"]
        if not segments:
            error_msg = "没有可翻译的语音段"
            logger.error(error_msg)
            return False, None, ERROR_CODES["SUBTITLE_EMPTY_ERROR"], error_msg
        
        logger.info(f"开始LLM翻译: 模型={llm_model}, 语音段数量={len(segments)}")
        
        # 加载系统提示词
        system_prompt = load_prompt_from_txt("LLM_prompt/toCN_prompt.txt")
        if not system_prompt:
            error_msg = "无法加载系统提示词"
            logger.error(error_msg)
            return False, None, ERROR_CODES["FILE_ERROR"], error_msg
        
        # 构建用户输入 - 将segments转换为字符串格式
        user_prompt_segments = []
        for segment in segments:
            segment_str = f'{{\n    "start": {segment["start"]},\n    "end": {segment["end"]},\n    "text": "{segment["text"]}"\n}}'
            user_prompt_segments.append(segment_str)
        
        user_prompt = ",\n".join(user_prompt_segments)
        
        # 初始化LLM客户端
        client = OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url=DASHSCOPE_BASE_URL,
        )
        
        # 调用LLM API
        completion = client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=LLM_TEMPERATURE
        )
        
        # 获取LLM响应
        llm_response = completion.choices[0].message.content
        
        if not llm_response:
            error_msg = "LLM返回空响应"
            logger.error(error_msg)
            return False, None, ERROR_CODES["LLM_API_ERROR"], error_msg
        
        logger.debug(f"LLM原始响应: {llm_response}")
        
        # 解析LLM响应 - 提取JSON格式的segments
        try:
            # 尝试直接解析为JSON
            if llm_response.strip().startswith('[') and llm_response.strip().endswith(']'):
                translated_segments = json.loads(llm_response)
            else:
                # 使用正则表达式提取JSON格式的segments
                json_pattern = r'\{[^{}]*"start"[^{}]*"end"[^{}]*"text"[^{}]*\}'
                matches = re.findall(json_pattern, llm_response, re.DOTALL)
                
                if not matches:
                    error_msg = f"无法从LLM响应中提取有效的JSON格式: {llm_response[:200]}..."
                    logger.error(error_msg)
                    return False, None, ERROR_CODES["LLM_ERROR"], error_msg
                
                # 解析每个匹配的JSON
                translated_segments = []
                for match in matches:
                    try:
                        segment = json.loads(match)
                        translated_segments.append(segment)
                    except json.JSONDecodeError:
                        logger.warning(f"跳过无效的JSON片段: {match}")
                        continue
            
        except json.JSONDecodeError as e:
            error_msg = f"LLM响应JSON解析失败: {str(e)}"
            logger.error(error_msg)
            return False, None, ERROR_CODES["LLM_ERROR"], error_msg
        
        # 验证LLM输出格式
        if not validate_llm_output(segments, translated_segments):
            error_msg = "LLM输出格式验证失败"
            logger.error(error_msg)
            return False, None, ERROR_CODES["LLM_ERROR"], error_msg
        
        # 构建最终结果
        translated_result = {
            "segments": translated_segments
        }
        
        segments_count = len(translated_segments)
        logger.log_llm_translation(llm_model, True, segments_count)
        
        return True, translated_result, ERROR_CODES["SUCCESS"], ""
        
    except Exception as e:
        error_msg = f"LLM翻译异常: {str(e)}"
        logger.exception(error_msg)
        
        # 判断错误类型
        if "timeout" in str(e).lower():
            return False, None, ERROR_CODES["LLM_TIMEOUT_ERROR"], error_msg
        elif "api" in str(e).lower() or "network" in str(e).lower():
            return False, None, ERROR_CODES["LLM_API_ERROR"], error_msg
        else:
            return False, None, ERROR_CODES["LLM_ERROR"], error_msg


@log_function_call
def srt_subtitle_handling(translated_json: Dict, srt_save_dir: str = None) -> Tuple[bool, Optional[str], str, str]:
    """
    将翻译后的JSON结果转换为SRT字幕文件
    
    Args:
        translated_json: LLM翻译后的JSON结果
        srt_save_dir: SRT文件保存目录（默认OUTPUT_DIR）
        
    Returns:
        Tuple[bool, Optional[str], str, str]:
        - is_success: 是否成功生成SRT
        - srt_save_path: SRT文件路径
        - error_code: 错误码
        - error_detail: 错误详情
    """
    try:
        # 检查输入参数
        if not translated_json or "segments" not in translated_json:
            error_msg = "输入的翻译结果无效"
            logger.error(error_msg)
            return False, None, ERROR_CODES["INVALID_INPUT_ERROR"], error_msg
        
        segments = translated_json["segments"]
        if not segments:
            error_msg = "没有可生成的字幕段"
            logger.error(error_msg)
            return False, None, ERROR_CODES["SUBTITLE_EMPTY_ERROR"], error_msg
        
        # 设置保存目录
        if srt_save_dir is None:
            save_dir = OUTPUT_DIR / "subtitles"
        else:
            save_dir = Path(srt_save_dir)
        
        # 确保目录存在
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成SRT文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        srt_filename = f"subtitle_{timestamp}.srt"
        srt_path = save_dir / srt_filename
        
        logger.info(f"开始生成SRT字幕: {len(segments)}个字幕段 -> {srt_path}")
        
        # 生成SRT内容
        srt_content = []
        for i, segment in enumerate(segments, 1):
            # 检查segment格式
            if not all(key in segment for key in ["start", "end", "text"]):
                logger.warning(f"跳过格式不正确的字幕段 {i}: {segment}")
                continue
            
            # 转换时间格式 (秒 -> SRT时间格式)
            start_time = seconds_to_srt_time(segment["start"])
            end_time = seconds_to_srt_time(segment["end"])
            text = segment["text"].strip()
            
            if not text:
                logger.warning(f"跳过空文本的字幕段 {i}")
                continue
            
            # SRT格式: 序号 + 时间范围 + 文本 + 空行
            srt_block = f"{i}\n{start_time} --> {end_time}\n{text}\n"
            srt_content.append(srt_block)
        
        if not srt_content:
            error_msg = "没有有效的字幕内容可生成"
            logger.error(error_msg)
            return False, None, ERROR_CODES["SUBTITLE_EMPTY_ERROR"], error_msg
        
        # 写入SRT文件
        try:
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(srt_content))
            
            logger.log_subtitle_generation(str(srt_path), True, len(srt_content))
            return True, str(srt_path), ERROR_CODES["SUCCESS"], ""
            
        except IOError as e:
            error_msg = f"SRT文件写入失败: {str(e)}"
            logger.error(error_msg)
            return False, None, ERROR_CODES["SRT_SAVE_FAILED"], error_msg
        
    except Exception as e:
        error_msg = f"SRT字幕生成异常: {str(e)}"
        logger.exception(error_msg)
        return False, None, ERROR_CODES["SUBTITLE_EXTRACT_FAILED"], error_msg


def seconds_to_srt_time(seconds: float) -> str:
    """
    将秒数转换为SRT时间格式 (HH:MM:SS,mmm)
    
    Args:
        seconds: 秒数
        
    Returns:
        str: SRT时间格式字符串
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


@log_function_call
def video_hardburn(
    input_video_path: str,
    srt_file_path: str,
    output_video_dir: str = None,
    output_video_name: str = None,
    subtitle_style: Dict = None
) -> Tuple[bool, Optional[str], Optional[str], str, str]:
    """
    使用FFmpeg将SRT字幕硬烧录到视频中
    
    Args:
        input_video_path: 原始MP4视频路径
        srt_file_path: SRT字幕文件路径
        output_video_dir: 输出视频保存目录
        output_video_name: 输出视频文件名（不含后缀）
        subtitle_style: 字幕样式配置
        
    Returns:
        Tuple[bool, Optional[str], Optional[str], str, str]:
        - is_success: 硬烧录是否成功
        - output_video_path: 输出视频路径
        - video_resolution: 视频分辨率
        - error_code: 错误码
        - error_detail: 错误详情
    """
    try:
        # 检查输入文件
        input_path = Path(input_video_path)
        srt_path = Path(srt_file_path)
        
        if not input_path.exists():
            error_msg = f"输入视频文件不存在: {input_video_path}"
            logger.error(error_msg)
            return False, None, None, ERROR_CODES["FILE_ERROR"], error_msg
        
        if not srt_path.exists():
            error_msg = f"SRT字幕文件不存在: {srt_file_path}"
            logger.error(error_msg)
            return False, None, None, ERROR_CODES["FILE_ERROR"], error_msg
        
        # 设置输出目录
        if output_video_dir is None:
            output_dir = OUTPUT_DIR / "videos"
        else:
            output_dir = Path(output_video_dir)
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成输出文件名
        if output_video_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_video_name = f"video_with_subtitles_{timestamp}"
        
        output_path = output_dir / f"{output_video_name}.mp4"
        
        logger.info(f"开始视频硬烧录: {input_video_path} + {srt_file_path} -> {output_path}")
        
        # 检查ffmpeg是否可用
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            error_msg = "FFmpeg未安装或不在PATH中"
            logger.error(error_msg)
            return False, None, None, ERROR_CODES["DEPENDENCY_MISSING"], error_msg
        
        # 获取原视频分辨率
        try:
            probe_cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                str(input_path)
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            probe_data = json.loads(probe_result.stdout)
            
            video_stream = None
            for stream in probe_data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break
            
            if video_stream:
                width = video_stream.get("width", 1920)
                height = video_stream.get("height", 1080)
                video_resolution = f"{width}x{height}"
            else:
                video_resolution = "1920x1080"  # 默认分辨率
                
        except Exception as e:
            logger.warning(f"获取视频分辨率失败: {str(e)}")
            video_resolution = "1920x1080"
        
        # 设置字幕样式
        if subtitle_style is None:
            subtitle_style = DEFAULT_SUBTITLE_STYLE.copy()
        
        # 构建字幕滤镜参数
        subtitle_filter = f"subtitles='{srt_path}':force_style='FontSize={subtitle_style['font_size']},PrimaryColour=&H{color_to_hex(subtitle_style['font_color'])},OutlineColour=&H{color_to_hex(subtitle_style['outline_color'])},Outline={subtitle_style['outline_width']}'"
        
        # 构建ffmpeg命令
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-vf", subtitle_filter,
            "-c:a", "copy",  # 音频流直接复制
            "-c:v", "libx264",  # 视频重新编码
            "-preset", "medium",  # 编码预设
            "-crf", "23",  # 质量控制
            "-y",  # 覆盖输出文件
            str(output_path)
        ]
        
        # 执行ffmpeg命令
        logger.debug(f"执行FFmpeg命令: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )
        
        if result.returncode != 0:
            error_msg = f"FFmpeg硬烧录失败: {result.stderr}"
            logger.error(error_msg)
            return False, None, None, ERROR_CODES["FFMPEG_ERROR"], error_msg
        
        # 检查输出文件是否生成
        if not output_path.exists():
            error_msg = "输出视频文件未生成"
            logger.error(error_msg)
            return False, None, None, ERROR_CODES["VIDEO_ENCODE_FAILED"], error_msg
        
        logger.log_video_processing(str(input_path), str(output_path), True, "hard_burned")
        return True, str(output_path), video_resolution, ERROR_CODES["SUCCESS"], ""
        
    except subprocess.TimeoutExpired:
        error_msg = "视频硬烧录超时"
        logger.error(error_msg)
        return False, None, None, ERROR_CODES["FFMPEG_ERROR"], error_msg
    except PermissionError:
        error_msg = f"输出目录权限不足: {output_dir}"
        logger.error(error_msg)
        return False, None, None, ERROR_CODES["PERMISSION_DENIED"], error_msg
    except Exception as e:
        error_msg = f"视频硬烧录异常: {str(e)}"
        logger.exception(error_msg)
        return False, None, None, ERROR_CODES["FFMPEG_ERROR"], error_msg


def color_to_hex(color_name: str) -> str:
    """
    将颜色名称转换为十六进制格式（用于FFmpeg）
    
    Args:
        color_name: 颜色名称
        
    Returns:
        str: 十六进制颜色代码
    """
    color_map = {
        "white": "FFFFFF",
        "black": "000000",
        "red": "FF0000",
        "green": "00FF00",
        "blue": "0000FF",
        "yellow": "FFFF00",
        "cyan": "00FFFF",
        "magenta": "FF00FF"
    }
    
    return color_map.get(color_name.lower(), "FFFFFF")


def cleanup_cache_files():
    """清理缓存目录中的临时文件"""
    try:
        logger.info("开始清理缓存文件...")
        
        cleaned_files = 0
        total_size = 0
        
        for file_path in CACHE_DIR.glob("*"):
            if file_path.is_file():
                file_size = file_path.stat().st_size
                total_size += file_size
                file_path.unlink()
                cleaned_files += 1
                logger.debug(f"删除缓存文件: {file_path}")
        
        total_size_mb = total_size / (1024 * 1024)
        logger.info(f"缓存清理完成: 清理了 {cleaned_files} 个文件，释放 {total_size_mb:.2f}MB 空间")
        
    except Exception as e:
        logger.error(f"缓存清理失败: {str(e)}")


class VideoTranslation:
    """
    视频翻译主类
    整合音频分离、语音识别、LLM翻译、字幕生成和视频处理功能
    """
    
    def __init__(self):
        """初始化视频翻译器"""
        self.logger = logger
        self.logger.info("VideoTranslation 初始化完成")
    
    @log_function_call
    def translation(self, mp4_file_path: str, output_mode: str = "soft_subtitle") -> Dict[str, Any]:
        """
        视频翻译主函数
        
        Args:
            mp4_file_path: MP4文件路径
            output_mode: 输出模式 ("soft_subtitle" 或 "hard_burned")
            
        Returns:
            Dict: 处理结果JSON
        """
        start_time = time.time()
        
        # 初始化结果字典
        result = {
            # 通用基础信息
            "success": False,
            "message": "",
            "processingTime": 0.0,
            "inputFile": mp4_file_path,
            
            # 音频处理相关
            "audioExtracted": False,
            "audioDuration": None,
            "whisperHandled": False,
            
            # 字幕相关
            "subtitleExtracted": False,
            "subtitleLanguage": {
                "source": "auto",
                "target": "zh-CN"
            },
            
            # 输出视频相关
            "outputMode": output_mode
        }
        
        try:
            self.logger.info(f"开始视频翻译任务: {mp4_file_path} (模式: {output_mode})")
            
            # 验证输出模式
            if output_mode not in ["soft_subtitle", "hard_burned"]:
                result["message"] = f"不支持的输出模式: {output_mode}"
                result["errorCode"] = ERROR_CODES["INVALID_INPUT_ERROR"]
                result["errorDetails"] = result["message"]
                return result
            
            # 步骤1: 音频分离
            self.logger.info("步骤1: 开始音频分离...")
            audio_success, audio_path, audio_duration, audio_error_code, audio_error_detail = separate_wav(mp4_file_path)
            
            result["audioExtracted"] = audio_success
            result["audioDuration"] = audio_duration
            
            if not audio_success:
                result["message"] = f"音频分离失败: {audio_error_detail}"
                result["errorCode"] = audio_error_code
                result["errorDetails"] = audio_error_detail
                return result
            
            # 步骤2: 语音识别
            self.logger.info("步骤2: 开始语音识别...")
            whisper_success, whisper_result, whisper_error_code, whisper_error_detail = whisper_detection(audio_path)
            
            result["whisperHandled"] = whisper_success
            
            if not whisper_success:
                result["message"] = f"语音识别失败: {whisper_error_detail}"
                result["errorCode"] = whisper_error_code
                result["errorDetails"] = whisper_error_detail
                return result
            
            # 步骤3: LLM翻译
            self.logger.info("步骤3: 开始LLM翻译...")
            llm_success, translated_result, llm_error_code, llm_error_detail = LLM_translation(
                DEFAULT_LLM_MODEL, whisper_result
            )
            
            if not llm_success:
                result["message"] = f"LLM翻译失败: {llm_error_detail}"
                result["errorCode"] = llm_error_code
                result["errorDetails"] = llm_error_detail
                return result
            
            # 步骤4: 生成SRT字幕
            self.logger.info("步骤4: 开始生成SRT字幕...")
            srt_success, srt_path, srt_error_code, srt_error_detail = srt_subtitle_handling(translated_result)
            
            result["subtitleExtracted"] = srt_success
            
            if not srt_success:
                result["message"] = f"字幕生成失败: {srt_error_detail}"
                result["errorCode"] = srt_error_code
                result["errorDetails"] = srt_error_detail
                return result
            
            # 软嵌入模式：到此结束
            if output_mode == "soft_subtitle":
                result["translatedSubtitlePath"] = srt_path
                result["success"] = True
                result["message"] = "翻译成功"
                
                self.logger.info(f"软嵌入模式完成: {srt_path}")
            
            # 硬烧录模式：继续处理视频
            elif output_mode == "hard_burned":
                self.logger.info("步骤5: 开始视频硬烧录...")
                
                video_success, output_video_path, video_resolution, video_error_code, video_error_detail = video_hardburn(
                    mp4_file_path, srt_path
                )
                
                if not video_success:
                    result["message"] = f"视频硬烧录失败: {video_error_detail}"
                    result["errorCode"] = video_error_code
                    result["errorDetails"] = video_error_detail
                    return result
                
                result["outputVideoPath"] = output_video_path
                result["videoResolution"] = video_resolution
                result["success"] = True
                result["message"] = "翻译成功"
                
                self.logger.info(f"硬烧录模式完成: {output_video_path}")
            
            # 计算总处理时间
            end_time = time.time()
            processing_time = end_time - start_time
            result["processingTime"] = round(processing_time, 2)
            
            # 记录任务总结
            self.logger.log_task_summary(mp4_file_path, True, processing_time, output_mode)
            
            return result
            
        except Exception as e:
            # 处理未捕获的异常
            end_time = time.time()
            processing_time = end_time - start_time
            result["processingTime"] = round(processing_time, 2)
            
            error_msg = f"视频翻译异常: {str(e)}"
            result["message"] = error_msg
            result["errorCode"] = ERROR_CODES["CONCURRENCY_ERROR"]
            result["errorDetails"] = error_msg
            
            self.logger.exception(error_msg)
            self.logger.log_task_summary(mp4_file_path, False, processing_time, output_mode, error_msg)
            
            return result
            
        finally:
            # 清理缓存文件
            try:
                cleanup_cache_files()
            except Exception as e:
                self.logger.warning(f"缓存清理失败: {str(e)}")
    
    def get_supported_formats(self) -> Dict[str, list]:
        """
        获取支持的文件格式
        
        Returns:
            Dict: 支持的视频和音频格式
        """
        from config import SUPPORTED_VIDEO_FORMATS, SUPPORTED_AUDIO_FORMATS
        
        return {
            "video_formats": SUPPORTED_VIDEO_FORMATS,
            "audio_formats": SUPPORTED_AUDIO_FORMATS
        }
    
    def validate_input_file(self, file_path: str) -> Tuple[bool, str]:
        """
        验证输入文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            path = Path(file_path)
            
            # 检查文件是否存在
            if not path.exists():
                return False, f"文件不存在: {file_path}"
            
            # 检查文件格式
            from config import SUPPORTED_VIDEO_FORMATS
            if path.suffix.lower() not in SUPPORTED_VIDEO_FORMATS:
                return False, f"不支持的文件格式: {path.suffix}"
            
            # 检查文件大小
            from config import MAX_VIDEO_SIZE
            file_size = path.stat().st_size
            if file_size > MAX_VIDEO_SIZE:
                return False, f"文件过大: {file_size / (1024**3):.2f}GB > {MAX_VIDEO_SIZE / (1024**3):.2f}GB"
            
            return True, ""
            
        except Exception as e:
            return False, f"文件验证异常: {str(e)}"


if __name__ == "__main__":
    # 测试函数
    logger.info("视频翻译核心模块加载完成")
    
    # 创建翻译器实例进行简单测试
    translator = VideoTranslation()
    logger.info("VideoTranslation 实例创建成功")
