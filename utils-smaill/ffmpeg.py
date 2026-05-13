import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

def convert_single_file(filename, input_dir, output_dir, valid_extensions):
    """
    单个文件转换函数，供线程池调用
    """
    if not filename.lower().endswith(valid_extensions):
        return None

    input_path = os.path.join(input_dir, filename)
    file_base = os.path.splitext(filename)[0]
    output_path = os.path.join(output_dir, f"{file_base}.wav")

    # FFmpeg 参数设置
    command = [
        'ffmpeg',
        '-i', input_path,
        '-af', 'highpass=f=100, lowpass=f=8000, loudnorm', 
        '-ar', '16000',
        '-ac', '1',
        '-y',  
        output_path
    ]

    try:
        # 使用 subprocess.run 执行命令
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        return f"成功: {filename}"
    except subprocess.CalledProcessError as e:
        return f"失败: {filename} (错误代码: {e.returncode})"
    except Exception as e:
        return f"异常: {filename} ({str(e)})"

def batch_convert_to_wav_multithreaded(input_dir, output_dir, max_workers=4):
    """
    多线程批量转换
    :param max_workers: 同时运行的线程数，建议设置为 CPU 核心数或稍大
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"提示: 已创建输出目录 -> {output_dir}")

    valid_extensions = ('.mp4', '.mkv', '.flv', '.avi', '.mov')
    
    # 1. 核心：预先对文件列表排序，保证分发顺序一致
    files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith(valid_extensions)])
    
    if not files:
        print("未找到支持的视频文件。")
        return

    print(f"开始并行处理，线程数: {max_workers}")
    print("-" * 30)

    # 2. 使用线程池
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交任务
        future_to_file = {executor.submit(convert_single_file, f, input_dir, output_dir, valid_extensions): f for f in files}
        
        # 3. 按完成顺序打印结果（如果非要按提交顺序打印，可以使用 map）
        # 这里使用 as_completed 可以让你实时看到进度
        for future in as_completed(future_to_file):
            result = future.result()
            if result:
                print(result)

    print("-" * 30 + "\n所有任务处理完成！")

if __name__ == "__main__":
    # 配置路径
    video_source_directory = r"G:\sucai\newVideo"
    audio_output_directory = r"G:\sucai\output"

    # 检查 ffmpeg 是否可用
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        print("错误: 系统找不到 FFmpeg。请确保它已添加到环境变量 Path 中。")
        exit()

    # 执行转换：根据你的 CPU 核心数调整 max_workers，一般 4-8 比较稳妥
    batch_convert_to_wav_multithreaded(video_source_directory, audio_output_directory, max_workers=6)