from openai import OpenAI

client = OpenAI(
    base_url="https://api.uniapi.vip/v1", 
    api_key="sk-6e7hQ3zBKFK8cQR_sE6231Vqkbk9ChDrar4W9SRX3RWgiKqrQ0kXxuxKiMQ" 
)

with open("audio.m4a", "rb") as audio_file:
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",  # 关键参数：启用详细JSON输出（包含时间戳）
        language="en"  # 可选：指定音频语言（如英语"en"、中文"zh"），提升转录精度
    )

# 输出结果解析（段落级时间戳在 response.segments 中）
print("完整转录文本：", response.text, "\n")
print("段落级时间戳：")
for segment in response.segments:
    # segment 包含：id（段落ID）、start（开始时间）、end（结束时间）、text（段落文本）
    print(f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")