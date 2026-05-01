#!/usr/bin/env python3
"""
代码安全审计脚本
作者：小赫（30年高级编程工程师）
日期：2026-05-02
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import json

class CodeSecurityAuditor:
    def __init__(self):
        self.suspicious_patterns = {
            "time_bomb": {
                "patterns": [
                    r'expir(?:y|ation|e)',
                    r'time.*(?:lock|bomb)',
                    r'date.*check',
                    r'valid_until',
                    r'license.*(?:expire|valid)'
                ],
                "description": "时间炸弹或过期检查",
                "severity": "high"
            },
            "feature_lock": {
                "patterns": [
                    r'feature.*(?:disable|enable|lock)',
                    r'premium.*only',
                    r'功能.*限制',
                    r'限制.*功能',
                    r'cripple.*feature'
                ],
                "description": "功能限制或锁定",
                "severity": "high"
            },
            "telemetry": {
                "patterns": [
                    r'telemetry',
                    r'phoning.*home',
                    r'call.*home',
                    r'analytics.*send',
                    r'usage.*track'
                ],
                "description": "遥测数据收集",
                "severity": "medium"
            },
            "backdoor": {
                "patterns": [
                    r'backdoor',
                    r'hidden.*feature',
                    r'easter.*egg',
                    r'debug.*mode.*always',
                    r'admin.*bypass'
                ],
                "description": "后门或隐藏功能",
                "severity": "critical"
            },
            "license_check": {
                "patterns": [
                    r'license.*check',
                    r'validate.*license',
                    r'activation.*required',
                    r'key.*validation'
                ],
                "description": "许可证检查",
                "severity": "medium"
            },
            "watermark": {
                "patterns": [
                    r'watermark',
                    r'branding.*enforce',
                    r'强制.*品牌',
                    r'品牌.*强制'
                ],
                "description": "水印或强制品牌",
                "severity": "low"
            }
        }
        
        self.whitelist_patterns = [
            r'expir',  # 在验证码过期消息中是正常的
            r'license',  # 许可证文件引用
            r'feature',  # 功能标志
        ]
        
        self.findings = []
    
    def is_whitelisted(self, line: str) -> bool:
        """检查是否在白名单中"""
        for pattern in self.whitelist_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # 检查是否是正常的验证码过期消息
                if 'verification code' in line.lower() and 'expired' in line.lower():
                    return True
                # 检查是否是许可证文件引用
                if 'license' in line.lower() and 'file' in line.lower():
                    return True
        return False
    
    def scan_file(self, file_path: Path) -> List[Dict]:
        """扫描单个文件"""
        findings = []
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # 跳过注释行
                stripped = line.strip()
                if stripped.startswith('//') or stripped.startswith('#'):
                    continue
                
                # 检查白名单
                if self.is_whitelisted(line):
                    continue
                
                # 检查所有可疑模式
                for category, info in self.suspicious_patterns.items():
                    for pattern in info['patterns']:
                        if re.search(pattern, line, re.IGNORECASE):
                            finding = {
                                'file': str(file_path),
                                'line': line_num,
                                'category': category,
                                'description': info['description'],
                                'severity': info['severity'],
                                'pattern': pattern,
                                'code': line.strip(),
                                'context': self.get_context(lines, line_num)
                            }
                            findings.append(finding)
                            break  # 每个类别只记录一次
        
        except Exception as e:
            print(f"❌ 扫描失败 {file_path}: {e}")
        
        return findings
    
    def get_context(self, lines: List[str], line_num: int, context_lines: int = 2) -> str:
        """获取代码上下文"""
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        
        context = []
        for i in range(start, end):
            prefix = '>>> ' if i == line_num - 1 else '    '
            context.append(f"{prefix}{i+1}: {lines[i]}")
        
        return '\n'.join(context)
    
    def scan_directory(self, directory: str = "src") -> Dict:
        """扫描目录"""
        print(f"🔍 扫描目录: {directory}")
        
        src_dir = Path(directory)
        if not src_dir.exists():
            print(f"❌ 目录不存在: {directory}")
            return {}
        
        # 查找 Rust 文件
        rust_files = list(src_dir.rglob("*.rs"))
        print(f"📁 找到 {len(rust_files)} 个 Rust 文件")
        
        total_findings = []
        for i, file_path in enumerate(rust_files, 1):
            print(f"  [{i}/{len(rust_files)}] 扫描: {file_path.relative_to(src_dir)}", end='\r')
            
            findings = self.scan_file(file_path)
            total_findings.extend(findings)
        
        print()  # 换行
        
        return {
            'directory': directory,
            'files_scanned': len(rust_files),
            'findings': total_findings,
            'findings_by_severity': self.group_by_severity(total_findings),
            'findings_by_category': self.group_by_category(total_findings)
        }
    
    def group_by_severity(self, findings: List[Dict]) -> Dict:
        """按严重程度分组"""
        groups = {}
        for finding in findings:
            severity = finding['severity']
            if severity not in groups:
                groups[severity] = []
            groups[severity].append(finding)
        return groups
    
    def group_by_category(self, findings: List[Dict]) -> Dict:
        """按类别分组"""
        groups = {}
        for finding in findings:
            category = finding['category']
            if category not in groups:
                groups[category] = []
            groups[category].append(finding)
        return groups
    
    def print_report(self, results: Dict):
        """打印报告"""
        print("\n" + "=" * 80)
        print("代码安全审计报告")
        print("=" * 80)
        
        print(f"📊 扫描统计:")
        print(f"  目录: {results.get('directory', 'N/A')}")
        print(f"  扫描文件数: {results.get('files_scanned', 0)}")
        print(f"  发现的问题: {len(results.get('findings', []))}")
        
        findings_by_severity = results.get('findings_by_severity', {})
        for severity in ['critical', 'high', 'medium', 'low']:
            count = len(findings_by_severity.get(severity, []))
            if count > 0:
                print(f"  {severity.upper()}: {count}")
        
        print("\n🔍 详细发现:")
        
        # 按严重程度排序显示
        for severity in ['critical', 'high', 'medium', 'low']:
            findings = findings_by_severity.get(severity, [])
            if findings:
                print(f"\n{'='*40}")
                print(f"{severity.upper()} 级别 ({len(findings)} 个):")
                print('='*40)
                
                for i, finding in enumerate(findings, 1):
                    print(f"\n{i}. [{finding['category']}] {finding['description']}")
                    print(f"   文件: {finding['file']}:{finding['line']}")
                    print(f"   代码: {finding['code']}")
                    print(f"   上下文:\n{finding['context']}")
        
        # 按类别统计
        print("\n📈 按类别统计:")
        findings_by_category = results.get('findings_by_category', {})
        for category, findings in findings_by_category.items():
            print(f"  {category}: {len(findings)} 个")
        
        # 建议
        print("\n💡 建议:")
        if findings_by_severity.get('critical') or findings_by_severity.get('high'):
            print("  ⚠️ 发现高危问题，建议立即审查和修复")
        elif findings_by_severity.get('medium'):
            print("  🔍 发现中危问题，建议在下一个版本中修复")
        else:
            print("  ✅ 未发现严重安全问题")
        
        print("\n" + "=" * 80)
    
    def save_report(self, results: Dict, output_file: str = "security_audit_report.json"):
        """保存报告到文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"📄 报告已保存: {output_file}")
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")

def main():
    print("🔒 LUODA 代码安全审计工具")
    print("=" * 60)
    
    auditor = CodeSecurityAuditor()
    
    # 扫描 src 目录
    results = auditor.scan_directory("src")
    
    if results:
        auditor.print_report(results)
        
        # 询问是否保存报告
        save = input("\n💾 是否保存详细报告到文件? (y/n): ").strip().lower()
        if save == 'y':
            auditor.save_report(results)
    
    print("\n✅ 审计完成！")

if __name__ == "__main__":
    main()