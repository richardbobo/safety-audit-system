#!/usr/bin/env python3
"""
安全智能审核系统 - 安全检查脚本
用于检查项目中是否存在硬编码的敏感信息
"""

import os
import re
import sys
from pathlib import Path

# 敏感信息模式
SENSITIVE_PATTERNS = [
    r'sk-[a-zA-Z0-9]{32,}',  # API密钥模式
    r'api[._-]?key\s*[:=]\s*["\'].*["\']',  # API密钥赋值
    r'password\s*[:=]\s*["\'].*["\']',  # 密码
    r'secret\s*[:=]\s*["\'].*["\']',  # 密钥
    r'token\s*[:=]\s*["\'].*["\']',  # 令牌
]

def check_file(file_path):
    """检查单个文件是否包含敏感信息"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        for i, line in enumerate(content.splitlines(), 1):
            for pattern in SENSITIVE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'line': i,
                        'content': line.strip(),
                        'pattern': pattern
                    })
                    break  # 一行只报告一个问题
    
    except Exception as e:
        print(f"  警告：无法读取文件 {file_path}: {e}")
    
    return issues

def main():
    print("安全智能审核系统 - 安全检查")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    print(f"检查目录: {project_root}")
    print()
    
    # 要检查的文件类型
    file_extensions = ['.py', '.js', '.html', '.bat', '.sh', '.json', '.yml', '.yaml', '.txt']
    
    issues_found = False
    
    for ext in file_extensions:
        for file_path in project_root.rglob(f'*{ext}'):
            # 跳过一些不需要检查的目录
            if any(part.startswith('.') for part in file_path.parts):
                continue
            if any(part in ['__pycache__', 'node_modules', 'venv', 'env'] for part in file_path.parts):
                continue
            
            issues = check_file(file_path)
            if issues:
                issues_found = True
                print(f"警告: 发现问题的文件: {file_path.relative_to(project_root)}")
                for issue in issues:
                    print(f"   第{issue['line']}行: {issue['content'][:80]}...")
                print()
    
    # 检查.env文件是否存在
    env_file = project_root / '.env'
    if env_file.exists():
        print("找到.env文件（建议不要提交到版本控制）")
    else:
        print("未找到.env文件，建议创建.env文件管理敏感信息")
    
    # 检查.gitignore是否包含.env
    gitignore_file = project_root / '.gitignore'
    if gitignore_file.exists():
        with open(gitignore_file, 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
        if '.env' in gitignore_content:
            print(".gitignore已包含.env文件")
        else:
            print("警告: .gitignore未包含.env文件，建议添加")
    else:
        print("警告: 未找到.gitignore文件，建议创建")
    
    print()
    print("=" * 50)
    
    if issues_found:
        print("发现潜在的安全问题！")
        print("建议：")
        print("1. 移除硬编码的敏感信息")
        print("2. 使用环境变量或配置文件管理敏感信息")
        print("3. 确保.gitignore包含敏感文件")
        return 1
    else:
        print("安全检查通过！")
        print("建议：")
        print("1. 定期运行此脚本检查安全配置")
        print("2. 不要将包含敏感信息的文件提交到版本控制")
        print("3. 使用环境变量管理API密钥等敏感信息")
        return 0

if __name__ == '__main__':
    sys.exit(main())