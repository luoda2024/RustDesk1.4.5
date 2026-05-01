#!/usr/bin/env python3
"""
批量更新文档中的 rustdesk.com 链接
作者：小赫（30年高级编程工程师）
日期：2026-05-02
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

def find_document_files() -> List[Path]:
    """查找所有文档文件"""
    doc_extensions = {'.md', '.txt', '.rst', '.adoc', '.asciidoc'}
    doc_files = []
    
    # 搜索 docs 目录
    docs_dir = Path("docs")
    if docs_dir.exists():
        for ext in doc_extensions:
            for file in docs_dir.rglob(f"*{ext}"):
                doc_files.append(file)
    
    # 搜索根目录的文档文件
    for ext in doc_extensions:
        for file in Path(".").glob(f"*{ext}"):
            if file.name not in ["README.md", "CONTRIBUTING.md"]:
                doc_files.append(file)
    
    return doc_files

def find_rustdesk_links(content: str) -> List[Tuple[str, str]]:
    """查找 rustdesk.com 链接"""
    patterns = [
        # HTTP/HTTPS 链接
        r'https?://(?:www\.)?rustdesk\.com[^\s\)\]]*',
        # Markdown 链接
        r'\[([^\]]+)\]\(https?://(?:www\.)?rustdesk\.com[^\)]*\)',
        # 纯文本链接
        r'rustdesk\.com(?:/[^\s\)\]]*)?',
    ]
    
    links = []
    for pattern in patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            links.append((match.group(), match.start(), match.end()))
    
    return links

def replace_rustdesk_links(content: str) -> Tuple[str, int]:
    """替换 rustdesk.com 链接为 luoda.cn"""
    replacements = {
        # 主域名替换
        'rustdesk.com': 'luoda.cn',
        'www.rustdesk.com': 'www.luoda.cn',
        
        # 特定页面替换
        'rustdesk.com/pricing.html': 'luoda.cn/pricing',
        'rustdesk.com/server': 'luoda.cn/server',
        'rustdesk.com/docs': 'luoda.cn/docs',
        'rustdesk.com/blog': 'luoda.cn/blog',
        
        # GitHub 仓库链接
        'github.com/rustdesk/rustdesk': 'github.com/luoda-org/luoda',
        'github.com/rustdesk/rustdesk-server': 'github.com/luoda-org/luoda-server',
        'github.com/rustdesk/rustdesk-server-demo': 'github.com/luoda-org/luoda-server-demo',
        'github.com/rustdesk/doc.rustdesk.com': 'github.com/luoda-org/docs.luoda.cn',
    }
    
    replaced_count = 0
    new_content = content
    
    # 先处理特定的替换
    for old, new in replacements.items():
        if old in new_content:
            count = new_content.count(old)
            new_content = new_content.replace(old, new)
            replaced_count += count
            print(f"   替换: {old} → {new} ({count} 处)")
    
    return new_content, replaced_count

def process_file(file_path: Path, dry_run: bool = False) -> int:
    """处理单个文件"""
    print(f"📄 处理: {file_path}")
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        # 查找链接
        links = find_rustdesk_links(content)
        if not links:
            print(f"  ✓ 无 rustdesk.com 链接")
            return 0
        
        print(f"  🔍 找到 {len(links)} 个链接")
        
        # 显示部分链接
        for link, start, end in links[:3]:
            context_start = max(0, start - 30)
            context_end = min(len(content), end + 30)
            context = content[context_start:context_end]
            print(f"    • {link}")
            print(f"      上下文: ...{context}...")
        
        if len(links) > 3:
            print(f"    ... 还有 {len(links)-3} 个链接")
        
        if dry_run:
            print(f"  🧪 模拟运行: 将替换 {len(links)} 个链接")
            return len(links)
        
        # 执行替换
        new_content, replaced_count = replace_rustdesk_links(content)
        
        if replaced_count > 0:
            # 备份原文件
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            if not backup_path.exists():
                file_path.rename(backup_path)
            
            # 写入新内容
            file_path.write_text(new_content, encoding='utf-8')
            print(f"  ✅ 替换完成: {replaced_count} 处")
            
            # 验证替换
            verify_content = file_path.read_text(encoding='utf-8', errors='ignore')
            remaining = find_rustdesk_links(verify_content)
            if remaining:
                print(f"  ⚠️ 警告: 仍有 {len(remaining)} 个链接未替换")
            else:
                print(f"  🎉 验证通过: 所有链接已替换")
            
            return replaced_count
        else:
            print(f"  ⚠️ 未进行替换")
            return 0
            
    except Exception as e:
        print(f"  ❌ 处理失败: {e}")
        return 0

def main():
    print("=" * 70)
    print("LUODA 文档链接批量更新工具")
    print("=" * 70)
    
    # 检查参数
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    if dry_run:
        print("🧪 模拟运行模式 (不实际修改文件)")
    
    # 查找文档文件
    print("\n🔍 搜索文档文件...")
    doc_files = find_document_files()
    
    if not doc_files:
        print("❌ 未找到文档文件")
        sys.exit(1)
    
    print(f"📁 找到 {len(doc_files)} 个文档文件")
    
    # 统计信息
    total_files = 0
    total_links = 0
    total_replaced = 0
    
    # 处理文件
    print("\n🔄 开始处理...")
    for file_path in doc_files:
        links_found = len(find_rustdesk_links(file_path.read_text(encoding='utf-8', errors='ignore')))
        if links_found > 0:
            total_files += 1
            total_links += links_found
            replaced = process_file(file_path, dry_run)
            total_replaced += replaced
            print()
    
    # 输出统计
    print("=" * 70)
    print("📊 处理统计:")
    print(f"  扫描文件数: {len(doc_files)}")
    print(f"  包含链接的文件: {total_files}")
    print(f"  发现的链接数: {total_links}")
    
    if dry_run:
        print(f"  模拟替换数: {total_replaced}")
        print("\n💡 提示: 使用不带 --dry-run 的参数实际执行替换")
    else:
        print(f"  实际替换数: {total_replaced}")
        
        if total_replaced > 0:
            print("\n✅ 替换完成！")
            
            # 建议后续操作
            print("\n📝 建议后续操作:")
            print("1. 使用 git diff 检查更改")
            print("2. 测试文档中的链接是否有效")
            print("3. 更新 README.md 中的链接")
            print("4. 提交更改到版本控制")
        else:
            print("\nℹ️ 未进行任何替换")
    
    print("\n" + "=" * 70)
    print("工具完成！")
    print("=" * 70)

if __name__ == "__main__":
    main()