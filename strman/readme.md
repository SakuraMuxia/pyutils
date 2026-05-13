# 视频字幕翻译工具 (Video Subtitle Translator)

一个自动化视频字幕生成工具，支持将本地视频或B站视频链接转换为双语字幕。

## 功能特性

- **视频转字幕**: 使用 Fast-Whisper 进行高精度语音识别
- **双语字幕**: 原文 + 译文同时显示
- **B站支持**: 直接输入B站URL自动下载处理
- **GPU加速**: 支持 CUDA 加速转录
- **视频总结**: 生成结构化 Markdown 笔记

## 项目结构

```
strMan/
├── .env                     # 环境配置
├── config.yaml               # 项目配置文件
├── main.py                  # 主入口
├── run.bat                  # Windows快速启动脚本
├── requirements.txt         # Python依赖
├── README.md               # 使用说明
├── CHANGELOG.md           # 项目日志
│
├── src/                   # 源代码模块
│   ├── audio/             # 音频提取模块
│   ├── transcription/    # 转录模块
│   ├── translation/       # 翻译模块
│   ├── subtitle/         # 字幕合并模块
│   ├── downloader/       # 视频下载模块
│   ├── summarizer/       # 视频总结模块
│   └── utils/            # 工具模块
│
├── output/               # 输出目录
│   ├── original/         # 原文字幕 (*.srt)
│   ├── bilingual/       # 双语字幕 (*.srt)
│   ├── summary_text/     # 字幕文本总结 (*.md)
│   └── summary_video/  # 视觉+字幕联合总结 (*.md)
│
└── temp/                 # 临时目录
    └── *.mp4, *.wav     # 下载的视频和音频(任务完成后自动删除)
```

## 环境要求

- **Python**: 3.11 (使用 conda 环境)
- **CUDA**: 可选，用于GPU加速
- **FFmpeg**: 必须安装并配置到系统PATH
- **faster-whisper**: 模型文件

## 外部配置

### 1. FFmpeg 安装

Windows:
```bash
# 方法1: 使用 Chocolatey
choco install ffmpeg

# 方法2: 手动安装
# 下载 https://ffmpeg.org/download.html
# 解压并将 bin 目录添加到系统 PATH
```

验证安装:
```bash
ffmpeg -version
```

### 2. Faster-Whisper 模型

下载 CTranslate2 格式的模型到本地:

推荐模型 (按需求选择):

| 模型 | 大小 | 精度 | 内存需求 |
|------|------|------|----------|
| faster-whisper-large-v3 | ~3GB | 最高 | 6GB+ VRAM |
| faster-whisper-medium | ~1.5GB | 高 | 4GB+ VRAM |
| faster-whisper-small | ~500MB | 中 | 2GB+ VRAM |

下载方式:
```bash
# 方法1: 使用 huggingface-cli
huggingface-cli download Systran/faster-whisper-large-v3 --local-dir G:\fastwhisper-model

# 方法2: 从 Hugging Face 下载
# https://huggingface.co/Systran/faster-whisper-large-v3
```

### 3. CUDA 加速依赖 (可选)

如需 GPU 加速，fast-whisper conda 环境需要安装:

```bash
# 在 fastwhisper 环境中安装
conda activate fastwhisper
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

检查 GPU 是否工作:
```bash
nvidia-smi
```

### 4. LLM 翻译服务

项目支持三种翻译服务:

#### OpenAI 兼容 API (如 MiniMax, Ollama, vLLM)

```yaml
llm:
  provider: "openai"
  openai:
    base_url: "https://api.minimaxi.com/v1"  # 或你使用的API地址
    api_key: "your-api-key"
    model: "MiniMax-M2.5"
```

#### 本地 Ollama

```yaml
llm:
  provider: "ollama"
  ollama:
    base_url: "http://localhost:11434"
    model: "qwen2.5"
```

#### vLLM

```yaml
llm:
  provider: "vllm"
  vllm:
    base_url: "http://localhost:8000"
    model: "qwen2.5"
```

## 快速开始

### 1. 环境配置

```bash
# 创建 conda 环境
conda create -n fastwhisper python=3.11
conda activate fastwhisper

# 安装依赖
pip install -r requirements.txt

# 安装 CUDA 依赖 (可选)
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

### 2. 配置 config.yaml

根据你的环境修改配置文件:

```yaml
# Whisper 模型配置
whisper:
  model_path: "G:\\fastwhisper-model"  # 模型路径
  device: "cuda"                      # cuda 或 cpu
  compute_type: "float16"            # float16, int8

# LLM 翻译配置
llm:
  provider: "openai"
  openai:
    base_url: "http://192.168.1.11:9090/v1"  # 你的API地址
    api_key: "your-api-key"
    model: "your-model"
```

### 3. 运行

```bash
# 激活环境
conda activate fastwhisper

# 或使用 run.bat
run.bat "https://www.bilibili.com/video/BVxxx"
```

## 使用示例

### 基本用法

```bash
# 处理本地视频
python main.py video.mp4
python main.py "C:\Users\mengxi\Downloads\1233.mp4" --only-subtitle

# 处理B站视频
python main.py https://www.bilibili.com/video/BV1AV576bEf2

# 指定语言
python main.py video.mp4 -l ja          # 日语
python main.py video.mp4 -l ko        # 韩语
python main.py video.mp4 -l en          # 英语

# 仅生成原文字幕
python main.py video.mp4 --only-subtitle

# 生成视频总结
python main.py video.mp4 --summary
python main.py "C:\Users\mengxi\Downloads\1223.mp4" --summary
```

### 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--language` | `-l` | 源语言 (ko/en/ja/zh) | 自动检测 |
| `--target-lang` | `-t` | 目标语言 | 中文 |
| `--output` | `-o` | 输出文件路径 | output目录 |
| `--only-subtitle` | - | 仅生成原文字幕 | 否 |
| `--summary` | - | 生成视频总结 | 否 |
| `--keep-audio` | - | 保留音频文件 | 否 |
| `--verbose` | `-v` | 详细日志 | 否 |
| `--config` | `-c` | 配置文件 | config.yaml |

## 输出说明

### output/ 目录结构

```
output/
├── original/          # 原文字幕 (*.srt)
│   └── *.srt
│
├── bilingual/        # 双语字幕 (*.srt)
│   └── *.srt
│
├── summary_text/      # 字幕文本总结 (*.md)
│   └── *.md
│
└── summary_video/     # 视觉+字幕联合总结 (*.md) - 后续实现
    └── *.md
```

### 字幕格式

原文字幕 (original/):
```
1
00:00:00,000 --> 00:00:04,440
原文内容
```

双语字幕 (bilingual/):
```
1
00:00:00,000 --> 00:00:04,440
原文内容
译文内容
```

## 性能优化

### 转录速度

```yaml
# 显存不足时
whisper:
  compute_type: "int8"

# 无GPU时
whisper:
  device: "cpu"
```

### 翻译速度

```yaml
llm:
  batch_size: 50  # 增加批处理大小
```

### 内存优化

RTX 4060 Ti (16GB VRAM):
- 推荐: `compute_type: "float16"`, `device: "cuda"`
- 大模型 + float16: ~2GB VRAM
- 中模型 + float16: ~1GB VRAM

## 项目后续计划

- [ ] Web界面 (后端 + 前端Vue)
- [ ] 多语言支持
- [ ] 批量处理
- [ ] ASS特效字幕

## 技术栈

- 转录: Faster-Whisper (CTranslate2加速)
- 翻译: OpenAI API / Ollama / vLLM
- 下载: yt-dlp
- 格式: SRT, VTT

## 许可证

MIT License