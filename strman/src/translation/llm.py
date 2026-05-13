"""
LLM Translation Module
使用 LLM 进行字幕翻译
"""
import os
import json
import logging
from typing import Iterator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TranslatedSegment:
    """翻译后的字幕片段"""
    index: int
    original: str
    translated: str


class LLMTranslator:
    """LLM 翻译器"""
    
    def __init__(self, config: dict):
        """
        初始化翻译器
        
        Args:
            config: LLM配置
        """
        self.config = config.get('llm', {})
        self.provider = self.config.get('provider', 'openai')
        self.batch_size = self.config.get('batch_size', 20)
        self.temperature = self.config.get('temperature', 0.3)
        
        # 初始化客户端
        self._client = None
        
        if self.provider == 'openai':
            self._init_openai()
        elif self.provider == 'ollama':
            self._init_ollama()
        elif self.provider == 'vllm':
            self._init_vllm()
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _init_openai(self):
        """初始化 OpenAI 客户端"""
        openai_config = self.config.get('openai', {})
        self.base_url = openai_config.get('base_url', 'http://localhost:11434/v1')
        self.api_key = openai_config.get('api_key', 'ollama')
        self.model = openai_config.get('model', 'qwen2.5')
        
        try:
            import openai
            self.openai = openai
            # 兼容不同版本的 openai 库
            self._client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except ImportError:
            # 尝试使用 openai 包
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                raise ImportError("Please install openai: pip install openai")
    
    def _init_ollama(self):
        """初始化 Ollama 客户端"""
        ollama_config = self.config.get('ollama', {})
        self.base_url = ollama_config.get('base_url', 'http://localhost:11434')
        self.model = ollama_config.get('model', 'qwen2.5')
        
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("Please install requests: pip install requests")
        
        self._client = None  # Ollama 使用 requests 直接调用
    
    def _init_vllm(self):
        """初始化 vLLM 客户端 (兼容 OpenAI)"""
        vllm_config = self.config.get('vllm', {})
        self.base_url = vllm_config.get('base_url', 'http://localhost:8000/v1')
        self.api_key = vllm_config.get('api_key', 'EMPTY')
        self.model = vllm_config.get('model', 'qwen2.5')
        
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    def _build_prompt(self, segments: list[str], target_lang: str = "中文") -> str:
        """
        构建翻译提示词
        
        Args:
            segments: 字幕片段列表
            target_lang: 目标语言
            
        Returns:
            翻译提示词
        """
        # 将字幕joining
        text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(segments)])
        
        prompt = f"""请翻译以下字幕片段成{target_lang}。

要求：
1. 保持原文的语气和情感
2. 翻译要自然流畅，符合目标语言习惯
3. 直译不要意译，保留原意
4. 只返回翻译结果，不要返回编号

字幕内容：
{text}

翻译："""
        return prompt
    
    def _parse_translation(self, response: str, count: int) -> list[str]:
        """
        解析翻译结果
        
        Args:
            response: LLM 响应
            count: 预期数量
            
        Returns:
            翻译后的片段列表
        """
        import re
        
        # 移除思考内容标签
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # 移除XML标签
        response = re.sub(r'<.*?>', '', response)
        
        # 移除 "以下is翻译结果：" 类似的前缀说明
        response = re.sub(r'^以下[是为].*?[:：]\s*', '', response, flags=re.MULTILINE)
        
        lines = response.strip().split('\n')
        results = []
        
        for line in lines:
            line = line.strip()
            # 跳过空行
            if not line:
                continue
            # 跳过以 - 或 * 开头的说明行
            if line.startswith('- ') or line.startswith('* '):
                continue
            if line.startswith('#'):
                continue
            # 跳过包含"翻译"的说明行
            if '翻译' in line and '以下' in line:
                continue
            # 移除编号格式 "1. " 或 "1:"
            for prefix in [f"{i+1}. " for i in range(count)]:
                if line.startswith(prefix):
                    line = line[len(prefix):]
                    break
            if line:
                results.append(line.strip())
        
        # 如果解析失败，返回整个响应作为单条
        if not results:
            # 尝试提取引号中的内容
            matches = re.findall(r'["「]([^"」]+)["」]', response)
            if matches:
                results = matches[:count]
            else:
                results = [response.strip()]
        
        return results[:count]
    
    def _translate_openai(self, segments: list[str], target_lang: str = "中文") -> list[str]:
        """使用 OpenAI API 翻译"""
        prompt = self._build_prompt(segments, target_lang)
        
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            # 使用 reasoning_split 分离思考内容
            extra_body={"reasoning_split": True},
        )
        
        # 获取内容（已分离思考内容）
        message = response.choices[0].message
        content = message.content
        
        # 如果 API 返回了 reasoning，直接使用 content
        return self._parse_translation(content, len(segments))
    
    def _translate_ollama(self, segments: list[str], target_lang: str = "中文") -> list[str]:
        """使用 Ollama 翻译"""
        prompt = self._build_prompt(segments, target_lang)
        
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        
        response = self.requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        content = result.get('message', {}).get('content', '')
        return self._parse_translation(content, len(segments))
    
    def translate_batch(
        self,
        segments: list[str],
        target_lang: str = "中文"
    ) -> list[str]:
        """
        批量翻译
        
        Args:
            segments: 字幕片段列表
            target_lang: 目标语言
            
        Returns:
            翻译后的片段列表
        """
        if not segments:
            return []
        
        logger.info(f"Translating {len(segments)} segments to {target_lang}")
        
        if self.provider == 'openai' or self.provider == 'vllm':
            return self._translate_openai(segments, target_lang)
        elif self.provider == 'ollama':
            return self._translate_ollama(segments, target_lang)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def translate_all(
        self,
        original_segments: list[str],
        target_lang: str = "中文",
        show_progress: bool = True
    ) -> list[TranslatedSegment]:
        """
        翻译所有字幕
        
        Args:
            original_segments: 原始字幕列表
            target_lang: 目标语言
            show_progress: 显示进度
            
        Returns:
            翻译后的片段列表
        """
        total = len(original_segments)
        results: list[TranslatedSegment] = []
        
        # 分批翻译
        for i in range(0, total, self.batch_size):
            batch = original_segments[i:i + self.batch_size]
            translations = self.translate_batch(batch, target_lang)
            
            # 确保数量一致
            while len(translations) < len(batch):
                translations.append(batch[len(translations) - len(batch)])
            
            for j, original in enumerate(batch):
                idx = i + j + 1
                translated = translations[j] if j < len(translations) else original
                
                results.append(TranslatedSegment(
                    index=idx,
                    original=original,
                    translated=translated
                ))
            
            if show_progress:
                logger.info(f"Translated {min(i + self.batch_size, total)}/{total}")
        
        logger.info(f"Translation complete: {len(results)} segments")
        return results


def translate_subtitles(
    original_segments: list[str],
    config: dict,
    target_lang: str = "中文"
) -> list[TranslatedSegment]:
    """
    便捷函数：翻译字幕
    
    Args:
        original_segments: 原始字幕列表
        config: 配置字典
        target_lang: 目标语言
        
    Returns:
        翻译后的片段列表
    """
    translator = LLMTranslator(config)
    return translator.translate_all(original_segments, target_lang)