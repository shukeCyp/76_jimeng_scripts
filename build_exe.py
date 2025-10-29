#!/usr/bin/env python3
"""
PyInstaller打包脚本
用于将WebView应用打包成exe文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


class PyInstallerBuilder:
    """PyInstaller构建器类"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.app_dir = self.project_root / 'app'
        self.static_dir = self.app_dir / 'static'
        self.dist_dir = self.project_root / 'dist'
        self.build_dir = self.project_root / 'build'
        self.spec_file = self.project_root / 'build_exe.spec'

    def check_dependencies(self):
        """检查必要的依赖"""
        print("=" * 50)
        print("检查依赖...")
        print("=" * 50)

        try:
            import PyInstaller
            print(f"✓ PyInstaller 已安装: {PyInstaller.__version__}")
        except ImportError:
            print("✗ PyInstaller 未安装")
            print("  请运行: pip install -r requirements.txt")
            return False

        try:
            import webview
            print(f"✓ pywebview 已安装")
        except ImportError:
            print("✗ pywebview 未安装")
            print("  请运行: pip install -r requirements.txt")
            return False

        return True

    def check_files(self):
        """检查必要的文件"""
        print("\n" + "=" * 50)
        print("检查文件...")
        print("=" * 50)

        files_to_check = [
            (self.app_dir / 'main.py', '主程序文件'),
            (self.static_dir / 'index.html', 'HTML文件'),
            (self.static_dir / 'styles.css', 'CSS文件'),
            (self.static_dir / 'script.js', 'JavaScript文件'),
        ]

        all_exist = True
        for file_path, description in files_to_check:
            if file_path.exists():
                print(f"✓ {description}: {file_path}")
            else:
                print(f"✗ {description} 不存在: {file_path}")
                all_exist = False

        return all_exist

    def clean_build_files(self):
        """清理之前的构建文件"""
        print("\n" + "=" * 50)
        print("清理旧的构建文件...")
        print("=" * 50)

        dirs_to_remove = [self.dist_dir, self.build_dir]

        for dir_path in dirs_to_remove:
            if dir_path.exists():
                print(f"删除目录: {dir_path}")
                shutil.rmtree(dir_path)

        # 删除 .spec 生成的缓存
        for file_path in self.project_root.glob('*.pyc'):
            if file_path.is_file():
                file_path.unlink()

    def build(self, onefile=False, console=False):
        """执行构建"""
        print("\n" + "=" * 50)
        print("开始打包...")
        print("=" * 50)

        # 构建命令
        cmd = [
            sys.executable,
            '-m', 'PyInstaller',
            '--distpath', str(self.dist_dir),
            '--buildpath', str(self.build_dir),
            '--specpath', str(self.project_root),
        ]

        # 添加静态文件
        cmd.extend([
            '--add-data',
            f'{self.static_dir}{os.pathsep}app/static'
        ])

        # 隐藏导入
        cmd.extend([
            '--hidden-import', 'pywebview.api',
        ])

        # 设置输出文件名
        cmd.extend([
            '--name', 'WebViewApp',
        ])

        # 控制台选项
        if not console:
            cmd.append('--windowed')

        # 单文件选项
        if onefile:
            cmd.append('--onefile')
            print("模式: 单个exe文件（更大但易于分发）")
        else:
            print("模式: 目录模式（更快，包含多个文件）")

        # 添加主程序
        cmd.append(str(self.app_dir / 'main.py'))

        print(f"\n执行命令: {' '.join(cmd)}\n")

        # 执行打包
        try:
            result = subprocess.run(cmd, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"✗ 打包失败: {e}")
            return False

    def print_result(self, success):
        """打印结果"""
        print("\n" + "=" * 50)
        if success:
            print("✓ 打包成功!")
            print("=" * 50)
            print(f"\n输出位置:")
            print(f"  {self.dist_dir}/WebViewApp/")
            print(f"\n运行应用:")
            if sys.platform == 'win32':
                print(f"  {self.dist_dir}/WebViewApp/WebViewApp.exe")
            else:
                print(f"  {self.dist_dir}/WebViewApp/WebViewApp")
        else:
            print("✗ 打包失败!")
            print("=" * 50)
            print("\n请检查:")
            print("  1. 所有依赖是否已安装")
            print("  2. 所有文件是否存在")
            print("  3. Python版本是否兼容")

    def run(self, onefile=False, console=False):
        """运行完整的构建流程"""
        print("\n")
        print("╔" + "=" * 48 + "╗")
        print("║" + " WebView 应用打包工具 ".center(48) + "║")
        print("╚" + "=" * 48 + "╝")

        # 检查依赖
        if not self.check_dependencies():
            self.print_result(False)
            return False

        # 检查文件
        if not self.check_files():
            self.print_result(False)
            return False

        # 清理旧文件
        self.clean_build_files()

        # 执行构建
        success = self.build(onefile=onefile, console=console)

        # 打印结果
        self.print_result(success)

        return success


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='WebView应用打包工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python build_exe.py              # 生成目录模式（推荐）
  python build_exe.py --onefile    # 生成单个exe文件
  python build_exe.py --console    # 显示控制台窗口（调试用）
        '''
    )

    parser.add_argument(
        '--onefile',
        action='store_true',
        help='生成单个exe文件（文件较大但易于分发）'
    )

    parser.add_argument(
        '--console',
        action='store_true',
        help='显示控制台窗口（用于调试）'
    )

    args = parser.parse_args()

    builder = PyInstallerBuilder()
    success = builder.run(onefile=args.onefile, console=args.console)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
