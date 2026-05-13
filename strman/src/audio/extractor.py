"""
Audio Extractor Module
从视频文件中提取音频
"""
import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioExtractor:
    """音频提取器"""
    
    def __init__(self, config: dict):
        """
        初始化音频提取器
        
        Args:
            config: ffmpeg配置
        """
        self.config = config.get('ffmpeg', {})
        self.audio_config = self.config.get('audio_extraction', {})
        self.sample_rate = self.audio_config.get('sample_rate', 16000)
        self.channels = self.audio_config.get('channels', 1)
        self.codec = self.audio_config.get('codec', 'pcm_s16le')
        self.format = self.audio_config.get('format', 'wav')
        self.af = self.audio_config.get('af', '')
    
    def check_ffmpeg(self) -> bool:
        """检查ffmpeg是否可用"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            logger.error("FFmpeg not found in PATH")
            return False
    
    def extract_audio(
        self,
        video_path: str,
        output_path: str | None = None,
        overwrite: bool = True
    ) -> str:
        """
        从视频提取音频
        
        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径，默认同目录同名.wav
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            输出的音频文件路径
        """
        video_path = os.path.abspath(video_path)
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # 确定输出路径
        if output_path is None:
            video_dir = os.path.dirname(video_path)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(video_dir, f"{video_name}.{self.format}")
        
        output_path = os.path.abspath(output_path)
        
        # 检查输出是否已存在
        if os.path.exists(output_path) and not overwrite:
            logger.info(f"Audio already exists: {output_path}")
            return output_path
        
        # 构建ffmpeg命令
        cmd = ['ffmpeg', '-i', video_path]
        
        # 添加音频滤镜
        if self.af:
            cmd.extend(['-af', self.af])
        
        # 添加音频参数
        cmd.extend([
            '-ar', str(self.sample_rate),
            '-ac', str(self.channels),
            '-acodec', self.codec,
        ])
        
        # 覆盖选项
        if overwrite:
            cmd.append('-y')
        
        cmd.append(output_path)
        
        logger.info(f"Extracting audio from: {video_path}")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        # 执行提取
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"Audio extraction failed: {result.stderr}")
        
        # 检查输出文件
        if not os.path.exists(output_path):
            raise RuntimeError(f"Audio file not created: {output_path}")
        
        file_size = os.path.getsize(output_path)
        logger.info(f"Audio extracted: {output_path} ({file_size / 1024 / 1024:.2f} MB)")
        
        return output_path


def extract_audio_from_video(video_path: str, config: dict) -> str:
    """
    便捷函数：从视频提取音频
    
    Args:
        video_path: 视频文件路径
        config: 配置字典
        
    Returns:
        输出的音频文件路径
    """
    extractor = AudioExtractor(config)
    return extractor.extract_audio(video_path)