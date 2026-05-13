"""
Bilingual Subtitle Merger Module
合并原文和译文生成双语字幕
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BilingualSegment:
    """双语字幕片段"""
    index: int
    start: float        # 秒
    end: float          # 秒
    original: str       # 原文
    translated: str     # 译文
    bilingual_text: str  # 合并后的文本


def format_srt_time(seconds: float) -> str:
    """将秒数转换为 SRT 标准时间格式: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milisecs = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milisecs:03d}"


def format_vtt_time(seconds: float) -> str:
    """将秒数转换为 VTT 标准时间格式: HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milisecs = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milisecs:03d}"


class SubtitleMerger:
    """字幕合并器"""
    
    def __init__(self, config: dict):
        """
        初始化字幕合并器
        
        Args:
            config: 字幕配置
        """
        self.config = config.get('subtitle', {})
        self.subtitle_format = self.config.get('format', 'srt')
        self.separator = self.config.get('separator', '\n')
        self.show_language_tag = self.config.get('show_language_tag', False)
        self.original_tag = self.config.get('original_tag', '[Original]')
        self.translated_tag = self.config.get('translated_tag', '[翻译]')
    
    def merge(
        self,
        original_segments: list,
        translated_segments: list,
        show_progress: bool = True
    ) -> list[BilingualSegment]:
        """
        合并原文和译文
        
        Args:
            original_segments: 原文片段列表 (来自 transcription)
            translated_segments: 译文片段列表 (来自 translation)
            show_progress: 显示进度
            
        Returns:
            双语片段列表
        """
        if len(original_segments) != len(translated_segments):
            logger.warning(
                f"Segment count mismatch: {len(original_segments)} original vs "
                f"{len(translated_segments)} translated. Truncating to minimum."
            )
        
        # 确保数量一致
        count = min(len(original_segments), len(translated_segments))
        results: list[BilingualSegment] = []
        
        for i in range(count):
            orig_seg = original_segments[i]
            trans_seg = translated_segments[i]
            
            # 构建双语文本
            if self.show_language_tag:
                bilingual = (
                    f"{self.original_tag} {orig_seg.text}\n"
                    f"{self.translated_tag} {trans_seg.translated}"
                )
            else:
                bilingual = f"{orig_seg.text}{self.separator}{trans_seg.translated}"
            
            results.append(BilingualSegment(
                index=i + 1,
                start=orig_seg.start,
                end=orig_seg.end,
                original=orig_seg.text,
                translated=trans_seg.translated,
                bilingual_text=bilingual
            ))
            
            if show_progress and (i + 1) % 100 == 0:
                logger.info(f"Merged {i + 1}/{count} segments...")
        
        logger.info(f"Merge complete: {len(results)} bilingual segments")
        return results
    
    def generate_srt(self, segments: list[BilingualSegment]) -> str:
        """
        生成 SRT 格式
        
        Args:
            segments: 双语片段列表
            
        Returns:
            SRT 内容
        """
        lines = []
        
        for seg in segments:
            lines.append(str(seg.index))
            lines.append(f"{format_srt_time(seg.start)} --> {format_srt_time(seg.end)}")
            lines.append(seg.bilingual_text)
            lines.append("")  # 空行分隔
        
        return "\n".join(lines)
    
    def generate_vtt(self, segments: list[BilingualSegment]) -> str:
        """
        生成 VTT 格式
        
        Args:
            segments: 双语片段列表
            
        Returns:
            VTT 内容
        """
        lines = ["WEBVTT", ""]  # VTT 文件头
        
        for seg in segments:
            lines.append(str(seg.index))
            lines.append(f"{format_vtt_time(seg.start)} --> {format_vtt_time(seg.end)}")
            lines.append(seg.bilingual_text)
            lines.append("")  # 空行分隔
        
        return "\n".join(lines)
    
    def save(
        self,
        segments: list[BilingualSegment],
        output_path: str,
        format: str | None = None
    ) -> str:
        """
        保存字幕文件
        
        Args:
            segments: 双语片段列表
            output_path: 输出文件路径
            format: 格式 (srt/vtt)，默认使用配置
            
        Returns:
            输出的文件路径
        """
        fmt = format or self.subtitle_format
        
        if fmt == 'vtt':
            content = self.generate_vtt(segments)
        else:
            content = self.generate_srt(segments)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Subtitle saved: {output_path}")
        return output_path


def merge_subtitles(
    original_segments: list,
    translated_segments: list,
    config: dict,
    output_path: str,
    format: str | None = None
) -> str:
    """
    便捷函数：合并并保存双语字幕
    
    Args:
        original_segments: 原文片段列表
        translated_segments: 译文片段列表
        config: 配置字典
        output_path: 输出文件路径
        format: 格式 (srt/vtt)
        
    Returns:
        输出的文件路径
    """
    merger = SubtitleMerger(config)
    merged = merger.merge(original_segments, translated_segments)
    return merger.save(merged, output_path, format)