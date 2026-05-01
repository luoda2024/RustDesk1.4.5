#!/usr/bin/env python3
"""
RustDesk 品牌化修复脚本
将剩余的 rustdesk 引用替换为 luoda
作者: 小赫 (30年高级编程工程师)
创建时间: 2026-05-01
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

class BrandingFixer:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.replacements = [
            # (pattern, replacement, description)
            (r'rustdesk', 'luoda', '二进制名称'),
            (r'RustDesk', 'LUODA', '应用显示名称'),
            (r'rustdesk\.desktop', 'luoda.desktop', '桌面文件'),
            (r'rustdesk\.service', 'luoda.service', '服务文件'),
            (r'rustdesk-link\.desktop', 'luoda-link.desktop', '链接处理文件'),
        ]
        
        # 排除的目录和文件
        self.exclude_dirs = {
            '.git', 'target', 'build', 'dist', 'node_modules',
            '__pycache__', '.dart_tool', '.idea', '.vscode'
        }
        
        self.exclude_files = {
            'Cargo.lock', 'package-lock.json', 'yarn.lock',
            '*.ico', '*.png', '*.jpg', '*.jpeg', '*.gif', '*.icns'
        }
        
        # 只处理特定扩展名的文件
        self.include_extensions = {
            '.py', '.sh', '.rs', '.dart', '.toml', '.yaml', '.yml',
            '.json', '.md', '.txt', '.desktop', '.service', '.cmake',
            'CMakeLists.txt', 'Makefile', 'Dockerfile'
        }
    
    def should_process_file(self, filepath: Path) -> bool:
        """判断是否应该处理该文件"""
        # 检查是否在排除目录中
        for part in filepath.parts:
            if part in self.exclude_dirs:
                return False
        
        # 检查文件扩展名
        if filepath.suffix not in self.include_extensions and filepath.name not in self.include_extensions:
            return False
        
        # 检查排除的文件名模式
        for pattern in self.exclude_files:
            if filepath.match(pattern):
                return False
        
        return True
    
    def find_files_to_fix(self) -> List[Path]:
        """查找需要修复的文件"""
        files_to_fix = []
        
        for root, dirs, files in os.walk(self.root_dir):
            # 跳过排除的目录
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                filepath = Path(root) / file
                if self.should_process_file(filepath):
                    # 检查文件内容是否包含 rustdesk
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if 'rustdesk' in content.lower():
                                files_to_fix.append(filepath)
                    except (UnicodeDecodeError, PermissionError, OSError):
                        continue
        
        return files_to_fix
    
    def fix_file(self, filepath: Path, dry_run: bool = True) -> Tuple[bool, List[str]]:
        """修复单个文件"""
        changes = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            new_content = original_content
            
            for pattern, replacement, description in self.replacements:
                # 使用正则表达式进行替换，保持大小写敏感
                if pattern == 'rustdesk':
                    # 特殊处理：只替换小写的 rustdesk
                    new_content = re.sub(r'\brustdesk\b', replacement, new_content)
                elif pattern == 'RustDesk':
                    # 特殊处理：只替换大写的 RustDesk
                    new_content = re.sub(r'\bRustDesk\b', replacement, new_content)
                else:
                    # 普通正则替换
                    new_content = re.sub(pattern, replacement, new_content)
            
            if new_content != original_content:
                changes.append(f"修改了 {len(re.findall(r'rustdesk', original_content, re.IGNORECASE))} 处")
                
                if not dry_run:
                    # 备份原文件
                    backup_path = filepath.with_suffix(filepath.suffix + '.bak')
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                    
                    # 写入新内容
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    changes.append(f"已备份到 {backup_path}")
                
                return True, changes
        
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            return False, [f"处理失败: {e}"]
        
        return False, changes
    
    def rename_config_files(self, dry_run: bool = True) -> List[str]:
        """重命名配置文件"""
        changes = []
        config_files = [
            ('rustdesk.desktop', 'luoda.desktop'),
            ('rustdesk-link.desktop', 'luoda-link.desktop'),
            ('rustdesk.service', 'luoda.service'),
        ]
        
        for old_name, new_name in config_files:
            old_path = self.root_dir / 'res' / old_name
            new_path = self.root_dir / 'res' / new_name
            
            if old_path.exists():
                if dry_run:
                    changes.append(f"需要重命名: {old_path} -> {new_path}")
                else:
                    try:
                        old_path.rename(new_path)
                        changes.append(f"已重命名: {old_path} -> {new_path}")
                    except OSError as e:
                        changes.append(f"重命名失败 {old_path}: {e}")
        
        return changes
    
    def optimize_icons(self, dry_run: bool = True) -> List[str]:
        """优化图标文件"""
        changes = []
        icon_files = [
            self.root_dir / 'res' / 'icon.png',
            self.root_dir / 'flutter' / 'assets' / 'icon.png',
        ]
        
        for icon_path in icon_files:
            if icon_path.exists():
                size = icon_path.stat().st_size / 1024  # KB
                if size > 50:  # 大于50KB需要优化
                    if dry_run:
                        changes.append(f"需要优化: {icon_path} ({size:.1f}KB)")
                    else:
                        # 这里可以添加实际的优化命令
                        # 例如: subprocess.run(['optipng', '-o5', str(icon_path)])
                        changes.append(f"应优化: {icon_path} ({size:.1f}KB)")
        
        return changes
    
    def run(self, dry_run: bool = True) -> dict:
        """运行修复程序"""
        print(f"=== RustDesk 品牌化修复 {'(模拟运行)' if dry_run else ''} ===")
        print(f"工作目录: {self.root_dir}")
        print()
        
        results = {
            'files_found': 0,
            'files_fixed': 0,
            'changes': [],
            'errors': []
        }
        
        # 1. 查找需要修复的文件
        print("1. 查找包含 rustdesk 的文件...")
        files_to_fix = self.find_files_to_fix()
        results['files_found'] = len(files_to_fix)
        print(f"   找到 {len(files_to_fix)} 个文件需要修复")
        
        # 2. 修复文件内容
        print("\n2. 修复文件内容...")
        for filepath in files_to_fix:
            relative_path = filepath.relative_to(self.root_dir)
            print(f"   处理: {relative_path}")
            
            fixed, changes = self.fix_file(filepath, dry_run)
            if fixed:
                results['files_fixed'] += 1
                for change in changes:
                    results['changes'].append(f"{relative_path}: {change}")
            elif changes:  # 有错误信息
                results['errors'].append(f"{relative_path}: {changes[0]}")
        
        # 3. 重命名配置文件
        print("\n3. 重命名配置文件...")
        rename_changes = self.rename_config_files(dry_run)
        results['changes'].extend(rename_changes)
        
        # 4. 优化图标
        print("\n4. 检查图标文件...")
        icon_changes = self.optimize_icons(dry_run)
        results['changes'].extend(icon_changes)
        
        # 5. 生成报告
        print("\n5. 生成修复报告...")
        report_path = self.root_dir / 'branding_fix_report.md'
        report = self.generate_report(results, dry_run)
        
        if not dry_run:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            results['changes'].append(f"报告已保存到: {report_path}")
        
        print(f"\n=== 修复完成 ===")
        print(f"找到文件: {results['files_found']}")
        print(f"修复文件: {results['files_fixed']}")
        print(f"错误数量: {len(results['errors'])}")
        
        if dry_run:
            print("\n⚠️  这是模拟运行，实际文件未被修改")
            print("   使用 --apply 参数应用更改")
        
        return results
    
    def generate_report(self, results: dict, dry_run: bool = True) -> str:
        """生成修复报告"""
        report = f"""# RustDesk 品牌化修复报告

**生成时间:** 2026-05-01
**运行模式:** {'模拟运行' if dry_run else '实际执行'}
**工作目录:** {self.root_dir}

## 统计信息
- 找到需要修复的文件: {results['files_found']}
- 成功修复的文件: {results['files_fixed']}
- 错误数量: {len(results['errors'])}

## 详细更改
"""
        
        if results['changes']:
            for change in results['changes']:
                report += f"- {change}\n"
        else:
            report += "无更改\n"
        
        if results['errors']:
            report += "\n## 错误信息\n"
            for error in results['errors']:
                report += f"- ❌ {error}\n"
        
        report += f"""
## 下一步操作

1. **测试构建:** 运行 `cargo build --release` 测试修复后的代码
2. **测试安装:** 在Linux上测试 .desktop 文件是否正确显示
3. **跨平台验证:** 验证所有平台的构建脚本
4. **清理备份:** 删除所有 .bak 备份文件

## 注意事项

- 修复后请重新构建所有平台的可执行文件
- 验证服务文件是否能正常启动
- 检查所有翻译文件的一致性

---
*自动生成 by 小赫的品牌化修复脚本*
"""
        
        return report


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='RustDesk 品牌化修复工具')
    parser.add_argument('--apply', action='store_true', help='实际应用更改（默认是模拟运行）')
    parser.add_argument('--dir', default='.', help='项目根目录（默认当前目录）')
    
    args = parser.parse_args()
    
    fixer = BrandingFixer(args.dir)
    results = fixer.run(dry_run=not args.apply)
    
    # 如果有错误，返回非零退出码
    if results['errors']:
        sys.exit(1)


if __name__ == '__main__':
    main()