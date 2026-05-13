"""
GPU 验证脚本
测试 faster-whisper 是否真正使用 GPU
"""
import sys
sys.path.append(r'E:\voiceAi\fastwhisper')

import os
import time

# 添加 CUDA DLL 路径
dll_paths = [
    r'C:\Users\mengxi\.conda\envs\fastwhisper\Lib\site-packages\nvidia\cublas\bin',
    r'C:\Users\mengxi\.conda\envs\fastwhisper\Lib\site-packages\nvidia\cudnn\bin'
]
for p in dll_paths:
    if os.path.exists(p):
        os.add_dll_directory(p)

from faster_whisper import WhisperModel

print("=" * 50)
print("Faster-Whisper GPU 验证测试")
print("=" * 50)

# 加载 CUDA 模型
print("\n加载模型 (device=cuda)...")
start = time.time()
model = WhisperModel(
    r'G:\fastwhisper-model', 
    device='cuda', 
    compute_type='float16'
)
load_time = time.time() - start
print(f"模型加载耗时: {load_time:.2f}秒")

# 转录一个测试音频
test_audio = r"E:\myVsCode\Utils\strMan\temp\���Y�Ǥ����ʡ�һ�����������������ƭ������.wav"
if os.path.exists(test_audio):
    print(f"\n执行转录: {test_audio}")
    segments, info = model.transcribe(test_audio, language="ja")
    
    print(f"\n转录信息:")
    print(f"  - 语言: {info.language} (概率: {info.language_probability:.2f})")
    print(f"  - 持续时间: {info.duration:.2f}秒")
    
    segment_list = list(segments)
    print(f"  - 字幕段数: {len(segment_list)}")
    
    print(f"\n前3条字幕:")
    for i, seg in enumerate(segment_list[:3]):
        print(f"  {i+1}. [{seg.start:.2f}-{seg.end:.2f}] {seg.text}")
else:
    print(f"\n测试音频文件不存在")

print("\n" + "=" * 50)
print("验证完成 - 请检查 GPU 内存使用情况")
print("=" * 50)