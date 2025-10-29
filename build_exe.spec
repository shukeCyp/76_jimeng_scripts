# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller规范文件
用于将WebView应用打包成独立的exe文件
"""

import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# 收集static文件夹
datas = [
    (os.path.join(os.path.dirname(__file__), 'app', 'static'), 'app/static')
]

a = Analysis(
    [os.path.join(os.path.dirname(__file__), 'app', 'main.py')],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['pywebview.api'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WebViewApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口，改为True可调试
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 可选：创建单个文件
# 如果希望生成单个exe文件，取消注释下面的代码并注释掉上面的exe配置
# exe = EXE(
#     pyz,
#     a.scripts,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     [],
#     name='WebViewApp',
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     runtime_tmpdir=None,
#     console=False,
#     target_arch=None,
#     codesign_identity=None,
#     entitlements_file=None,
#     onefile=True,  # 生成单个文件
# )
