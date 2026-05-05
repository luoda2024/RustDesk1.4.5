#!/usr/bin/env python3
"""
RustDesk 图标优化脚本
优化PNG图标文件大小和质量
作者: 小赫 (30年高级编程工程师)
创建时间: 2026-05-01
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional

class IconOptimizer:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        
        # 需要优化的图标文件
        self.icon_files = [
            # 主图标
            self.root_dir / 'res' / 'icon.png',
            self.root_dir / 'res' / 'icon.ico',
            self.root_dir / 'res' / 'tray-icon.ico',
            
            # Flutter 图标
            self.root_dir / 'flutter' / 'assets' / 'icon.png',
            
            # Windows 图标
            self.root_dir / 'flutter' / 'windows' / 'runner' / 'resources' / 'app_icon.ico',
            
            # macOS 图标
            self.root_dir / 'flutter' / 'macos' / 'Runner' / 'AppIcon.icns',
        ]
        
        # 检查工具是否可用
        self.tools = self.check_tools()
    
    def check_tools(self) -> dict:
        """检查优化工具是否可用"""
        tools = {
            'optipng': False,
            'pngquant': False,
            'pngcrush': False,
            'advpng': False,
            'convert': False,  # ImageMagick
            'icotool': False,  # ico工具
        }
        
        for tool in tools.keys():
            try:
                subprocess.run([tool, '--version'], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
                tools[tool] = True
            except (FileNotFoundError, subprocess.CalledProcessError):
                pass
        
        return tools
    
    def get_file_info(self, filepath: Path) -> Optional[dict]:
        """获取文件信息"""
        if not filepath.exists():
            return None
        
        try:
            stat = filepath.stat()
            info = {
                'path': filepath,
                'size_kb': stat.st_size / 1024,
                'exists': True,
                'type': filepath.suffix.lower(),
            }
            
            # 尝试获取图像尺寸
            if filepath.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                if self.tools['convert']:
                    try:
                        result = subprocess.run(
                            ['identify', str(filepath)],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        # 解析输出: icon.png PNG 256x256 256x256+0+0 8-bit sRGB 89KB 0.000u 0:00.000
                        parts = result.stdout.strip().split()
                        if len(parts) >= 3:
                            dimensions = parts[2]
                            if 'x' in dimensions:
                                width, height = dimensions.split('x')
                                info['width'] = int(width)
                                info['height'] = int(height)
                    except:
                        pass
            
            return info
        
        except OSError:
            return None
    
    def optimize_png(self, filepath: Path, backup: bool = True) -> Tuple[bool, str]:
        """优化PNG文件"""
        if not filepath.exists() or filepath.suffix.lower() != '.png':
            return False, "不是PNG文件或文件不存在"
        
        original_size = filepath.stat().st_size
        
        # 创建备份
        if backup:
            backup_path = filepath.with_suffix('.png.bak')
            try:
                subprocess.run(['cp', str(filepath), str(backup_path)], check=True)
            except subprocess.CalledProcessError:
                return False, "创建备份失败"
        
        optimization_steps = []
        
        try:
            # 1. 使用optipng优化（如果可用）
            if self.tools['optipng']:
                cmd = ['optipng', '-o5', '-strip', 'all', str(filepath)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    optimization_steps.append("optipng优化完成")
            
            # 2. 使用pngquant进行有损压缩（如果可用）
            if self.tools['pngquant']:
                # 先复制文件，因为pngquant需要输出到新文件
                temp_path = filepath.with_suffix('.quant.png')
                cmd = ['pngquant', '--quality=80-95', '--speed=1', '--force', 
                      '--output', str(temp_path), str(filepath)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    # 替换原文件
                    subprocess.run(['mv', str(temp_path), str(filepath)], check=True)
                    optimization_steps.append("pngquant压缩完成")
            
            # 3. 使用advpng进一步压缩（如果可用）
            if self.tools['advpng']:
                cmd = ['advpng', '-z4', str(filepath)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    optimization_steps.append("advpng压缩完成")
            
            # 4. 使用pngcrush（如果可用）
            if self.tools['pngcrush']:
                temp_path = filepath.with_suffix('.crush.png')
                cmd = ['pngcrush', '-ow', '-rem', 'alla', '-reduce', str(filepath), str(temp_path)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    subprocess.run(['mv', str(temp_path), str(filepath)], check=True)
                    optimization_steps.append("pngcrush优化完成")
            
            new_size = filepath.stat().st_size
            reduction = ((original_size - new_size) / original_size) * 100
            
            message = f"优化完成: {original_size/1024:.1f}KB → {new_size/1024:.1f}KB "
            message += f"({reduction:.1f}% 减少)"
            if optimization_steps:
                message += f" [步骤: {', '.join(optimization_steps)}]"
            
            return True, message
        
        except subprocess.CalledProcessError as e:
            # 恢复备份
            if backup and backup_path.exists():
                subprocess.run(['mv', str(backup_path), str(filepath)], check=False)
            return False, f"优化失败: {e}"
    
    def check_ico_sizes(self, filepath: Path) -> Tuple[bool, str]:
        """检查ICO文件包含的尺寸"""
        if not filepath.exists() or filepath.suffix.lower() != '.ico':
            return False, "不是ICO文件或文件不存在"
        
        if not self.tools['icotool']:
            return False, "icotool不可用"
        
        try:
            cmd = ['icotool', '-l', str(filepath)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            sizes = []
            for line in result.stdout.split('\n'):
                if 'width' in line.lower() and 'height' in line.lower():
                    # 解析尺寸信息
                    parts = line.split()
                    for part in parts:
                        if 'x' in part and part.replace('x', '').isdigit():
                            sizes.append(part)
            
            if sizes:
                return True, f"包含尺寸: {', '.join(sizes)}"
            else:
                return True, "无法解析尺寸信息"
        
        except subprocess.CalledProcessError:
            return False, "检查失败"
    
    def generate_icon_variants(self) -> List[str]:
        """生成不同尺寸的图标变体"""
        messages = []
        source_icon = self.root_dir / 'res' / 'icon.png'
        
        if not source_icon.exists():
            return ["源图标不存在"]
        
        if not self.tools['convert']:
            return ["ImageMagick (convert) 不可用"]
        
        # 需要生成的尺寸
        sizes = [
            (16, 16, '16x16'),
            (32, 32, '32x32'),
            (48, 48, '48x48'),
            (64, 64, '64x64'),
            (128, 128, '128x128'),
            (256, 256, '256x256'),
            (512, 512, '512x512'),
        ]
        
        output_dir = self.root_dir / 'res' / 'icons'
        output_dir.mkdir(exist_ok=True)
        
        for width, height, name in sizes:
            output_path = output_dir / f'icon_{name}.png'
            
            try:
                cmd = [
                    'convert', str(source_icon),
                    '-resize', f'{width}x{height}',
                    '-unsharp', '1x1',
                    str(output_path)
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                
                # 优化生成的图标
                self.optimize_png(output_path, backup=False)
                
                size_kb = output_path.stat().st_size / 1024
                messages.append(f"生成: {name} ({size_kb:.1f}KB)")
            
            except subprocess.CalledProcessError as e:
                messages.append(f"生成失败 {name}: {e}")
        
        return messages
    
    def create_windows_ico(self) -> Tuple[bool, str]:
        """创建Windows ICO文件（包含多个尺寸）"""
        if not self.tools['convert']:
            return False, "ImageMagick (convert) 不可用"
        
        icon_dir = self.root_dir / 'res' / 'icons'
        if not icon_dir.exists():
            return False, "图标目录不存在，请先运行 --generate-variants"
        
        # 收集所有尺寸的PNG
        png_files = []
        sizes = ['16x16', '32x32', '48x48', '64x64', '128x128', '256x256']
        
        for size in sizes:
            png_path = icon_dir / f'icon_{size}.png'
            if png_path.exists():
                png_files.append(str(png_path))
        
        if not png_files:
            return False, "没有找到PNG图标文件"
        
        # 输出ICO路径
        ico_path = self.root_dir / 'res' / 'luoda.ico'
        
        try:
            # 使用convert创建ICO
            cmd = ['convert'] + png_files + [str(ico_path)]
            subprocess.run(cmd, check=True, capture_output=True)
            
            size_kb = ico_path.stat().st_size / 1024
            return True, f"创建成功: {ico_path} ({size_kb:.1f}KB, 包含 {len(png_files)} 个尺寸)"
        
        except subprocess.CalledProcessError as e:
            return False, f"创建失败: {e}"
    
    def run_optimization(self, backup: bool = True) -> dict:
        """运行优化程序"""
        print("=== RustDesk 图标优化 ===")
        print(f"工作目录: {self.root_dir}")
        print()
        
        # 显示可用工具
        print("可用工具:")
        for tool, available in self.tools.items():
            status = "✅" if available else "❌"
            print(f"  {status} {tool}")
        print()
        
        results = {
            'files_processed': 0,
            'total_savings_kb': 0,
            'optimizations': [],
            'errors': [],
            'warnings': [],
        }
        
        # 处理每个图标文件
        print("处理图标文件:")
        for icon_path in self.icon_files:
            relative_path = icon_path.relative_to(self.root_dir)
            
            info = self.get_file_info(icon_path)
            if not info:
                print(f"  ❌ {relative_path}: 文件不存在")
                continue
            
            print(f"  📄 {relative_path}: {info['size_kb']:.1f}KB", end='')
            
            if 'width' in info and 'height' in info:
                print(f" ({info['width']}x{info['height']})", end='')
            print()
            
            # 根据文件类型处理
            if icon_path.suffix.lower() == '.png':
                if info['size_kb'] > 30:  # 大于30KB需要优化
                    success, message = self.optimize_png(icon_path, backup)
                    if success:
                        results['files_processed'] += 1
                        new_info = self.get_file_info(icon_path)
                        if new_info:
                            savings = info['size_kb'] - new_info['size_kb']
                            results['total_savings_kb'] += savings
                            results['optimizations'].append(
                                f"{relative_path}: {info['size_kb']:.1f}KB → {new_info['size_kb']:.1f}KB "
                                f"(节省 {savings:.1f}KB)"
                            )
                        print(f"    ✅ {message}")
                    else:
                        results['errors'].append(f"{relative_path}: {message}")
                        print(f"    ❌ {message}")
                else:
                    results['warnings'].append(f"{relative_path}: 文件较小 ({info['size_kb']:.1f}KB)，跳过优化")
                    print(f"    ⚠️  文件较小，跳过优化")
            
            elif icon_path.suffix.lower() == '.ico':
                success, message = self.check_ico_sizes(icon_path)
                if success:
                    print(f"    ℹ️  {message}")
                else:
                    print(f"    ⚠️  {message}")
            
            elif icon_path.suffix.lower() == '.icns':
                print(f"    ℹ️  macOS ICNS文件 ({info['size_kb']:.1f}KB)")
        
        # 生成报告
        print(f"\n=== 优化完成 ===")
        print(f"处理文件: {results['files_processed']}")
        print(f"总节省空间: {results['total_savings_kb']:.1f}KB")
        
        if results['optimizations']:
            print("\n优化详情:")
            for opt in results['optimizations']:
                print(f"  ✅ {opt}")
        
        if results['warnings']:
            print("\n警告:")
            for warning in results['warnings']:
                print(f"  ⚠️  {warning}")
        
        if results['errors']:
            print("\n错误:")
            for error in results['errors']:
                print(f"  ❌ {error}")
        
        return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='RustDesk 图标优化工具')
    parser.add_argument('--dir', default='.', help='项目根目录（默认当前目录）')
    parser.add_argument('--no-backup', action='store_true', help='不创建备份文件')
    parser.add_argument('--generate-variants', action='store_true', help='生成不同尺寸的图标变体')
    parser.add_argument('--create-ico', action='store_true', help='创建Windows ICO文件')
    
    args = parser.parse_args()
    
    optimizer = IconOptimizer(args.dir)
    
    if args.generate_variants:
        print("生成图标变体...")
        messages = optimizer.generate_icon_variants()
        for msg in messages:
            print(f"  {msg}")
        return
    
    if args.create_ico:
        print("创建Windows ICO文件...")
        success, message = optimizer.create_windows_ico()
        if success:
            print(f"  ✅ {message}")
        else:
            print(f"  ❌ {message}")
            sys.exit(1)
        return
    
    # 运行优化
    results = optimizer.run_optimization(backup=not args.no_backup)
    
    # 如果有错误，返回非零退出码
    if results['errors']:
        sys.exit(1)


if __name__ == '__main__':
    main()