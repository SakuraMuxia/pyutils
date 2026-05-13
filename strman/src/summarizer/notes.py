"""
Video Summarizer Module
使用 LLM 生成结构化视频笔记
"""
import logging
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VideoSummary:
    """视频摘要"""
    title: str          # 标题
    overview: str       # 概要
    key_points: list     # 关键点
    chapters: list     # 章节 (时间线)
    quotes: list        # 关键引言
    tags: list         # 标签
    full_content: str   # 完整 Markdown


class VideoSummarizer:
    """视频摘要生成器"""
    
    def __init__(self, config: dict):
        """
        初始化摘要生成器
        
        Args:
            config: 配置字典
        """
        self.config = config.get('summary', {})
        self.llm_config = config.get('llm', {})
        self.provider = self.llm_config.get('provider', 'openai')
        self.batch_size = self.config.get('batch_size', 50)
        
        # 初始化 LLM 客户端
        self._init_client()
    
    def _init_client(self):
        """初始化 LLM 客户端"""
        if self.provider == 'openai':
            openai_config = self.llm_config.get('openai', {})
            base_url = openai_config.get('base_url', 'http://localhost:11434/v1')
            api_key = openai_config.get('api_key', 'ollama')
            
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
            except ImportError:
                raise ImportError("Please install openai: pip install openai")
            
            self.model = openai_config.get('model', 'qwen2.5')
    
    def _build_summary_prompt(self, subtitle_data: list, lang: str = "中文") -> str:
        """
        构建摘要提示词
        
        Args:
            subtitle_data: 字幕数据列表
            lang: 目标语言
            
        Returns:
            提示词
        """
        # 构建字幕文本 - 使用所有字幕，不限制条数
        subtitles = []
        for item in subtitle_data:
            start = self._format_time(item.get('start', 0))
            text = item.get('text', '')
            subtitles.append(f"[{start}] {text}")
        
        content = "\n".join(subtitles)
        
        prompt = f"""你是一个专业的视频内容分析助手。请分析以下视频字幕内容，生成结构化的 Markdown 笔记。

要求：
1. 用 {lang} 生成
2. 生成结构化内容，包含：标题、概要、关键点、章节时间线、关键引言、标签
3. 时间格式如 "00:01:30 - 标题"
4. 格式规范，使用 Markdown

视频字幕内容：
{content}

请生成以下格式的笔记：

```markdown
# 视频标题（从内容中提取）

## 概要
（用2-3句话总结视频主要内容）

## 关键点
1. ...
2. ...
3. ...

## 章节时间线
- 00:00:00 - 章节1
- 00:01:30 - 章节2
- ...

## 关键引言
> "引言内容"

## 标签
#标签1 #标签2
```

请只返回 Markdown 内容，不要其他说明："""
        return prompt
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _parse_summary(self, response: str, subtitle_data: list) -> VideoSummary:
        """
        解析���要响应
        
        Args:
            response: LLM 响应
            subtitle_data: 原始字幕数据
            
        Returns:
            VideoSummary
        """
        content = response.strip()
        
        # 提取各部分
        title = "视频笔记"
        overview = ""
        key_points = []
        chapters = []
        quotes = []
        tags = []
        
        # 简单解析 Markdown
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测章节
            if line.startswith('## '):
                current_section = line[3:]
            elif line.startswith('# ') and current_section is None:
                title = line[2:].strip()
            elif current_section == '概要':
                overview += line + " "
            elif current_section == '关键点':
                if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                    key_points.append(line.lstrip('1234567890.').strip())
            elif current_section == '章节时间线':
                if line.startswith('- '):
                    chapters.append(line[2:])
            elif current_section == '关键引言':
                if line.startswith('>'):
                    quotes.append(line.lstrip('> ').strip())
            elif current_section == '标签':
                tags = [t.strip() for t in line.split('#') if t.strip()]
        
        return VideoSummary(
            title=title,
            overview=overview.strip(),
            key_points=key_points,
            chapters=chapters,
            quotes=quotes,
            tags=tags,
            full_content=content
        )
    
    def _get_subtitle_data(self, segments: list) -> list:
        """
        获取字幕数据
        
        Args:
            segments: 字幕片段列表
            
        Returns:
            数据列表
        """
        data = []
        for seg in segments:
            data.append({
                'index': seg.index,
                'start': seg.start,
                'end': seg.end,
                'text': seg.text
            })
        return data
    
    def summarize(
        self,
        subtitle_segments: list,
        target_lang: str = "中文",
        show_progress: bool = True
    ) -> VideoSummary:
        """
        生成视频摘要
        
        Args:
            subtitle_segments: 字幕片段列表
            target_lang: 目标语言
            show_progress: 显示进度
            
        Returns:
            VideoSummary
        """
        logger.info(f"Generating summary for {len(subtitle_segments)} segments...")
        
        # 获取字幕数据
        subtitle_data = self._get_subtitle_data(subtitle_segments)
        
        # 构建提示词
        prompt = self._build_summary_prompt(subtitle_data, target_lang)
        
        # 获取 max_tokens 配置
        max_tokens = self.config.get('max_tokens', 8192)
        
        # 调用 LLM
        if self.provider == 'openai':
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=max_tokens,
            )
            
            content = response.choices[0].message.content
        
        # 解析结果
        summary = self._parse_summary(content, subtitle_data)
        
        logger.info("Summary generated successfully")
        return summary
    
    def save_summary(
        self,
        summary: VideoSummary,
        output_path: str
    ) -> str:
        """
        保存摘要到文件
        
        Args:
            summary: 视频摘要
            output_path: 输出路径
            
        Returns:
            文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary.full_content)
        
        logger.info(f"Summary saved: {output_path}")
        return output_path


def generate_video_summary(
    subtitle_segments: list,
    config: dict,
    output_path: str,
    target_lang: str = "中文"
) -> str:
    """
    便捷函数：生成视频摘要
    
    Args:
        subtitle_segments: 字幕片段列表
        config: 配置字典
        output_path: 输出路径
        target_lang: 目标语言
        
    Returns:
        输出的文件路径
    """
    summarizer = VideoSummarizer(config)
    summary = summarizer.summarize(subtitle_segments, target_lang)
    return summarizer.save_summary(summary, output_path)