# 项目开发日志 (Changelog)

## 当前版本: v2.0.0

---

### 2026-05-12 - v2.0.0

**代码重构:**
- 将子模块移动到 src/ 目录
- 优化导入路径: from src.xxx import xxx

**目录结构调整:**
```
strMan/
├── src/                   # 源代码模块
│   ├── audio/             # 音频提取
│   ├── transcription/    # 转录
│   ├── translation/       # 翻译
│   ├── subtitle/         # 字幕合并
│   ├── downloader/       # 下载
│   ├── summarizer/       # 总结
│   └── utils/            # 工具
│
├── output/               # 输出目录
└── temp/               # 临时目录
```

**配置更新:**
- 字幕后缀: .srt
- 临时文件自动清理 (cleanup_temp)
- 输出统一到 output/ 目录

---

## 功能清单

### ✅ 已完成

| 功能 | 状态 | 说明 |
|------|------|------|
| 视频音频提取 | 完成 | 使用 ffmpeg 提取音频 |
| Fast-Whisper 转录 | 完成 | 支持 CUDA 加速 |
| LLM 翻译 | 完成 | 支持 OpenAI/Ollama/vLLM |
| 双语字幕生成 | 完成 | 原文 + 译文显示 |
| B站视频下载 | 完成 | 使用 yt-dlp |
| 临时文件清理 | 完成 | 任务完成后自动删除temp文件 |
| reasoning_split | 完成 | 分离思考内容 |
| 视频总结 | 完成 | 结构化 Markdown 笔记 |
| 项目结构优化 | 完成 | src目录模块化 |
| 4输出目录分类 | 完成 | original/bilingual/summary_text/summary_video |

### 🔄 待优化

| 功能 | 优先级 | 说明 |
|------|--------|------|
| Web界面 | 高 | 后端 + 前端Vue |
| 多语言支持 | 中 | 目标语言选择 |
| 批量处理 | 中 | 多个视频 |
| 视觉+字幕联合总结 | 中 | summary_video目录 |
| ASS特效字幕 | 低 | 字幕特效 |

### 🗑️ 已废弃

| 功能 | 原因 |
|------|------|
| you-get 支持 | yt-dlp 已足够 |

---

## 开发记录

### 2026-05-09 - v1.0.0

**新增功能：**
- 项目框架搭建
- config.yaml 配置系统
- main.py 命令行入口
- audio/extractor.py - 音频提取模块
- transcription/whisper.py - Fast-Whisper 转录模块
- translation/llm.py - LLM 翻译模块
- subtitle/merger.py - 双语字幕合并模块
- downloader/video.py - B站视频下载模块

**配置文件：**
- Whisper 模型路径: `G:\fastwhisper-model`
- LLM API: MiniMax-M2.5
- faster-whisper 路径: `E:\voiceAi\fastwhisper`

**新增命令参数：**
- `--language` / `-l` - 指定源语言
- `--target-lang` / `-t` - 指定目标语言
- `--output` / `-o` - 指定输出文件
- `--only-subtitle` - 仅生成原文字幕
- `--keep-audio` - 保留音频文件
- `--verbose` / `-v` - 详细日志
- `--config` / `-c` - 配置文件路径

**已知问题：**
- Windows 终端编码问题（显示乱码，但功能正常）

---

### 2026-05-09 - v1.1.0

**新增功能：**
- summarizer/notes.py - 视频总结模块
- 生成结构化 Markdown 笔记
- 包含：标题、概要、关键点、章节时间线、关键引言、标签

**新增配置：**
```yaml
summary:
  enabled: false
  max_segments: 100
  language: "中文"
```

**新增命令参数：**
- `--summary` - 生成视频总结笔记

---

## 完整配置参数参考

### config.yaml 完整配置

```yaml
# ===================
# Fast-Whisper 配置
# ===================
whisper:
  model_path: "G:\\fastwhisper-model"  # 模型路径
  device: "cuda"                       # cuda 或 cpu
  compute_type: "float16"              # float16, int8
  language: null                     # 指定语言，null自动检测
  initial_prompt: ""                 # 提示词

# ===================
# LLM 翻译配置
# ===================
llm:
  provider: "openai"                # openai, ollama, vllm
  
  openai:
    base_url: "https://api.minimaxi.com/v1"
    api_key: "sk-cp-xxx"           # 你的API密钥
    model: "MiniMax-M2.5"
  
  ollama:
    base_url: "http://localhost:11434"
    model: "qwen2.5"
  
  vllm:
    base_url: "http://localhost:8000"
    model: "qwen2.5"
  
  temperature: 0.3
  max_tokens: 4096
  batch_size: 20

# ===================
# FFmpeg 配置
# ===================
ffmpeg:
  audio_extraction:
    format: "wav"
    sample_rate: 16000
    channels: 1
    codec: "pcm_s16le"

# ===================
# 字幕格式配置
# ===================
subtitle:
  format: "srt"
  separator: "\n"
  show_language_tag: false
  original_tag: "[原文]"
  translated_tag: "[译文]"

# ===================
# B站下载配置
# ===================
bilibili:
  tool: "yt-dlp"
  cleanup: true

# ===================
# 视频总结配置
# ===================
summary:
  enabled: false
  max_segments: 100
  language: "中文"
```

---

## 模块架构

### 处理流程

```
输入(视频/URL)
    ↓
[视频下载] ← B站URL则下载
    ↓
[音频提取] ← ffmpeg
    ↓
[语音转录] ← faster-whisper
    ↓
[LLM翻译] ← OpenAI/Ollama/vLLM
    ↓
[字幕合并] ← 原文+译文
    ↓
输出(SRT双语字幕)
    ↓ (可选)
[视频总结] ← 结构化笔记
```

### 文件结构

```
strMan/
├── config.yaml              # 配置文件
├── main.py                # 主入口
├── run.bat               # Windows快速启动脚本
├── README.md             # 使用说明
├── CHANGELOG.md          # 项目日志
│
├── audio/                 # 音频提取模块
│   ├── __init__.py
│   └── extractor.py
│
├── transcription/        # 转录模块
│   ├── __init__.py
│   └── whisper.py
│
├── translation/          # 翻译模块
│   ├── __init__.py
│   └── llm.py
│
├── subtitle/            # 字幕模块
│   ├── __init__.py
│   └── merger.py
│
├── downloader/          # 下载模块
│   ├── __init__.py
│   └── video.py
│
├── summarizer/          # 总结模块
│   ├── __init__.py
│   └── notes.py
│
├── utils/               # 工具模块
│   ├── __init__.py
│   └── config.py
│
├── output/             # 字幕输出目录
│   └── *.srt
│
└── temp/              # 临时文件目录
    ├── *.wav
    └── *.mp4
```