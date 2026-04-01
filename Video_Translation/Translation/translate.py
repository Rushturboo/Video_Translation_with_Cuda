# 需先安装依赖：？
# pip install torch torchaudio transformers ffmpeg-python moviepy gtts pydub soundfile

#README
#本项目依赖ffgmeg，请在官网安装并将bin目录添加到环境变量Path中
#运行时需要科学上网，请准备好VPN
#需要将moviepy版本降级为1.0.3，否则会出现代码重构混用冲突

#https://www.geeksforgeeks.org/how-to-install-ffmpeg-on-windows/
#ffmpeg安装教程！！！！
from transformers import MarianMTModel, MarianTokenizer
from gtts import gTTS

# #读取文件用
# from pathlib import Path
# current_path = Path(__file__)  # 当前脚本所在目录（src）

#用户自主选择读取文件路径
import tkinter as tk
from tkinter import filedialog

output_audio_path = "translated_audio.mp3"
output_video_path = "translated_video.mp4"

video_path = "chushihua" # 初始化变量
audio_path = "audio.wav" # 提取出的音频文件路径
#video_path = "E:/Data Analyze/video-translation-master/Translation/testdata.mp4"
subtitle_path = "subtitles.srt"
def get_file_path():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    return file_path  # 读取视频文件路径

###################################### 提取音频（已测试无需修改）
import subprocess

def extract_audio(video_path, audio_path):
     command = f'ffmpeg -i "{video_path}" -q:a 0 -map a "{audio_path}" -y'
    # print("执行命令:", command)
     subprocess.run(command, shell=True)

#print("done")
###################################### 语音转文本（使用本地Whisper，第一次启动需要下载模型，约1G，已测试无需修改）
import whisper
import torch
transcribed_text = "" # 初始化变量
def format_time_for_text(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# def speech_to_text(audio_path):
#     device = "cuda" if torch.cuda.is_available() else "cpu"
#     print(f"✅ 使用设备: {device}")
#     print(f"🔍 正在加载 Whisper 模型...")
#     model = whisper.load_model("base", device=device)
#     print(f"🎙️ 正在转录文件: {audio_path}")
#     result = model.transcribe(audio_path, fp16=True)
#
#     original_segments = result["segments"]
#     full_segments = []
#     gap_threshold = 0.3  # 静音间隔阈值（秒）
#
#     for i, seg in enumerate(original_segments):
#         if i > 0:
#             prev = original_segments[i - 1]
#             gap = seg["start"] - prev["end"]
#             if gap >= gap_threshold:
#                 # 插入静音段
#                 full_segments.append({
#                     "start": prev["end"],
#                     "end": seg["start"],
#                     "text": "",
#                     "is_silence": True
#                 })
#         # 插入当前语音段
#         full_segments.append({
#             "start": seg["start"],
#             "end": seg["end"],
#             "text": seg["text"].strip(),
#             "is_silence": False
#         })
#
#     # 打印段落检查
#     for seg in full_segments:
#         start = format_time_for_text(seg["start"])
#         end = format_time_for_text(seg["end"])
#         label = "[Silence]" if seg["is_silence"] else ""
#         print(f"{label} [{start} - {end}] {seg['text']}")
#
#     return full_segments
def speech_to_text(audio_path):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model("base", device=device)
    result = model.transcribe(audio_path, fp16=True, word_timestamps=True)

    words_all = []
    for seg in result["segments"]:
        words_all.extend(seg.get("words", []))

    max_word_gap = 1.0
    min_silence_gap = 1.0

    merged_segments = []
    current_text = ""
    sentence_start = sentence_end = prev_end = None

    for word in words_all:
        word_text = word["word"].strip()
        word_start = word["start"]
        word_end = word["end"]

        if sentence_start is None:
            sentence_start = word_start
            current_text = word_text
        else:
            gap = word_start - prev_end
            if gap > max_word_gap:
                merged_segments.append({"start": sentence_start, "end": sentence_end, "text": current_text.strip(), "is_silence": False})
                if word_start - sentence_end > min_silence_gap:
                    merged_segments.append({"start": sentence_end, "end": word_start, "text": "", "is_silence": True})
                sentence_start = word_start
                current_text = word_text
            else:
                current_text += " " + word_text

        sentence_end = word_end
        prev_end = word_end

    if current_text:
        merged_segments.append({"start": sentence_start, "end": sentence_end, "text": current_text.strip(), "is_silence": False})

    return merged_segments


def write_to_file(segments):
    print(f"📝 正在写入文本到文件: transcribed_text.txt")
    with open("transcribed_text.txt", "w", encoding="utf-8") as file:
        file.write(segments)
    print("写入完成")

###################################### 翻译（使用MarianMT模型）(已测试无需修改)
def translate_segments(segments):
    model_name = "Helsinki-NLP/opus-mt-en-zh"
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)

    translated = []
    for seg in segments:
        if seg["is_silence"]:
            translated.append(seg)
            continue

        inputs = tokenizer([seg["text"]], return_tensors="pt", truncation=True, max_length=512)
        translated_tokens = model.generate(**inputs)
        translated_text = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
        translated.append({
            **seg,
            "text": translated_text,
            "original_text": seg["text"]
        })

    print("🌍 翻译完成")
    return translated

def write_to_file_1(translated_text):
    # 保存到文件
    print(f"📝 正在写入翻译文本到文件: full_translated_text.txt")
    with open("full_translated_text.txt", "w", encoding="utf-8") as file:
        file.write(translated_text)
    print("写入完成")
###################################### 文本转语音（已测试无需修改）
def text_to_speech(translated, output_audio_path):
    tts = gTTS(text=translated, lang="zh")
    tts.save(output_audio_path)
    with open("full_translated_text.txt", "r", encoding="utf-8") as file:
        full_translated_text = file.read()

#后端程序员如有时间请添加翻译后音频相对时间轴的缩放
###################################### 字幕生成 ################################
def format_time_srt(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')


def generate_subtitles(segments, subtitle_path):
    with open(subtitle_path, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n")
            f.write(f"{format_time_srt(seg['start'])} --> {format_time_srt(seg['end'])}\n")

            # 有原文就输出中英双语，否则只输出空白或翻译
            if seg.get("original_text"):
                f.write(f"{seg['original_text']}\n{seg['text']}\n\n")
            elif seg.get("text"):
                f.write(f"{seg['text']}\n\n")
            else:
                f.write("\n")


###################################### 语音合成与对齐 ##########################
from gtts import gTTS
from pydub import AudioSegment
import soundfile as sf
import wave


def create_atempo_filter(speed_factor):
    """创建变速滤镜链，限制变速范围在0.5x-2.0x之间"""
    # 限制变速范围在0.5到2.0之间，不然过于失真
    speed_factor = max(0.5, min(2.0, speed_factor))
    return f"atempo={speed_factor:.3f}"


def adjust_audio_duration(input_path, output_path, target_duration, sample_rate=44100):
    """使用FFmpeg精确调整音频时长，限制变速范围"""
    # 获取当前音频时长
    audio = AudioSegment.from_file(input_path)
    current_duration = len(audio) / 1000  # 转换为秒

    # 计算变速因子，并限制在0.5-2.0范围内
    speed_factor = current_duration / target_duration
    speed_factor = max(0.5, min(2.0, speed_factor))

    # 创建滤镜链
    filter_str = create_atempo_filter(speed_factor)

    # 构建FFmpeg命令
    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-af', filter_str,
        '-ar', str(sample_rate),
        output_path
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg处理失败: {e}")
        # 回退方案：直接复制文件
        audio.export(output_path, format='wav')
        return

    # 精确裁剪或填充
    audio = AudioSegment.from_wav(output_path)
    target_ms = int(target_duration * 1000)
    if len(audio) > target_ms:
        audio = audio[:target_ms]
    elif len(audio) < target_ms:
        silence = AudioSegment.silent(duration=target_ms - len(audio))
        audio = audio + silence

    audio.export(output_path, format='wav')
import os
# 创建临时文件目录
temp_dir = "temp_audio_files"
os.makedirs(temp_dir, exist_ok=True)


def process_audio_segments(segments, output_path):
    final_audio = AudioSegment.silent(duration=0)
    sample_rate = 44100

    try:
        for i, seg in enumerate(segments):
            target_duration = seg["end"] - seg["start"]

            if seg.get("is_silence", False) or seg["text"].strip() == "":
                silent_audio = AudioSegment.silent(duration=int(target_duration * 1000))
                final_audio += silent_audio
                print(f"➖ 插入静音段 [{seg['start']:.2f} - {seg['end']:.2f}]")
                continue

            tts_path = os.path.join(temp_dir, f"tts_{i}.mp3")
            raw_path = os.path.join(temp_dir, f"raw_{i}.wav")
            adjusted_path = os.path.join(temp_dir, f"adjusted_{i}.wav")

            tts = gTTS(seg["text"], lang='zh')
            tts.save(tts_path)

            audio = AudioSegment.from_mp3(tts_path)
            audio.set_frame_rate(sample_rate).set_channels(1).export(raw_path, format='wav')

            adjust_audio_duration(raw_path, adjusted_path, target_duration)

            final_audio += AudioSegment.from_wav(adjusted_path)

            os.remove(tts_path)
            os.remove(raw_path)
            os.remove(adjusted_path)

        final_audio.export(output_path, format='wav')
        print(f"🔊 合成音频已保存至：{output_path}")

    except Exception as e:
        print(f"❌ 音频处理出错: {str(e)}")
        raise



###################################### 合成新视频（已测试无需修改）（如有时间可构建此功能）（需要将moviepy版本降级为1.0.3，否则会出现代码重构混用冲突）
from moviepy.editor import VideoFileClip,AudioFileClip,CompositeVideoClip


def add_audio_to_video(video_path, audio_path,subtitle_path,output_video_path):
    """合成最终视频"""
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-i', audio_path,
        '-vf', f"subtitles={subtitle_path}:force_style='Fontsize=24,PrimaryColour=&HFFFFFF&'",
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-shortest',
        '-y',
        output_video_path
    ]
    subprocess.run(cmd, check=True)
    print(f"🎥 最终视频(含字幕)已保存至：{output_video_path}")
def cleanup():
    """清理临时文件"""
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)


def run():
    print("🔧 正在提取音频...")
    extract_audio(video_path, audio_path)

    print("🎤 正在将语音转为文本...")
    segments = speech_to_text(audio_path)

    write_to_file("\n".join([seg["text"] for seg in segments]))  # 保存原始文本

    print("🌐 正在翻译文本...")
    translated_segments = translate_segments(segments)

    full_translated_text = "\n".join([seg["text"] for seg in translated_segments])
    write_to_file_1(full_translated_text)

    print("🗣️ 正在将翻译文本转为语音并对齐...")
    process_audio_segments(translated_segments, "aligned_audio.wav")

    print("📝 正在生成字幕文件...")
    generate_subtitles(translated_segments, subtitle_path)

    print("🎞️ 正在合成新视频...")
    add_audio_to_video(video_path, "aligned_audio.wav", subtitle_path, output_video_path)

    print("🧹 正在清理临时文件...")
    cleanup()

    print("✅ 项目执行完成！输出视频路径：", output_video_path)

if __name__ == "__main__":
    run()
