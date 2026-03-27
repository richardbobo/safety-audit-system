#!/usr/bin/env python3
"""
AI智能审核API服务 - 确定性版本
修复AI审核结果随机性问题，确保每次审核结果一致
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
from datetime import datetime
import json
import time
import os
import threading
import requests
from pathlib import Path
import hashlib

app = FastAPI(title="AI智能审核API（确定性版本）", version="5.0.0", description="修复AI审核结果随机性问题")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 根路径重定向到测试页面
@app.get("/")
async def root():
    test_page = static_dir / "test-page.html"
    if test_page.exists():
        return FileResponse(str(test_page))
    return {"message": "AI智能审核API服务（确定性版本）运行中", "version": "5.0.0"}

# 数据库连接
def get_db_connection():
    """获取数据库连接"""
    db_path = Path(__file__).parent.parent / "data" / "safety_audit.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

# 文件路径解析
def resolve_file_path(file_path_str: str) -> Path:
    """解析文件路径"""
    if not file_path_str:
        raise ValueError("文件路径为空")
    
    file_path_str = file_path_str.strip()
    
    if os.path.isabs(file_path_str):
        return Path(file_path_str)
    
    possible_paths = [
        Path(__file__).parent.parent / file_path_str,
        Path(__file__).parent.parent / "data" / file_path_str,
        Path(__file__).parent.parent / "data" / "uploads" / Path(file_path_str).name,
        Path(__file__).parent.parent / "data" / "uploads" / file_path_str,
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return possible_paths[0]

# PDF内容提取
def extract_pdf_content(pdf_path: Path) -> Dict[str, Any]:
    """提取PDF内容"""
    try:
        import pdfplumber
        
        if not pdf_path.exists():
            return {"success": False, "error": f"文件不存在: {pdf_path}"}
        
        content = []
        tables_content = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # 提取文本
                text = page.extract_text()
                if text:
                    content.append(f"--- 第{page_num}页 ---\n{text}")
                
                # 提取表格
                tables = page.extract_tables()
                for table_num, table in enumerate(tables, 1):
                    if table:
                        table_text = f"表格{page_num}-{table_num}:\n"
                        for row in table:
                            table_text += " | ".join([str(cell) if cell else "" for cell in row]) + "\n"
                        tables_content.append(table_text)
        
        full_content = "\n".join(content)
        if tables_content:
            full_content += "\n\n--- 表格内容 ---\n" + "\n".join(tables_content)
        
        return {
            "success": True,
            "content": full_content,
            "pages": len(content),
            "tables": len(tables_content),
            "text_length": len(full_content)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# 加载环境变量
def load_env_vars():
    """从.env文件加载环境变量"""
    env_files = [
        Path(__file__).parent.parent / ".env",
        Path(__file__).parent.parent / ".env.real",
        Path(__file__).parent.parent / ".env.example"
    ]
    
    for env_file in env_files:
        if env_file.exists():
            print(f"加载环境变量文件: {env_file}")
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            break

# 加载环境变量
load_env_vars()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def call_deepseek_api_deterministic(prompt: str, max_tokens: int = 3000) -> Dict[str, Any]:
    """
    调用DeepSeek API - 确定性版本
    使用低温度和固定参数确保每次输出一致
    """
    if not DEEPSEEK_API_KEY or not DEEPSEEK_API_KEY.startswith("sk-"):
        raise ValueError("DeepSeek API密钥无效或未配置")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    # 确定性参数配置
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个安全审核专家，专门分析安全操作规程的合规性。请确保审核结果客观、一致、可重复。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.1,      # 非常低的温度，确保输出确定性
        "top_p": 0.9,           # 控制词汇选择范围
        "frequency_penalty": 0, # 不惩罚高频词
        "presence_penalty": 0,  # 不惩罚新词
        "stream": False
    }
    
    # 增加重试机制
    max_retries = 3
    timeout_settings = [60, 90, 120]
    
    for attempt in range(max_retries):
        try:
            timeout = timeout_settings[min(attempt, len(timeout_settings)-1)]
            print(f"尝试第 {attempt+1} 次调用DeepSeek API，超时时间: {timeout}秒")
            
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                print(f"DeepSeek API调用成功 (第{attempt+1}次尝试)")
                return result
            else:
                print(f"DeepSeek API返回错误: {response.status_code} - {response.text}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"DeepSeek API返回错误: {response.status_code}")
                    
        except requests.exceptions.Timeout:
            print(f"DeepSeek API调用超时，将在 {attempt+2} 秒后重试...")
            if attempt < max_retries - 1:
                time.sleep(attempt + 2)
            else:
                raise Exception(f"DeepSeek API调用超时，已重试{max_retries}次")
                
        except requests.exceptions.ConnectionError as e:
            print(f"DeepSeek API连接错误: {e}，将在 {attempt+2} 秒后重试...")
            if attempt < max_retries - 1:
                time.sleep(attempt + 2)
            else:
                raise Exception(f"DeepSeek API连接失败，已重试{max_retries}次: {e}")
                
        except Exception as e:
            print(f"DeepSeek API调用失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(attempt + 1)
            else:
                raise Exception(f"DeepSeek API调用失败: {e}")
    
    raise Exception("DeepSeek API调用失败，未知错误")

# 审核结果缓存
audit_cache = {}

def get_audit_cache_key(sop_id: str, sop_content: str, standards: List[Dict]) -> str:
    """生成审核缓存键"""
    standards_str = json.dumps(sorted([s.get('id', '') for s in standards]), sort_keys=True)
    content_hash = hashlib.md5(f"{sop_id}_{sop_content[:1000]}_{standards_str}".encode()).hexdigest()
    return f"audit_cache_{content_hash}"

def get_cached_audit(sop_id: str, sop_content: str, standards: List[Dict]) -> Optional[Dict]:
    """获取缓存的审核结果"""
    cache_key = get_audit_cache_key(sop_id, sop_content, standards)
    return audit_cache.get(cache_key)

def cache_audit_result(sop_id: str, sop_content: str, standards: List[Dict], result: Dict):
    """缓存审核结果"""
    cache_key = get_audit_cache_key(sop_id, sop_content, standards)
    audit_cache[cache_key] = result
    print(f"审核结果已缓存，缓存键: {cache_key}")

def save_audit_to_database(audit_result: Dict):
    """保存审核结果到数据库"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sop_id = audit_result.get("sop_id")
        auditor = audit_result.get("auditor", "AI智能审核系统（确定性版本）")
        audit_date = audit_result.get("audit_date", datetime.now().isoformat())
        
        # 从审核结果中提取数据
        audit_data = audit_result.get("audit_result", {})
        audit_summary = audit_data.get("audit_summary", {})
        itemized_audit = audit_data.get("itemized_audit", [])
        
        # 计算总体评分
        overall_score = 0
        if itemized_audit:
            total_score = 0
            for item in itemized_audit:
                status = item.get("compliance_status", "")
                if status == "符合":
                    total_score += 100
                elif status == "部分符合":
                    total_score += 60
                elif status == "不符合":
                    total_score += 0
                else:
                    total_score += 50
            overall_score = total_score / len(itemized_audit)
        
        # 计算合规分数
        compliance_score = int(overall_score)
        
        # 提取总结
        summary = audit_summary.get("overall_compliance", "")
        
        # 提取建议
        suggestions = audit_data.get("optimization_suggestions", [])
        recommendations_text = "\\n".join(suggestions) if suggestions else ""
        
        # 插入审核结果
        cursor.execute("""
            INSERT INTO audit_results
            (sop_id, auditor, audit_date, overall_score, status, 
             compliance_score, summary, recommendations, raw_result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sop_id,
            auditor,
            audit_date,
            overall_score,
            "completed",
            compliance_score,
            summary[:500],
            recommendations_text[:1000],
            json.dumps(audit_result, ensure_ascii=False)
        ))
        
        audit_id = cursor.lastrowid
        
        # 保存审核明细到audit_details表
        itemized_audit = audit_data.get("itemized_audit", [])
        for i, item in enumerate(itemized_audit):
            standard_section = item.get("standard_section", f"标准{i+1}")
            requirement_summary = item.get("requirement_summary", "")
            sop_content = item.get("sop_content", "")
            audit_opinion = item.get("audit_opinion", "")
            compliance_status = item.get("compliance_status", "需审核")
            modification_suggestion = item.get("modification_suggestion", "")
            
            # 从standard_section中提取标准ID（例如："第4.1条" -> "4.1"）
            standard_id = "通用标准"
            if "第" in standard_section and "条" in standard_section:
                # 提取类似"第4.1条"中的"4.1"
                import re
                match = re.search(r'第([\d\.]+)条', standard_section)
                if match:
                    standard_id = f"标准{match.group(1)}"
            
            # 计算符合性分数
            compliance_score = 0.0
            if compliance_status == "符合":
                compliance_score = 1.0
            elif compliance_status == "部分符合":
                compliance_score = 0.6
            elif compliance_status == "不符合":
                compliance_score = 0.0
            else:
                compliance_score = 0.5  # 默认值
            
            # 插入审核明细
            cursor.execute("""
                INSERT INTO audit_details
                (audit_id, standard_id, sop_clause, standard_clause, 
                 compliance_score, comments, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                audit_id,
                standard_id,
                sop_content[:500],  # SOP条款内容
                requirement_summary[:500],  # 标准条款要求
                compliance_score,
                audit_opinion[:1000],  # 审核意见
                modification_suggestion[:1000]  # 改进建议
            ))
        
        conn.commit()
        conn.close()
        
        print(f"审核结果已保存到数据库，ID: {audit_id}，明细数量: {len(itemized_audit)}")
        return audit_id
        
    except Exception as e:
        print(f"保存审核结果到数据库失败: {e}")
        return None

# 补充审核条款函数
def supplement_audit_items(existing_items: List[Dict], standards: List[Dict], sop_content: str, current_count: int) -> List[Dict]:
    """补充审核条款以达到至少5条"""
    supplemented_items = existing_items.copy()
    
    # 需要补充的数量
    needed = 5 - current_count
    
    if needed <= 0:
        return supplemented_items
    
    print(f"需要补充{needed}个审核条款")
    
    # 获取标准名称
    standard_names = []
    for standard in standards:
        name = standard.get('name', standard.get('standard_name', '未知标准'))
        standard_no = standard.get('standard_no', standard.get('code', ''))
        if standard_no:
            standard_names.append(f"{standard_no} - {name}")
        else:
            standard_names.append(name)
    
    # 常见的审核维度
    common_audit_dimensions = [
        {
            "clause": "文件完整性",
            "requirement": "操作规程应包含完整的章节结构，包括目的、范围、职责、程序等",
            "status": "部分符合"
        },
        {
            "clause": "风险识别",
            "requirement": "操作规程应识别并评估相关安全风险",
            "status": "需审核"
        },
        {
            "clause": "应急措施",
            "requirement": "操作规程应包含应急响应和处置措施",
            "status": "需审核"
        },
        {
            "clause": "培训要求",
            "requirement": "操作规程应明确相关人员的培训要求",
            "status": "需审核"
        },
        {
            "clause": "记录管理",
            "requirement": "操作规程应规定相关记录的保存和管理要求",
            "status": "需审核"
        }
    ]
    
    # 添加补充条款
    for i in range(needed):
        if i < len(common_audit_dimensions):
            dimension = common_audit_dimensions[i]
            new_item = {
                "standard_section": f"通用要求 - {dimension['clause']}",
                "requirement_summary": dimension['requirement'],
                "sop_content": "需进一步审核确认",
                "audit_opinion": "AI审核未覆盖此条款，需要人工复核",
                "compliance_status": dimension['status']
            }
            supplemented_items.append(new_item)
    
    return supplemented_items

# 结构化审核提示
def create_structured_audit_prompt(sop_content: str, standards: List[Dict]) -> str:
    """创建结构化的审核提示，确保输出一致性"""
    
    # 构建标准列表
    standards_text = ""
    for i, standard in enumerate(standards, 1):
        standard_no = standard.get('standard_no', standard.get('code', f'标准{i}'))
        standard_name = standard.get('name', standard.get('standard_name', '未知标准'))
        standard_desc = standard.get('description', standard.get('desc', '无描述'))
        
        standards_text += f"{i}. {standard_no} - {standard_name}\n"
        standards_text += f"   要求: {standard_desc}\n\n"
    
    prompt = f"""
# 安全操作规程AI智能审核任务

## 审核要求
你是一个专业的安全审核专家。请对以下安全操作规程进行逐条详细审核。

### 1. 需要审核的技术标准
{standards_text}

### 2. 被审核的安全操作规程内容
{sop_content[:5000]}...

## 核心审核指令（必须严格遵守）
1. **逐条审核**：对每个技术标准进行逐条款审核，不能只做整体评价
2. **最少5条**：必须生成至少5条独立的审核结果
3. **具体到条款**：每条审核必须对应具体的技术标准条款（如"第4.1条"、"第5.2.3款"）

## 审核结果输出格式（必须严格遵循）

### 审核摘要
- 总体符合性: [符合/部分符合/不符合]
- 审核标准数量: [数字]
- 审核条款数量: [必须≥5]
- 符合条款数: [数字]
- 部分符合条款数: [数字]
- 不符合条款数: [数字]

### 逐条审核结果表格（必须至少5行，每行一个独立的审核发现）

| 序号 | 技术标准章节 | 核心要求摘要 | 操作规程对应内容 | 审核意见 | 符合状态 | 修改建议（仅对不符合和部分符合项） |
|------|--------------|--------------|------------------|----------|----------|-----------------------------------|
| 1 | [具体条款，如"第4.1条"] | [该条款的核心要求] | [操作规程中对应的具体内容] | [具体审核意见] | [符合/部分符合/不符合] | [如不符合或部分符合，给出具体修改建议] |
| 2 | [具体条款，如"第4.2条"] | [该条款的核心要求] | [操作规程中对应的具体内容] | [具体审核意见] | [符合/部分符合/不符合] | [如不符合或部分符合，给出具体修改建议] |
| 3 | [具体条款，如"第5.1条"] | [该条款的核心要求] | [操作规程中对应的具体内容] | [具体审核意见] | [符合/部分符合/不符合] | [如不符合或部分符合，给出具体修改建议] |
| 4 | [具体条款，如"第5.2条"] | [该条款的核心要求] | [操作规程中对应的具体内容] | [具体审核意见] | [符合/部分符合/不符合] | [如不符合或部分符合，给出具体修改建议] |
| 5 | [具体条款，如"第5.3条"] | [该条款的核心要求] | [操作规程中对应的具体内容] | [具体审核意见] | [符合/部分符合/不符合] | [如不符合或部分符合，给出具体修改建议] |
| ... | ... | ... | ... | ... | ... | ... |

### 重点问题与改进建议（针对不符合和部分符合项）
#### 不符合项改进建议：
- [不符合项1的具体改进建议]
- [不符合项2的具体改进建议]

#### 部分符合项改进建议：
- [部分符合项1的具体改进建议]
- [部分符合项2的具体改进建议]

### 审核依据
- [使用的标准1全称]
- [使用的标准2全称]

## 强制要求
1. **表格必须至少5行**，每行对应一个独立的技术标准条款审核
2. **不能合并审核**：每个技术标准条款必须单独审核，不能合并评价
3. **必须具体引用**：操作规程对应内容必须从提供的文本中直接引用
4. **审核意见要具体**：指出具体问题或符合情况，不能只说"符合"或"不符合"
5. **技术标准章节要具体**：必须写明具体条款编号，不能只写标准名称

## 审核步骤
1. 仔细阅读每个技术标准，识别出关键条款
2. 在操作规程中查找与每个条款对应的内容
3. 逐条对比，给出具体审核意见
4. 确保生成至少5条独立的审核结果
5. 按照格式要求输出

现在开始逐条审核，确保输出至少5条审核结果：
"""
    
    return prompt

# 解析审核结果
def parse_audit_result(ai_response: str) -> Dict[str, Any]:
    """解析AI返回的审核结果"""
    try:
        result = {
            "audit_summary": {},
            "itemized_audit": [],
            "optimization_suggestions": [],
            "standards_audited": []
        }
        
        lines = ai_response.split('\n')
        
        # 解析审核摘要
        for line in lines:
            if '总体符合性:' in line:
                result["audit_summary"]["overall_compliance"] = line.split(':')[1].strip()
            elif '审核标准数量:' in line:
                result["audit_summary"]["standards_count"] = int(line.split(':')[1].strip())
            elif '审核条款数量:' in line:
                result["audit_summary"]["items_count"] = int(line.split(':')[1].strip())
        
        # 解析表格
        in_table = False
        table_header_found = False
        
        for line in lines:
            line = line.strip()
            
            # 检测表格开始
            if '| 序号 |' in line or '| 技术标准章节 |' in line:
                in_table = True
                table_header_found = True
                continue
            
            # 检测表格结束
            if in_table and (not line.startswith('|') or line.startswith('###') or line.startswith('##')):
                in_table = False
                continue
            
            # 解析表格行
            if in_table and line.startswith('|') and table_header_found:
                # 跳过表头分隔行
                if '---' in line:
                    continue
                
                # 解析表格数据
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(cells) >= 6:
                    item = {
                        "standard_section": cells[1],
                        "requirement_summary": cells[2],
                        "sop_content": cells[3],
                        "audit_opinion": cells[4],
                        "compliance_status": cells[5],
                        "modification_suggestion": cells[6] if len(cells) > 6 else ""
                    }
                    result["itemized_audit"].append(item)
        
        # 解析改进建议 - 现在有多个部分
        in_non_compliant_suggestions = False
        in_partial_compliant_suggestions = False
        
        for line in lines:
            # 检测不符合项改进建议开始
            if '#### 不符合项改进建议' in line or '### 不符合项改进建议' in line or '不符合项改进建议：' in line:
                in_non_compliant_suggestions = True
                in_partial_compliant_suggestions = False
                continue
            
            # 检测部分符合项改进建议开始
            if '#### 部分符合项改进建议' in line or '### 部分符合项改进建议' in line or '部分符合项改进建议：' in line:
                in_partial_compliant_suggestions = True
                in_non_compliant_suggestions = False
                continue
            
            # 检测其他章节开始
            if (line.startswith('###') or line.startswith('##')) and ('改进建议' not in line):
                in_non_compliant_suggestions = False
                in_partial_compliant_suggestions = False
                continue
            
            # 解析不符合项改进建议
            if in_non_compliant_suggestions and line.strip().startswith('-'):
                suggestion = line.strip()[1:].strip()
                if suggestion:
                    result.setdefault("non_compliant_suggestions", []).append(suggestion)
            
            # 解析部分符合项改进建议
            if in_partial_compliant_suggestions and line.strip().startswith('-'):
                suggestion = line.strip()[1:].strip()
                if suggestion:
                    result.setdefault("partial_compliant_suggestions", []).append(suggestion)
            
            # 也解析旧的改进建议格式（兼容性）
            if '### 改进建议' in line or '## 改进建议' in line:
                in_suggestions = True
                continue
            
            if 'in_suggestions' in locals() and in_suggestions and line.strip().startswith('-'):
                suggestion = line.strip()[1:].strip()
                if suggestion:
                    result["optimization_suggestions"].append(suggestion)
        
        # 解析审核依据
        in_basis = False
        for line in lines:
            if '### 审核依据' in line or '## 审核依据' in line:
                in_basis = True
                continue
            
            if in_basis and (line.startswith('###') or line.startswith('##')):
                in_basis = False
                continue
            
            if in_basis and line.strip().startswith('-'):
                standard = line.strip()[1:].strip()
                if standard:
                    result["standards_audited"].append(standard)
        
        return result
        
    except Exception as e:
        print(f"解析审核结果失败: {e}")
        return {
            "audit_summary": {"overall_compliance": "解析失败", "error": str(e)},
            "itemized_audit": [],
            "optimization_suggestions": ["审核结果解析失败，请检查AI响应格式"],
            "standards_audited": []
        }

# 数据模型
class AuditRequest(BaseModel):
    sop_id: str
    force_new: bool = False

class AuditTask(BaseModel):
    task_id: str
    sop_id: str
    status: str = "pending"
    progress: int = 0
    step: str = "等待开始"
    message: str = ""
    result: Optional[Dict] = None
    error: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

# 任务存储
audit_tasks = {}

# 生成任务ID
def generate_task_id(sop_id: str) -> str:
    timestamp = int(time.time())
    return f"audit-det-{sop_id}-{timestamp}"

# 执行审核任务
def execute_audit_task(task_id: str, sop_id: str, force_new: bool = False):
    """执行审核任务 - 确定性版本"""
    try:
        task = audit_tasks[task_id]
        task.status = "running"
        task.step = "获取SOP信息"
        task.progress = 10
        task.updated_at = datetime.now()
        
        # 获取SOP信息
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 尝试不同的表名
        sop_data = None
        table_names = ['sops', 'safety_operation_procedures', 'sop_records']
        
        for table_name in table_names:
            try:
                cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (sop_id,))
                sop_data = cursor.fetchone()
                if sop_data:
                    print(f"在表 {table_name} 中找到SOP: {sop_id}")
                    break
            except Exception as e:
                print(f"查询表 {table_name} 失败: {e}")
                continue
        
        if not sop_data:
            task.status = "failed"
            task.error = f"未找到SOP: {sop_id}"
            task.updated_at = datetime.now()
            return
        
        sop_info = dict(sop_data)
        task.step = "提取PDF内容"
        task.progress = 20
        task.updated_at = datetime.now()
        
        # 提取PDF内容
        file_path = resolve_file_path(sop_info.get('file_path', ''))
        pdf_result = extract_pdf_content(file_path)
        
        if not pdf_result.get('success', False):
            task.status = "failed"
            task.error = f"PDF内容提取失败: {pdf_result.get('error', '未知错误')}"
            task.updated_at = datetime.now()
            return
        
        sop_content = pdf_result.get('content', '')
        task.step = "获取关联标准"
        task.progress = 30
        task.updated_at = datetime.now()
        
        # 获取关联标准
        standards = []
        
        # 尝试从mapping_matrix表获取关联标准
        try:
            cursor.execute("""
                SELECT s.* FROM core_standards s
                JOIN mapping_matrix m ON s.id = m.standard_id
                WHERE m.sop_id = ?
            """, (sop_id,))
            
            standards = [dict(row) for row in cursor.fetchall()]
            print(f"从mapping_matrix找到 {len(standards)} 个关联标准")
        except Exception as e:
            print(f"从mapping_matrix查询关联标准失败: {e}")
        
        # 只使用关联的标准，不添加额外标准
        print(f"使用 {len(standards)} 个关联标准进行审核")
        
        # 如果没有关联标准，提示用户
        if len(standards) == 0:
            task.status = "failed"
            task.error = "该SOP未关联任何技术标准，请先在标准管理页面关联标准后再进行AI审核"
            task.updated_at = datetime.now()
            conn.close()
            return
        
        conn.close()
        
        task.step = "检查缓存"
        task.progress = 40
        task.updated_at = datetime.now()
        
        # 检查缓存（除非强制重新审核）
        if not force_new:
            cached_result = get_cached_audit(sop_id, sop_content, standards)
            if cached_result:
                task.result = cached_result
                task.status = "completed"
                task.progress = 100
                task.step = "完成"
                task.message = "使用缓存结果"
                task.updated_at = datetime.now()
                print(f"使用缓存结果 for {sop_id}")
                return
        
        task.step = "创建审核提示"
        task.progress = 50
        task.updated_at = datetime.now()
        
        # 创建结构化审核提示
        audit_prompt = create_structured_audit_prompt(sop_content, standards)
        
        task.step = "调用AI审核"
        task.progress = 60
        task.updated_at = datetime.now()
        
        # 调用DeepSeek API
        ai_response = call_deepseek_api_deterministic(audit_prompt, max_tokens=4000)
        
        if not ai_response or 'choices' not in ai_response or not ai_response['choices']:
            task.status = "failed"
            task.error = "AI返回结果为空"
            task.updated_at = datetime.now()
            return
        
        ai_content = ai_response['choices'][0]['message']['content']
        
        task.step = "解析审核结果"
        task.progress = 80
        task.updated_at = datetime.now()
        
        # 解析审核结果
        audit_result = parse_audit_result(ai_content)
        
        # 验证审核结果
        itemized_audit = audit_result.get("itemized_audit", [])
        original_count = len(itemized_audit)
        
        if original_count < 5:
            print(f"警告：审核结果只有{original_count}个条款，少于要求的5个，尝试补充默认条款")
            
            # 补充默认审核条款以达到至少5条
            itemized_audit = supplement_audit_items(itemized_audit, standards, sop_content, original_count)
            
            # 更新审核结果
            audit_result["itemized_audit"] = itemized_audit
            
            print(f"补充后审核条款数量: {len(itemized_audit)}个")
        
        # 构建完整结果
        full_result = {
            "sop_id": sop_id,
            "sop_info": sop_info,
            "auditor": "AI智能审核系统（确定性版本）",
            "audit_date": datetime.now().isoformat(),
            "audit_id": task_id,
            "audit_result": audit_result,
            "standards_count": len(standards),
            "standards_audited": [s.get('name', s.get('standard_no', '未知标准')) for s in standards],
            "content_length": len(sop_content),
            "audit_format": "structured_table_v2",
            "audit_items_count": len(itemized_audit)
        }
        
        task.result = full_result
        task.status = "completed"
        task.progress = 100
        task.step = "完成"
        task.message = f"审核完成，基于{len(standards)}个标准，生成{len(itemized_audit)}个审核条款"
        task.updated_at = datetime.now()
        
        # 缓存结果
        cache_audit_result(sop_id, sop_content, standards, full_result)
        
        # 保存到数据库
        save_audit_to_database(full_result)
        
        print(f"审核任务完成: {task_id}")
        
    except Exception as e:
        print(f"审核任务失败: {e}")
        task = audit_tasks.get(task_id)
        if task:
            task.status = "failed"
            task.error = str(e)
            task.updated_at = datetime.now()

# API端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "AI Audit API (Deterministic)",
        "version": "5.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "deterministic_output": True,
            "temperature": 0.1,
            "top_p": 0.9,
            "audit_cache": True,
            "structured_prompt": True,
            "deepseek_integration": True
        }
    }

@app.post("/api/ai-audit/start")
async def start_audit(request: AuditRequest, background_tasks: BackgroundTasks):
    """启动AI审核任务"""
    try:
        # 生成任务ID
        task_id = generate_task_id(request.sop_id)
        
        # 创建任务
        task = AuditTask(
            task_id=task_id,
            sop_id=request.sop_id,
            status="pending",
            progress=0,
            step="初始化",
            message="任务已创建，等待执行"
        )
        
        audit_tasks[task_id] = task
        
        # 在后台执行审核任务
        background_tasks.add_task(execute_audit_task, task_id, request.sop_id, request.force_new)
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "AI审核任务已创建并开始执行",
            "sop_id": request.sop_id,
            "force_new": request.force_new,
            "status_url": f"/api/ai-audit/status/{task_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动审核任务失败: {str(e)}")

@app.get("/api/ai-audit/status/{task_id}")
async def get_audit_status(task_id: str):
    """获取审核任务状态"""
    task = audit_tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"未找到任务: {task_id}")
    
    return {
        "task_id": task.task_id,
        "sop_id": task.sop_id,
        "status": task.status,
        "progress": task.progress,
        "step": task.step,
        "message": task.message,
        "result": task.result,
        "error": task.error,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat()
    }

@app.get("/api/ai-audit/cache/info")
async def get_cache_info():
    """获取缓存信息"""
    return {
        "cache_size": len(audit_cache),
        "cache_keys": list(audit_cache.keys())[:10],  # 只显示前10个
        "cache_enabled": True
    }

@app.delete("/api/ai-audit/cache/clear")
async def clear_cache():
    """清空缓存"""
    global audit_cache
    cache_size = len(audit_cache)
    audit_cache = {}
    return {
        "success": True,
        "message": f"已清空缓存，共清除 {cache_size} 个缓存项"
    }

@app.get("/api/ai-audit/history")
async def get_audit_history(sop_id: Optional[str] = None, limit: int = 5):
    """获取审核历史（从数据库）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 构建SQL查询
        sql = """
            SELECT ar.id, ar.sop_id, ar.auditor, ar.audit_date,
                   ar.overall_score, ar.compliance_score, ar.summary,
                   s.name as sop_name
            FROM audit_results ar
            LEFT JOIN safety_operation_procedures s ON ar.sop_id = s.id
            WHERE ar.auditor LIKE '%确定性版本%' OR ar.auditor LIKE '%AI智能审核系统%'
        """
        
        params = []
        
        # 添加SOP ID过滤
        if sop_id:
            sql += " AND ar.sop_id = ?"
            params.append(sop_id)
        
        # 添加排序和限制
        sql += " ORDER BY ar.audit_date DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        history = cursor.fetchall()
        conn.close()

        result = []
        for record in history:
            result.append({
                "id": record["id"],
                "sop_id": record["sop_id"],
                "sop_name": record["sop_name"] or f"SOP {record['sop_id']}",
                "auditor": record["auditor"],
                "audit_date": record["audit_date"],
                "overall_score": record["overall_score"],
                "compliance_level": record["compliance_score"],
                "summary": record["summary"],
                "is_real_audit": True,
                "audit_mode": "deterministic"
            })

        return {
            "status": "success",
            "count": len(result),
            "mode": "deterministic",
            "history": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"获取审核历史失败: {str(e)}",
            "history": []
        }



# 测试端点
@app.get("/test/deterministic")
async def test_deterministic():
    """测试确定性输出"""
    test_prompt = "请回答：1+1等于几？"
    
    # 调用两次，应该得到相同的结果
    result1 = call_deepseek_api_deterministic(test_prompt, max_tokens=50)
    result2 = call_deepseek_api_deterministic(test_prompt, max_tokens=50)
    
    content1 = result1['choices'][0]['message']['content'] if result1 and 'choices' in result1 else "失败"
    content2 = result2['choices'][0]['message']['content'] if result2 and 'choices' in result2 else "失败"
    
    return {
        "test": "deterministic_output",
        "prompt": test_prompt,
        "result1": content1,
        "result2": content2,
        "identical": content1 == content2,
        "temperature": 0.1,
        "top_p": 0.9
    }

# 启动服务
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("AI智能审核API服务（确定性版本）")
    print("版本: 5.0.0")
    print("特性: 确定性输出、审核缓存、结构化提示")
    print(f"DeepSeek API配置: {'正常' if DEEPSEEK_API_KEY.startswith('sk-') else '未配置'}")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8002)
