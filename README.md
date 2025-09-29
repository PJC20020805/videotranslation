# 视频翻译系统

一个基于 Whisper + LLM 的智能视频翻译字幕系统，支持音轨分离、语音识别、智能翻译和字幕嵌入。

## 功能特性

- 🎵 **音轨分离**: 使用 FFmpeg 从 MP4 视频中提取高质量音频
- 🎤 **语音识别**: 基于 Whisper API 的精准语音转文字
- 🧠 **智能翻译**: 使用阿里云百炼大模型进行上下文相关的中文翻译
- 📝 **字幕生成**: 自动生成标准 SRT 字幕文件
- 🎬 **字幕嵌入**: 支持软嵌入和硬烧录两种模式
- ⚡ **异步处理**: 高效的异步 I/O 处理，适合长时间任务

## 系统架构

```
VideoTranslation 主类
├── separate_wav()          # 音轨分离 (MP4 → WAV numpy数组)
├── whisper_detection()     # 语音识别 (WAV → JSON with timestamps)
├── LLM_translation()       # 智能翻译 (English JSON → Chinese JSON)
├── srt_subtitle_handling() # 字幕生成 (JSON → SRT文件)
└── video_hardburn()        # 硬烧录 (MP4 + SRT → 新MP4)
```

## 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 FFmpeg (Ubuntu/Debian)
sudo apt update && sudo apt install ffmpeg

# 安装 FFmpeg (CentOS/RHEL)
sudo yum install ffmpeg
```

## 环境配置

```bash
# 设置阿里云百炼 API Key
export DASHSCOPE_API_KEY="your-dashscope-api-key"

# 验证环境变量
echo $DASHSCOPE_API_KEY
```

## 使用方法

### 命令行使用

```bash
# 软嵌入模式（生成 SRT 字幕文件）
python main.py video.mp4 soft_subtitle

# 硬烧录模式（字幕直接烧录到视频）
python main.py video.mp4 hard_burned

# 使用默认模式（软嵌入）
python main.py video.mp4
```

### 编程接口

```python
import asyncio
from video_translator import VideoTranslation

async def translate_video():
    translator = VideoTranslation()
    
    # 执行翻译
    result = await translator.translation(
        mp4_file_path="video.mp4",
        output_mode="soft_subtitle"  # 或 "hard_burned"
    )
    
    if result["success"]:
        print(f"翻译成功! 耗时: {result['processingTime']:.2f}秒")
        if result["outputMode"] == "soft_subtitle":
            print(f"字幕文件: {result['translatedSubtitlePath']}")
        else:
            print(f"输出视频: {result['outputVideoPath']}")
    else:
        print(f"翻译失败: {result['message']}")

# 运行
asyncio.run(translate_video())
```

## 输出格式

### 成功响应示例

```json
{
  "success": true,
  "message": "翻译成功",
  "processingTime": 45.67,
  "inputFile": "video.mp4",
  "audioExtracted": true,
  "audioDuration": 120.5,
  "whisperHandled": true,
  "subtitleExtracted": true,
  "subtitleLanguage": {
    "source": "auto",
    "target": "zh-CN"
  },
  "outputMode": "soft_subtitle",
  "translatedSubtitlePath": "/root/video-translation/output/subtitles/subtitle_20241228_143022.srt"
}
```

### 错误响应示例

```json
{
  "success": false,
  "message": "音轨分离失败",
  "processingTime": 2.34,
  "inputFile": "video.mp4",
  "audioExtracted": false,
  "whisperHandled": false,
  "subtitleExtracted": false,
  "errorCode": "AUDIO_EXTRACT_FAILED",
  "errorDetails": "FFmpeg错误: 文件格式不支持"
}
```

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| `SUCCESS` | 处理成功 |
| `AUDIO_EXTRACT_FAILED` | 音轨分离失败 |
| `WHISPER_MODEL_LOAD_FAILED` | Whisper 模型加载失败 |
| `LLM_API_KEY_MISSING` | LLM API 密钥缺失 |
| `SRT_SAVE_FAILED` | SRT 文件保存失败 |
| `FFMPEG_ERROR` | FFmpeg 处理错误 |
| `FILE_ERROR` | 文件读取错误 |
| `PERMISSION_DENIED` | 权限不足 |
| `NETWORK_ERROR` | 网络请求失败 |
| `API_ERROR` | API 调用失败 |
| `BIG_FILE_ERROR` | 文件过大（超过30分钟） |

## 限制说明

- **视频时长**: 最大支持 30 分钟的视频文件
- **音频格式**: 自动转换为 16kHz 单声道 WAV
- **字幕样式**: 硬烧录默认使用 55px 中文字体，底部居中
- **API 限制**: 受 Whisper 和阿里云百炼 API 的调用限制

## 开发和部署

### 开发环境

```bash
# 启动开发环境
./bin/develop.sh

# 运行测试
python test_example.py
```

### 生产环境

```bash
# 后台启动服务
./bin/server.sh video.mp4 soft_subtitle

# 查看日志
tail -f logs/video_translation_$(date +%Y%m%d).log
```

## 目录结构

```
video-translation/
├── main.py                 # 主程序入口
├── video_translator.py     # 核心翻译类
├── config.py              # 配置文件
├── requirements.txt       # 依赖包
├── test_example.py        # 测试示例
├── README.md             # 说明文档
├── bin/                  # 启动脚本
│   ├── develop.sh        # 开发环境
│   └── server.sh         # 生产环境
├── output/               # 输出目录
│   ├── audio/           # 临时音频文件
│   ├── subtitles/       # SRT 字幕文件
│   └── videos/          # 处理后的视频
└── logs/                # 日志文件
```

## 技术栈

- **音频处理**: FFmpeg, ffmpeg-python
- **语音识别**: OpenAI Whisper API
- **智能翻译**: 阿里云百炼 (Qwen-Plus)
- **异步处理**: asyncio, aiofiles
- **数据处理**: NumPy

## 注意事项

1. 确保系统已安装 FFmpeg
2. 设置正确的 API 密钥环境变量
3. 网络环境需要能访问相关 API 服务
4. 临时文件会在处理完成后自动清理
5. 大文件处理可能需要较长时间，请耐心等待
