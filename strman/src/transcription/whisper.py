"""
Fast-Whisper Transcription Module
使用 faster-whisper 进行语音转文字
"""
import os
import sys
import logging
from dataclasses import dataclass
from typing import Iterator

logger = logging.getLogger(__name__)


@dataclass
class SubtitleSegment:
    """字幕片段"""
    index: int
    start: float      # 秒
    end: float        # 秒
    text: str        # 原文


# 语言提示词映射
LANGUAGE_PROMPTS = {
    "zh": "以下是普通话字幕，使用简体中文。",
    "en": "Hello. This is an English transcription with proper punctuation.",
    "ja": "こんにちは、日本語の字幕です。句読点を正しく使用します。",
    "ko": "안녕하세요, 한국어 자막입니다.",
    "zh-TW": "以下是台灣國語字幕，使用繁體中文。",
}


def fix_cuda_path(cuda_env_path: str):
    """修复 Windows 下 CUDA DLL 路径
    
    Args:
        cuda_env_path: CUDA 环境路径 (conda 环境目录)
    """
    dll_folders = [
        os.path.join(cuda_env_path, r"Lib\site-packages\nvidia\cublas\bin"),
        os.path.join(cuda_env_path, r"Lib\site-packages\nvidia\cudnn\bin")
    ]
    
    for folder in dll_folders:
        if os.path.exists(folder):
            os.environ["PATH"] = folder + os.pathsep + os.environ.get("PATH", "")
            if hasattr(os, 'add_dll_directory'):
                os.add_dll_directory(folder)


def format_srt_time(seconds: float) -> str:
    """将秒数转换为 SRT 标准时间格式: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milisecs = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milisecs:03d}"


def get_initial_prompt(lang: str) -> str:
    """针对不同语言提供提示词，优化标点和语气"""
    return LANGUAGE_PROMPTS.get(lang, "")


class WhisperTranscriber:
    """Whisper 转录器"""
    
    def __init__(self, config: dict):
        """
        初始化转录器
        
        Args:
            config: 配置文件 (包含 whisper, runtime 配置)
        """
        self.config = config.get('whisper', {})
        self.runtime_config = config.get('runtime', {})
        
        self.model_path = self.config.get('model_path', 'G:\\fastwhisper-model')
        self.device = self.config.get('device', 'cuda')
        self.compute_type = self.config.get('compute_type', 'float16')
        self.language = self.config.get('language', None)
        self.initial_prompt = self.config.get('initial_prompt', '')
        
        # 从配置读取路径
        self.fastwhisper_module_path = self.runtime_config.get('fastwhisper_module_path', '')
        self.cuda_env_path = self.runtime_config.get('cuda_env_path', r"C:\Users\mengxi\.conda\envs\fastwhisper")
        
        # 添加模块路径并修复 CUDA DLL
        self._setup_paths()
        
        # 延迟导入，确保路径已设置
        from faster_whisper import WhisperModel
        self.WhisperModel = WhisperModel
        
        self.model = None
    
    def _setup_paths(self):
        """设置运行时路径"""
        # 添加 faster-whisper 模块路径
        if self.fastwhisper_module_path:
            if os.path.exists(self.fastwhisper_module_path):
                sys.path.insert(0, self.fastwhisper_module_path)
                logger.info(f"Added fastwhisper module path: {self.fastwhisper_module_path}")
        
        # 修复 CUDA DLL 路径
        fix_cuda_path(self.cuda_env_path)
    
    def load_model(self):
        """加载模型"""
        if self.model is None:
            logger.info(f"Loading whisper model: {self.model_path}")
            logger.info(f"Device: {self.device}, Compute: {self.compute_type}")
            self.model = self.WhisperModel(
                self.model_path,
                device=self.device,
                device_index=0,
                compute_type=self.compute_type
            )
            logger.info("Model loaded successfully")
        return self.model
    
    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        show_progress: bool = True
    ) -> list[SubtitleSegment]:
        """
        转录音频
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码，None 则自动检测
            show_progress: 显示进度
            
        Returns:
            字幕片段列表
        """
        model = self.load_model()
        
        # 使用配置或参数指定的语言
        lang = language or self.language
        
        # 获取提示词
        prompt = self.initial_prompt
        if not prompt and lang:
            prompt = get_initial_prompt(lang)
        
        logger.info(f"Transcribing: {audio_path}")
        if lang:
            logger.info(f"Language: {lang}")
        
        segments, info = model.transcribe(
            audio_path,
            language=lang,
            vad_filter=False,
            vad_parameters=dict(
                threshold=0.2,
                min_speech_duration_ms=100,
                min_silence_duration_ms=800,
                speech_pad_ms=400
            ),
            beam_size=5,
            initial_prompt=prompt,
            word_timestamps=True,
        )
        
        # 显示检测到的语言信息
        logger.info(f"Detected language: {info.language} (prob: {info.language_probability:.2f})")
        
        # 收集字幕片段
        results: list[SubtitleSegment] = []
        
        for i, segment in enumerate(segments, 1):
            sub = SubtitleSegment(
                index=i,
                start=segment.start,
                end=segment.end,
                text=segment.text.strip()
            )
            results.append(sub)
            
            if show_progress and i % 10 == 0:
                logger.info(f"Processed {i} segments...")
        
        logger.info(f"Transcription complete: {len(results)} segments")
        return results
    
    def transcribe_to_srt(
        self,
        audio_path: str,
        output_path: str,
        language: str | None = None
    ) -> str:
        """
        转录并保存为 SRT 格式
        
        Args:
            audio_path: 音频文件路径
            output_path: 输出文件路径
            language: 语言代码
            
        Returns:
            输出的文件路径
        """
        segments = self.transcribe(audio_path, language)
        
        # 生成 SRT
        srt_content = self._generate_srt(segments)
        
        # 保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        logger.info(f"SRT saved: {output_path}")
        return output_path
    
    def _generate_srt(self, segments: list[SubtitleSegment]) -> str:
        """生成 SRT 格式"""
        lines = []
        
        for seg in segments:
            # SRT 格式: 索引 + 时间轴 + 文本 + 空行
            lines.append(str(seg.index))
            lines.append(f"{format_srt_time(seg.start)} --> {format_srt_time(seg.end)}")
            lines.append(seg.text)
            lines.append("")  # 空行分隔
        
        return "\n".join(lines)


def transcribe_audio(audio_path: str, config: dict, language: str | None = None) -> list[SubtitleSegment]:
    """
    便捷函数：转录音频
    
    Args:
        audio_path: 音频文件路径
        config: 配置字典
        language: 语言代码
        
    Returns:
        字幕片段列表
    """
    transcriber = WhisperTranscriber(config)
    return transcriber.transcribe(audio_path, language)