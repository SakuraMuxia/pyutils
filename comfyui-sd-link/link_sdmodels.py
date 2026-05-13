import os
import sys
import ctypes
import shutil

def is_admin():
    """检查是否拥有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def create_model_links():
    # --- 配置区域 ---
    # 快捷方式/链接所在的目录（目标位置 - 即将创建“虚身”的地方）
    target_base_dir = r"D:\stableDiffusion\sd-webui-aki-v4.11.1-cu128\models"
    # 实际存放文件的目录（源位置 - 真实数据存放地）
    source_base_dir = r"D:\stableDiffusionResource\models"
    
    # 需要处理的文件夹列表
    folders_to_link = [
        "checkpoint", "ControlNet", "embeddings", "Lora",
        "vae", "vae-approx","Stable-diffusion"
    ]
    # ----------------

    print("="*60)
    print(" Windows 模型路径映射工具")
    print(f" [目标端]: {target_base_dir}")
    print(f" [源端端]: {source_base_dir}")
    print("="*60)
    
    if not is_admin():
        print("[错误] 必须以管理员身份运行此脚本！")
        input("请右键点击 '以管理员身份运行'。按回车键退出..."); return

    for base in [target_base_dir, source_base_dir]:
        if not os.path.exists(base):
            os.makedirs(base)
            print(f"[系统] 已创建基础目录: {base}")

    for folder in folders_to_link:
        target_path = os.path.join(target_base_dir, folder)
        source_path = os.path.join(source_base_dir, folder)

        print(f"\n>>> 任务: 处理子文件夹 [{folder}]")

        # 1. 源文件夹处理
        if not os.path.exists(source_path):
            os.makedirs(source_path)
            print(f" [源位置] 自动创建了缺失的源文件夹: {source_path}")
        else:
            print(f" [源位置] 确认存在: {source_path}")

        # 2. 目标文件夹处理 (核心修改点)
        if os.path.exists(target_path) or os.path.islink(target_path):
            print(f" [警告] 发现冲突！")
            print(f"        位置: 【目标端 - TARGET】")
            print(f"        路径: {target_path}")
            
            choice = input(f" [询问] 是否删除上述【目标端】的文件夹以建立链接？(y/n): ").lower()
            
            if choice == 'y':
                try:
                    if os.path.islink(target_path) or os.path.isfile(target_path):
                        os.remove(target_path)
                    else:
                        shutil.rmtree(target_path)
                    print(f" [清理] 已成功删除【目标端】的旧文件夹。")
                except Exception as e:
                    print(f" [错误] 无法删除目标文件夹: {e}")
                    continue
            else:
                print(f" [跳过] 用户选择保留【目标端】原始文件，未建立链接。")
                continue

        # 3. 创建链接
        try:
            os.symlink(source_path, target_path, target_is_directory=True)
            print(f" [完成] 链接成功: 【目标端】已指向【源端】")
        except Exception as e:
            print(f" [失败] 创建链接出错: {e}")

    print("\n" + "="*60)
    print(" 所有映射任务处理完毕！")
    input(" 按回车键退出脚本...")

if __name__ == "__main__":
    create_model_links()