"""
视频字幕翻译工具 - 主入口
视频/URL -> 音频 -> 字幕 -> 翻译 -> 双语字幕
"""
import os
import sys
import argparse
import logging
import shutil
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import load_config, get_config
from src.audio.extractor import AudioExtractor
from src.transcription.whisper import WhisperTranscriber, format_srt_time
from src.translation.llm import LLMTranslator
from src.subtitle.merger import SubtitleMerger
from src.downloader.video import VideoDownloader, is_supported_url
from src.summarizer.notes import VideoSummarizer


# 配置日志
def setup_logging(level: str = "INFO"):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


def get_output_paths(config: dict, video_name: str):
    """获取输出路径"""
    output_config = config.get('output', {})
    
    # 输出目录
    output_dir = output_config.get('directory', 'output')
    if not output_dir:
        output_dir = 'output'
    
    # 临时目录
    temp_dir = output_config.get('temp_directory', 'temp')
    
    # 获取子目录
    original_dir = output_config.get('original_dir', 'original')
    bilingual_dir = output_config.get('bilingual_dir', 'bilingual')
    summary_text_dir = output_config.get('summary_text_dir', 'summary_text')
    summary_video_dir = output_config.get('summary_video_dir', 'summary_video')
    
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, original_dir), exist_ok=True)
    os.makedirs(os.path.join(output_dir, bilingual_dir), exist_ok=True)
    os.makedirs(os.path.join(output_dir, summary_text_dir), exist_ok=True)
    os.makedirs(os.path.join(output_dir, summary_video_dir), exist_ok=True)
    
    # 输出文件名
    video_name_safe = video_name  # 基础文件名
    
    # 字幕后缀
    subtitle_suffix = output_config.get('subtitle_suffix', '.srt')
    
    return {
        'output_dir': output_dir,
        'temp_dir': temp_dir,
        'original_dir': original_dir,
        'bilingual_dir': bilingual_dir,
        'summary_text_dir': summary_text_dir,
        'summary_video_dir': summary_video_dir,
        'original_srt': os.path.join(output_dir, original_dir, f"{video_name_safe}{subtitle_suffix}"),
        'bilingual_srt': os.path.join(output_dir, bilingual_dir, f"{video_name_safe}{subtitle_suffix}"),
        'summary_text_md': os.path.join(output_dir, summary_text_dir, f"{video_name_safe}.md"),
        'summary_video_md': os.path.join(output_dir, summary_video_dir, f"{video_name_safe}_视频总结.md"),
    }


def process_video(
    video_path: str,
    config: dict,
    language: str | None = None,
    target_lang: str = "中文",
    output_path: str | None = None,
    keep_audio: bool = False,
    skip_extraction: bool = False,
    only_subtitle: bool = False,
    is_url: bool = False,
    generate_summary: bool = False
) -> dict:
    """
    处理视频，生成双语字幕
    
    Args:
        video_path: 视频文件路径或URL
        config: 配置字典
        language: 源语言代码
        target_lang: 目标语言
        output_path: 输出字幕路径（可选）
        keep_audio: 是否保留提取的音频
        skip_extraction: 跳过音频提取
        only_subtitle: 只生成原文字幕
        is_url: 是否是URL输入
        
    Returns:
        包含输出文件路径的字典
    """
    logger = logging.getLogger(__name__)
    
    # 获取输出路径
    if is_url:
        # 从URL提取视频名
        video_name = "video"
        # 尝试从URL获取标题
        try:
            from src.downloader.video import VideoDownloader
            dl = VideoDownloader(config)
            # 下载后会获得实际文件名
            video_name = "bili_video"
        except:
            pass
    else:
        video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    paths = get_output_paths(config, video_name)
    output_dir = paths['output_dir']
    temp_dir = paths['temp_dir']
    
    # 临时视频文件（URL下载）
    temp_video = None
    
    logger.info(f"="*50)
    logger.info(f"Processing: {video_path}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"="*50)
    
    # 步骤1: 下载视频（如果是URL）
    actual_video_path = video_path
    
    if is_url:
        logger.info("Step 1: Downloading video...")
        downloader = VideoDownloader(config)
        temp_video = downloader.download(video_path, temp_dir)
        actual_video_path = temp_video
        logger.info(f"Video downloaded: {temp_video}")
        video_name = os.path.splitext(os.path.basename(temp_video))[0]
        
        # 更新输出路径
        paths = get_output_paths(config, video_name)
    
    # 步骤2: 提取音频
    audio_path = None
    
    if only_subtitle:
        audio_path = actual_video_path
        logger.info("Using video directly as audio source")
    elif skip_extraction:
        audio_path = os.path.join(
            temp_dir, 
            f"{video_name}.wav"
        )
        if not os.path.exists(audio_path):
            # 尝试从临时目录
            audio_path = os.path.join(temp_dir, "audio.wav")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio not found: {audio_path}")
        logger.info(f"Using existing audio: {audio_path}")
    else:
        extractor = AudioExtractor(config)
        # 提取到临时目录
        audio_path = extractor.extract_audio(
            actual_video_path,
            os.path.join(temp_dir, f"{video_name}.wav")
        )
        logger.info(f"Audio extracted: {audio_path}")
    
    # 步骤3: 转录
    logger.info("Step 2: Transcribing audio...")
    transcriber = WhisperTranscriber(config)
    original_segments = transcriber.transcribe(audio_path, language=language)
    logger.info(f"Transcription complete: {len(original_segments)} segments")
    
    # 步骤4: 翻译
    translated_segments = None
    
    if not only_subtitle:
        logger.info("Step 3: Translating subtitles...")
        translator = LLMTranslator(config)
        translated_segments = translator.translate_all(
            [seg.text for seg in original_segments],
            target_lang=target_lang
        )
        logger.info(f"Translation complete: {len(translated_segments)} segments")
    
    # 步骤5: 保存字幕
    paths = get_output_paths(config, video_name)
    
    if only_subtitle:
        # 保存原文字幕
        output_srt = output_path or paths['original_srt']
        
        lines = []
        for seg in original_segments:
            lines.append(str(seg.index))
            lines.append(f"{format_srt_time(seg.start)} --> {format_srt_time(seg.end)}")
            lines.append(seg.text)
            lines.append("")
        
        content = "\n".join(lines)
        with open(output_srt, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Original subtitle saved: {output_srt}")
        final_output = output_srt
    else:
        # 合并双语字幕
        logger.info("Step 4: Merging bilingual subtitles...")
        merger = SubtitleMerger(config)
        merged_segments = merger.merge(original_segments, translated_segments)
        
        output_srt = output_path or paths['bilingual_srt']
        merger.save(merged_segments, output_srt)
        logger.info(f"Bilingual subtitle saved: {output_srt}")
        final_output = output_srt
    
    # 步骤6: 生成视频总结（可选）
    summary_enabled = config.get('summary', {}).get('enabled', False)
    summary_output = None
    
    # 检查配置或命令行参数
    if (summary_enabled or generate_summary) and original_segments:
        logger.info("Step 5: Generating video summary...")
        summarizer = VideoSummarizer(config)
        
        # 获取摘要语言
        summary_lang = config.get('summary', {}).get('language', '中文')
        
        summary = summarizer.summarize(original_segments, summary_lang)
        
        # 保存到summary_text目录
        summary_path = paths['summary_text_md']
        summarizer.save_summary(summary, summary_path)
        summary_output = summary_path
        logger.info(f"Summary saved: {summary_path}")
    
    # 清理临时文件
    cleanup_temp = config.get('bilibili', {}).get('cleanup_temp', True)
    
    # 清理下载的视频
    if cleanup_temp and is_url and temp_video and os.path.exists(temp_video):
        try:
            os.remove(temp_video)
            logger.info(f"Temp video cleaned: {temp_video}")
        except Exception as e:
            logger.warning(f"Failed to clean temp video: {e}")
    
    # 清理临时音频（在temp目录中的wav）
    if cleanup_temp and audio_path and os.path.exists(audio_path):
        if temp_dir in audio_path:  # 只清理临时目录的音频
            try:
                os.remove(audio_path)
                logger.info(f"Temp audio cleaned: {audio_path}")
            except Exception as e:
                logger.warning(f"Failed to clean audio: {e}")
    
    logger.info(f"="*50)
    logger.info(f"DONE! Output: {final_output}")
    logger.info(f"="*50)
    
    return {
        'output_path': final_output,
        'output_dir': output_dir,
        'segments': len(original_segments),
        'summary_path': summary_output,
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="视频字幕翻译工具 - 支持本地视频和B站URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py 234.mp4                           # 本地视频
  python main.py https://bilibili.com/video/BVxxx  # B站视频
  python main.py video.mp4 -l ko                  # 指定语言
  python main.py video.mp4 --only-subtitle          # 仅原文字幕
        """
    )
    
    parser.add_argument(
        'input',
        help="视频文件路径或B站URL"
    )
    parser.add_argument(
        '-l', '--language',
        help="源语言代码 (如 ko, en, ja, zh)",
        default=None
    )
    parser.add_argument(
        '-t', '--target-lang',
        help="目标语言",
        default="中文"
    )
    parser.add_argument(
        '-o', '--output',
        help="输出文件路径",
        default=None
    )
    parser.add_argument(
        '-c', '--config',
        help="配置文件路径",
        default=None
    )
    parser.add_argument(
        '--keep-audio',
        help="保留提取的音频文件",
        action='store_true'
    )
    parser.add_argument(
        '--skip-extraction',
        help="跳过音频提取",
        action='store_true'
    )
    parser.add_argument(
        '--only-subtitle',
        help="仅生成原文字幕",
        action='store_true'
    )
    parser.add_argument(
        '--summary',
        help="生成视频总结笔记",
        action='store_true'
    )
    parser.add_argument(
        '-v', '--verbose',
        help="显示详细日志",
        action='store_true'
    )
    
    args = parser.parse_args()
    
    # 配置日志
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    # 加载配置
    config = load_config(args.config)
    
    # 检查输入
    input_path = args.input
    
    # 检测是否是URL
    is_url = is_supported_url(input_path)
    
    if is_url:
        logger.info(f"Detected URL: {input_path}")
    elif not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # 处理
    try:
        result = process_video(
            video_path=input_path,
            config=config,
            language=args.language,
            target_lang=args.target_lang,
            output_path=args.output,
            keep_audio=args.keep_audio,
            skip_extraction=args.skip_extraction,
            only_subtitle=args.only_subtitle,
            is_url=is_url,
            generate_summary=args.summary
        )
        
        print(f"\nOutput: {result['output_path']}")
        print(f"Directory: {result['output_dir']}")
        print(f"Segments: {result['segments']}")
        if result.get('summary_path'):
            print(f"Summary: {result['summary_path']}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()