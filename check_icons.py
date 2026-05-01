#!/usr/bin/env python3
import os
import sys

# 检查图标文件是否存在
icon_files = [
    ('res/icon.png', '256x256'),
    ('res/icon.ico', 'ICO'),
    ('flutter/assets/icon.png', '256x256'),
    ('flutter/assets/logo.png', '300x60'),
]

print("检查图标文件状态:")
all_ok = True
for path, expected in icon_files:
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"  ✓ {path} ({expected}) - {size} bytes")
    else:
        print(f"  ✗ {path} ({expected}) - 文件不存在")
        all_ok = False

if not all_ok:
    print("\n需要修复的图标:")
    # 从 res/icon.png 复制到 flutter/assets/
    if os.path.exists('res/icon.png'):
        if not os.path.exists('flutter/assets/icon.png'):
            print("  - 复制 res/icon.png -> flutter/assets/icon.png")
            with open('res/icon.png', 'rb') as src, open('flutter/assets/icon.png', 'wb') as dst:
                dst.write(src.read())
        
        # 创建 logo.png (需要外部工具处理)
        print("  - 需要创建 flutter/assets/logo.png (300x60)")
        print("    建议使用: convert res/icon.png -resize 300x60 flutter/assets/logo.png")
    sys.exit(1)
else:
    print("\n所有图标文件正常 ✓")