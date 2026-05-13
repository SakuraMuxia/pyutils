"""
Video Downloader Module
支持从 B站 等平台下载视频
"""
import os
import re
import subprocess
import logging
import tempfile
import shutil
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def is_bilibili_url(url: str) -> bool:
    """检查是否是B站链接"""
    patterns = [
        r'bilibili\.com/video/',
        r'b23\.tv/',  # B站短链接
        r'bilibili\.com\\/video/',
    ]
    return any(re.search(p, url) for p in patterns)


def is_supported_url(url: str) -> bool:
    """检查是否支持此URL"""
    return is_bilibili_url(url)


class VideoDownloader:
    """视频下载器"""
    
    def __init__(self, config: dict):
        """
        初始化下载器
        
        Args:
            config: 配置字典
        """
        self.config = config.get('bilibili', {})
        self.tool = self.config.get('tool', 'yt-dlp')
        self.quality = self.config.get('quality', 'best')
        self.cleanup = self.config.get('cleanup', True)
        
        # 检查工具是否安装
        self._check_tool()
    
    def _check_tool(self):
        """检查下载工具"""
        try:
            subprocess.run(
                [self.tool, '--version'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
        except FileNotFoundError:
            logger.warning(f"{self.tool} not found, attempting to install...")
            self._install_tool()
    
    def _install_tool(self):
        """安装下载工具"""
        if self.tool == 'yt-dlp':
            subprocess.run(['pip', 'install', 'yt-dlp'], check=True)
        elif self.tool == 'you-get':
            subprocess.run(['pip', 'install', 'you-get'], check=True)
    
    def download(
        self,
        url: str,
        output_dir: str | None = None,
        cookies_file: str | None = None
    ) -> str:
        """
        下载视频
        
        Args:
            url: 视频URL
            output_dir: 输出目录
            cookies_file: Cookie文件 (用于需要登录的视频)
            
        Returns:
            下载的视频文件路径
        """
        if output_dir is None:
            output_dir = tempfile.gettempdir()
        
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Downloading video from: {url}")
        
        # 构建下载命令
        if self.tool == 'yt-dlp':
            return self._download_yt_dlp(url, output_dir, cookies_file)
        elif self.tool == 'you-get':
            return self._download_you_get(url, output_dir, cookies_file)
        else:
            raise ValueError(f"Unsupported tool: {self.tool}")
    
    def _download_yt_dlp(
        self,
        url: str,
        output_dir: str,
        cookies_file: str | None = None
    ) -> str:
        """使用 yt-dlp 下载"""
        # 输出模板
        output_template = os.path.join(output_dir, '%(title)s.%(ext)s')
        
        cmd = [
            self.tool,
            '-o', output_template,
            '--no-playlist',  # 不下载播放列表
            '--merge-output-format', 'mp4',  # 合并为mp4
        ]
        
        # 添加cookie (如果需要)
        if cookies_file and os.path.exists(cookies_file):
            cmd.extend(['--cookies', cookies_file])
        
        cmd.append(url)
        
        logger.debug(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Download failed: {result.stderr}")
            raise RuntimeError(f"Video download failed: {result.stderr}")
        
        # 找到下载的文件
        files = list(Path(output_dir).glob('*.*'))
        # 排除临时文件
        video_files = [f for f in files if f.suffix.lower() 
                    in ['.mp4', '.mkv', '.flv', '.avi', '.webm']]
        
        if not video_files:
            raise RuntimeError("No video file found after download")
        
        # 返回最新的视频文件
        latest = max(video_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"Video downloaded: {latest}")
        
        return str(latest)
    
    def _download_you_get(
        self,
        url: str,
        output_dir: str,
        cookies_file: str | None = None
    ) -> str:
        """使用 you-get 下载"""
        cmd = [
            self.tool,
            '-o', output_dir,
            '--no-playlist',
        ]
        
        if cookies_file and os.path.exists(cookies_file):
            cmd.extend(['--cookies', cookies_file])
        
        cmd.append(url)
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Video download failed: {result.stderr}")
        
        # 找到下载的文件
        files = list(Path(output_dir).glob('*.*'))
        video_files = [f for f in files if f.suffix.lower() 
                    in ['.mp4', '.mkv', '.flv', '.avi', '.webm']]
        
        if not video_files:
            raise RuntimeError("No video file found")
        
        latest = max(video_files, key=lambda f: f.stat().st_mtime)
        return str(latest)


def download_video(url: str, config: dict, output_dir: str | None = None) -> str:
    """
    便捷函数：下载视频
    
    Args:
        url: 视频URL
        config: 配置字典
        output_dir: 输出目录
        
    Returns:
        下载的视频文件路径
    """
    downloader = VideoDownloader(config)
    return downloader.download(url, output_dir)