import os
import sys
sys.path.append(r"E:\voiceAi\fastwhisper")
# =========================================================
# 1. 环境修复：解决 Windows 下找不到 cublas64_12.dll 的问题
# =========================================================
# 路径根据你之前的报错信息设定
env_path = r"C:\Users\mengxi\.conda\envs\fastwhisper"
dll_folders = [
    os.path.join(env_path, r"Lib\site-packages\nvidia\cublas\bin"),
    os.path.join(env_path, r"Lib\site-packages\nvidia\cudnn\bin")
]

for folder in dll_folders:
    if os.path.exists(folder):
        os.environ["PATH"] = folder + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(folder)

# 必须在修复路径后再导入模型
from faster_whisper import WhisperModel

# =========================================================
# 2. 辅助工具函数
# =========================================================
def format_srt_time(seconds):
    """将秒数转换为 SRT 标准时间格式: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milisecs = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milisecs:03d}"

def get_initial_prompt(lang):
    """针对不同语言提供提示词，优化标点和语气"""
    prompts = {
        "zh": "以下是普通话字幕，使用简体中文。",
        "en": "Hello. This is an English transcription with proper punctuation.",
        "ja": "こんにちは、日本語の字幕です。句読点を正しく使用します。",
        # "ja": "ご主人様、おちんちん、気持ちいい",
        "ko": "안녕하세요, 한국어 자막입니다.",
    }
    return prompts.get(lang, "")

# =========================================================
# 3. 核心转录逻辑
# =========================================================
def run_transcription(audio_path, output_path, lang="ko"):
    # 模型配置 (确保 G:\fastwhisper-model 是多语言版本，如 large-v3)
    model_path = r"G:\fastwhisper-model"
    
    print(f"--- 正在初始化模型 (Device: CUDA, Compute: float16) ---")
    model = WhisperModel(
        model_path, 
        device="cuda", 
        device_index=0, 
        compute_type="float16" # 4060Ti 推荐使用 float16
    )

    print(f"--- 开始处理音频: {os.path.basename(audio_path)} (目标语言: {lang}) ---")
    
    segments, info = model.transcribe(
        audio_path,
        language=lang,           # 手动指定语种，也可以设为 None 自动检测
        vad_filter=False,         # 过滤静音和底噪
        vad_parameters=dict(
            threshold=0.2,              # 默认是0.5。降低阈值可以让模型对微弱声音更敏感
            min_speech_duration_ms=100,  # 捕捉更短促的发音
            min_silence_duration_ms=800,  # 稍微拉长静音判断，防止悄悄话中的停顿被切断
            speech_pad_ms=400            # 4. 在语音前后多留出一些缓冲，确保单词首尾完整
        ),
        beam_size=5,
        initial_prompt=get_initial_prompt(lang),
        word_timestamps=False,    # 如果需要词级时间戳可设为 True
        condition_on_previous_text=False,
        no_repeat_ngram_size=3,
        repetition_penalty=1.2,
        # --- 增加鲁棒性 ---
        no_speech_threshold=0.4,          # 默认0.6。调低它，强迫模型在不确定的情况下也尝试转录
        compression_ratio_threshold=2.4,   # 防止模型陷入死循环输出重复文本
        # --- 降低模型“闭嘴”的概率 ---
        # log_prob_threshold=-1.5,         # 如果音频很糊，调低这个值可以防止模型因为不自信而沉默
    )

    print(f"检测到语种: {info.language} (置信度: {info.language_probability:.2f})")

    # 写入 SRT 文件
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = format_srt_time(seg.start)
            end = format_srt_time(seg.end)
            text = seg.text.strip()
            
            # SRT 格式：序号 -> 时间轴 -> 内容 -> 空行
            srt_block = f"{i}\n{start} --> {end}\n{text}\n\n"
            f.write(srt_block)
            
            # 实时控制台打印
            print(f"[{start} -> {end}] {text}")

    print(f"\n--- 处理完成！字幕已保存至: {output_path} ---")

# =========================================================
# 4. 执行入口
# =========================================================
if __name__ == "__main__":
    # 在这里修改你的输入输出
    input_wav = r"G:\sucai\output\SUZU2.wav" # 之前 ffmpeg 转换后的文件路径
    output_txt = r"G:\sucai\output\SUZU2.srt" # 建议后缀直接用 .srt
    
    # 语言选项: "zh", "en", "ja", "ko"
    target_language = "ko" 
    
    run_transcription(input_wav, output_txt, lang=target_language)