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

def create_workflow_link():
    # --- 配置区域 ---
    # 快捷方式所在的目录（ComfyUI 内部工作流位置）
    target_path = r"D:\comfyui\wan2.2\ComfyUI-aki-v2\ComfyUI\user\default\workflows"
    # 实际存放工作流文件的目录（你的资源库位置）
    source_path = r"G:\AiResource\comfyuiResource\workflows\wan2.2"
    # ----------------

    print("="*40)
    print(" Windows 工作流路径映射工具")
    print("="*40)
    
    # 1. 权限检查
    if not is_admin():
        print("[错误] 必须以管理员身份运行此脚本！")
        input("请右键点击 '以管理员身份运行'。按回车键退出..."); return

    # 2. 检查并创建源文件夹 (如果 D:\ComfyUI-Resource\workflow 不存在)
    if not os.path.exists(source_path):
        os.makedirs(source_path)
        print(f" [源目录] 已自动创建工作流资源库: {source_path}")

    # 确保目标路径的父级目录存在 (即 default 文件夹)
    target_parent = os.path.dirname(target_path)
    if not os.path.exists(target_parent):
        os.makedirs(target_parent)
        print(f" [系统] 已创建配置目录: {target_parent}")

    # 3. 处理目标位置是否已存在
    if os.path.exists(target_path) or os.path.islink(target_path):
        print(f"\n>>> 发现现有工作流目录: {target_path}")
        choice = input(f" [询问] 是否删除旧目录并链接到资源库？(y/n): ").lower()
        if choice == 'y':
            try:
                if os.path.islink(target_path) or os.path.isfile(target_path):
                    os.remove(target_path)
                else:
                    shutil.rmtree(target_path)
                print(f" [清理] 已移除旧的工作流目录")
            except Exception as e:
                print(f" [错误] 无法删除文件: {e}")
                input("按回车键退出..."); return
        else:
            print(f" [跳过] 保持原样，不进行链接。")
            input("按回车键退出..."); return

    # 4. 创建符号链接
    try:
        # 创建目录符号链接
        os.symlink(source_path, target_path, target_is_directory=True)
        print(f"\n [成功] 工作流映射已建立！")
        print(f" 映射路径: {target_path} \n 指向: {source_path}")
    except Exception as e:
        print(f" [失败] 创建链接时发生错误: {e}")

    print("\n" + "="*40)
    print(" 处理完毕！")
    input(" 按回车键退出脚本...")

if __name__ == "__main__":
    create_workflow_link()