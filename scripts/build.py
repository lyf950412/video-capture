import os
import sys
import subprocess
import shutil


def build_executable():
    print("=" * 50)
    print("CapSure - 打包成可执行程序")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    print(f"\n项目目录: {project_root}")
    
    icon_path = os.path.join(project_root, 'assets', 'icon.ico')
    if not os.path.exists(icon_path):
        print(f"\n警告: 图标文件不存在 {icon_path}")
        print("将使用默认图标")
        icon_path = None
    
    main_script = os.path.join(project_root, 'main.py')
    if not os.path.exists(main_script):
        print(f"\n错误: 找不到主程序文件 {main_script}")
        return False
    
    print("\n正在打包...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=CapSure',
        '--windowed',
        '--onefile',
        '--clean',
        '--noconfirm',
    ]
    
    if icon_path:
        cmd.extend(['--icon', icon_path])
        assets_dir = os.path.join(project_root, 'assets')
        if os.path.exists(assets_dir):
            cmd.extend(['--add-data', f'{assets_dir};assets'])
    
    cmd.append(main_script)
    
    print(f"命令: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        
        dist_path = os.path.join(project_root, 'dist', 'CapSure.exe')
        if os.path.exists(dist_path):
            file_size = os.path.getsize(dist_path) / (1024 * 1024)
            print(f"\n{'=' * 50}")
            print(f"打包成功!")
            print(f"可执行文件: {dist_path}")
            print(f"文件大小: {file_size:.1f} MB")
            print(f"{'=' * 50}")
            return True
        else:
            print("\n错误: 打包完成但未找到可执行文件")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {e}")
        return False
    except Exception as e:
        print(f"\n发生错误: {e}")
        return False


if __name__ == '__main__':
    build_executable()
