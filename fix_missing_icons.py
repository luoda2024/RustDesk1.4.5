#!/usr/bin/env python3
"""
修复缺失的图标文件脚本
作者：小赫（30年高级编程工程师）
日期：2026-05-02
"""

import os
import sys
import subprocess
from pathlib import Path

def check_icon_files():
    """检查图标文件是否存在"""
    icon_dir = Path("res")
    required_icons = [
        ("icon.ico", "Windows 应用程序图标"),
        ("icon.png", "通用应用程序图标"),
        ("tray-icon.ico", "系统托盘图标")
    ]
    
    missing = []
    existing = []
    
    print("🔍 检查图标文件...")
    for filename, description in required_icons:
        icon_path = icon_dir / filename
        if icon_path.exists():
            existing.append((filename, description, icon_path))
        else:
            missing.append((filename, description, icon_path))
    
    return existing, missing

def create_placeholder_icon(icon_path, size=256):
    """创建占位图标文件"""
    try:
        # 检查是否安装了 ImageMagick
        result = subprocess.run(["which", "convert"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️ ImageMagick 未安装，无法创建 {icon_path.name}")
            return False
        
        # 创建简单的占位图标
        if icon_path.suffix == '.png':
            cmd = [
                "convert", "-size", f"{size}x{size}", 
                "gradient:blue-red", "-font", "Arial", "-pointsize", "48",
                "-fill", "white", "-gravity", "center",
                "-annotate", "0", "LUODA", str(icon_path)
            ]
        elif icon_path.suffix == '.ico':
            # 创建多个尺寸的 ICO 文件
            sizes = [16, 32, 48, 64, 128, 256]
            temp_files = []
            
            for s in sizes:
                temp_png = f"/tmp/icon_{s}.png"
                cmd = [
                    "convert", "-size", f"{s}x{s}", 
                    "gradient:blue-red", "-font", "Arial", 
                    "-pointsize", str(s//8), "-fill", "white",
                    "-gravity", "center", "-annotate", "0", "LU", temp_png
                ]
                subprocess.run(cmd, check=True)
                temp_files.append(temp_png)
            
            # 合并为 ICO
            cmd = ["convert"] + temp_files + [str(icon_path)]
            subprocess.run(cmd, check=True)
            
            # 清理临时文件
            for temp in temp_files:
                os.unlink(temp)
        else:
            print(f"❓ 不支持的图标格式: {icon_path.suffix}")
            return False
        
        print(f"✅ 创建占位图标: {icon_path}")
        return True
        
    except Exception as e:
        print(f"❌ 创建图标失败: {e}")
        return False

def copy_from_template():
    """从模板复制图标文件"""
    template_dir = Path("res/template")
    if not template_dir.exists():
        print("⚠️ 模板目录不存在，创建中...")
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建示例图标
        create_placeholder_icon(template_dir / "icon.ico")
        create_placeholder_icon(template_dir / "icon.png")
        create_placeholder_icon(template_dir / "tray-icon.ico", size=32)
        
        print("📁 模板图标已创建")
    
    return template_dir

def main():
    print("=" * 60)
    print("LUODA 图标文件修复工具")
    print("=" * 60)
    
    # 检查当前目录
    if not Path("Cargo.toml").exists():
        print("❌ 错误: 请在 rustdesk-custom 目录下运行此脚本")
        sys.exit(1)
    
    # 检查图标文件
    existing, missing = check_icon_files()
    
    if existing:
        print("\n✅ 已存在的图标文件:")
        for filename, description, path in existing:
            size = path.stat().st_size if path.exists() else 0
            print(f"  • {filename} ({description}) - {size:,} bytes")
    
    if missing:
        print(f"\n❌ 缺失 {len(missing)} 个图标文件:")
        for filename, description, path in missing:
            print(f"  • {filename} ({description})")
        
        print("\n🛠️ 开始修复...")
        
        # 询问用户操作
        print("\n请选择操作:")
        print("1. 创建占位图标（使用 ImageMagick）")
        print("2. 从模板复制（如果存在）")
        print("3. 手动处理")
        
        try:
            choice = input("选择 (1-3): ").strip()
            
            if choice == "1":
                # 创建占位图标
                success_count = 0
                for filename, description, path in missing:
                    if create_placeholder_icon(path):
                        success_count += 1
                
                print(f"\n📊 结果: 成功创建 {success_count}/{len(missing)} 个图标")
                
            elif choice == "2":
                # 从模板复制
                template_dir = copy_from_template()
                success_count = 0
                
                for filename, description, path in missing:
                    template_file = template_dir / filename
                    if template_file.exists():
                        import shutil
                        shutil.copy2(template_file, path)
                        print(f"✅ 从模板复制: {filename}")
                        success_count += 1
                    else:
                        print(f"⚠️ 模板文件不存在: {template_file}")
                
                print(f"\n📊 结果: 成功复制 {success_count}/{len(missing)} 个图标")
                
            elif choice == "3":
                print("\n📝 请手动处理以下文件:")
                for filename, description, path in missing:
                    print(f"  • {path}")
                print("\n建议使用专业图标设计工具创建:")
                print("  - Windows ICO: 256x256, 48x48, 32x32, 16x16")
                print("  - PNG: 512x512 透明背景")
                print("  - 系统托盘图标: 32x32 或 16x16")
                
            else:
                print("❌ 无效选择")
                
        except KeyboardInterrupt:
            print("\n⏹️ 用户中断")
            sys.exit(0)
            
    else:
        print("\n🎉 所有图标文件完整！")
    
    # 验证修复结果
    print("\n" + "=" * 60)
    print("验证结果:")
    
    existing, missing = check_icon_files()
    if missing:
        print(f"❌ 仍有 {len(missing)} 个图标缺失:")
        for filename, description, path in missing:
            print(f"  • {filename}")
    else:
        print("✅ 所有图标文件已修复！")
        
        # 显示图标信息
        print("\n📊 图标文件详情:")
        for filename, description, path in existing:
            size = path.stat().st_size
            print(f"  • {filename}: {size:,} bytes")
            
            # 获取图标尺寸
            try:
                result = subprocess.run(
                    ["identify", str(path)], 
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(f"    尺寸: {result.stdout.strip()}")
            except:
                pass
    
    print("\n" + "=" * 60)
    print("修复完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()