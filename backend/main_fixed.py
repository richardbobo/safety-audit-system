#!/usr/bin/env python3
"""
修复版本：解决API路由注册问题
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from pathlib import Path
from datetime import datetime
import json
import random
import sqlite3
import tempfile
import shutil
import sys

# 添加当前目录到Python路径，以便导入dashboard_api
sys.path.append(os.path.dirname(__file__))

app = FastAPI()

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，便于开发测试
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
frontend_dir = os.path.join(os.path.dirname(__file__), "../frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# 挂载uploads目录
uploads_dir = os.path.join(os.path.dirname(__file__), "../data/uploads")
app.mount("/static/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# ========== 数据库连接函数 ==========
def get_db_connection():
    """获取数据库连接"""
    # 使用相对路径，兼容Windows和Mac/Linux
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "safety_audit.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 返回字典格式的行
    return conn

# ========== 健康检查 ==========
@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM safety_operation_procedures")
        sop_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "healthy", 
            "service": "safety-audit-backend", 
            "sop_count": sop_count
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "safety-audit-backend",
            "error": str(e)
        }

# ========== Favicon处理 ==========
@app.get("/favicon.ico")
async def get_favicon():
    """提供favicon图标"""
    try:
        # favicon.ico文件路径
        frontend_dir = os.path.join(os.path.dirname(__file__), "../frontend")
        favicon_path = os.path.join(frontend_dir, "favicon.ico")
        
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path, media_type="image/x-icon")
        else:
            # 如果文件不存在，返回一个简单的404响应而不是抛出异常
            from fastapi.responses import Response
            return Response(status_code=404)
    except Exception:
        # 发生错误时返回404
        from fastapi.responses import Response
        return Response(status_code=404)

# ========== SOP管理API ==========
@app.get("/api/sops")
async def get_all_sops():
    """获取所有SOP，包含关联标准数量"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 查询所有SOP
        cursor.execute('''
            SELECT id, name, version, file_path, category, department,
                   last_review_date, content, created_at, updated_at, file_size
            FROM safety_operation_procedures
            ORDER BY created_at DESC
        ''')
        
        sops = cursor.fetchall()
        
        # 转换为字典列表，并统计每个SOP的关联标准数量
        result = []
        for sop in sops:
            sop_id = sop[0]
            
            # 统计该SOP的关联标准数量
            cursor.execute('''
                SELECT COUNT(*) FROM mapping_matrix 
                WHERE sop_id = ?
            ''', (sop_id,))
            
            standards_count = cursor.fetchone()[0]
            
            # 获取该SOP的最新审核状态
            cursor.execute('''
                SELECT status, overall_score, audit_date, auditor
                FROM audit_results 
                WHERE sop_id = ? 
                ORDER BY audit_date DESC, created_at DESC 
                LIMIT 1
            ''', (sop_id,))
            
            audit_record = cursor.fetchone()
            
            # 根据审核记录确定状态
            compliance_status = "pending"  # 默认值
            audit_score = None
            last_audit_date = None
            last_auditor = None
            
            if audit_record:
                audit_status = audit_record[0]
                audit_score = audit_record[1]
                last_audit_date = audit_record[2]
                last_auditor = audit_record[3]
                
                # 根据审核状态和分数确定显示状态
                if audit_status == "completed":
                    if audit_score is not None:
                        if audit_score >= 80:
                            compliance_status = "compliant"  # 优秀：分数≥80
                        elif audit_score >= 60:
                            compliance_status = "compliant"  # 合格：分数60-79
                        else:
                            compliance_status = "non-compliant"  # 不合格：分数<60
                    else:
                        compliance_status = "reviewing"  # 已完成但无分数
                elif audit_status == "in_progress":
                    compliance_status = "reviewing"  # 审核中
                elif audit_status == "failed":
                    compliance_status = "non-compliant"  # 审核失败
                else:
                    # 如果有审核记录但状态未知，视为已审核
                    compliance_status = "compliant" if audit_score is not None else "reviewing"
            
            sop_dict = {
                "id": sop_id,
                "name": sop[1],
                "version": sop[2],
                "file_path": sop[3],
                "category": sop[4],
                "department": sop[5],  # 使用实际的department值
                "last_review_date": sop[6],
                "content": sop[7],
                "created_at": sop[8],
                "updated_at": sop[9],
                "file_size": sop[10],
                # 添加缺失的字段，使用默认值
                "sop_id": sop_id,  # 使用id作为sop_id
                "file_name": os.path.basename(sop[3]) if sop[3] else "",  # 从file_path提取文件名
                "compliance_status": compliance_status,  # 从审核记录获取
                "audit_score": audit_score,  # 从审核记录获取
                "last_audit_date": last_audit_date,  # 最近审核日期
                "last_auditor": last_auditor,  # 最近审核人
                "last_updated": sop[9],  # 使用updated_at
                # 添加关联标准数量
                "standards_count": standards_count
            }
            result.append(sop_dict)
        
        conn.close()
        
        return {
            "status": "success",
            "message": f"成功获取 {len(result)} 条SOP记录",
            "data": result
        }
        
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"获取SOP列表失败: {str(e)}")
        
        return {
            "status": "success",
            "message": f"成功获取 {len(result)} 条SOP记录",
            "data": result
        }
        
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"获取SOP列表失败: {str(e)}")

@app.get("/api/sops/search")
async def search_sops(
    q: Optional[str] = None,
    category: Optional[str] = None
):
    """搜索安全操作规程，包含关联标准数量"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            id, name, version, file_path, category, department,
            last_review_date, content, file_size,
            created_at, updated_at
        FROM safety_operation_procedures 
        WHERE 1=1
        """
        params = []
        
        if q:
            query += " AND (name LIKE ? OR id LIKE ? OR content LIKE ?)"
            search_term = f"%{q}%"
            params.extend([search_term, search_term, search_term])
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        sops = cursor.fetchall()
        
        result = []
        for sop in sops:
            sop_id = sop[0]
            
            # 统计该SOP的关联标准数量
            cursor.execute('''
                SELECT COUNT(*) FROM mapping_matrix 
                WHERE sop_id = ?
            ''', (sop_id,))
            
            standards_count = cursor.fetchone()[0]
            
            # 获取该SOP的最新审核状态
            cursor.execute('''
                SELECT status, overall_score, audit_date, auditor
                FROM audit_results 
                WHERE sop_id = ? 
                ORDER BY audit_date DESC, created_at DESC 
                LIMIT 1
            ''', (sop_id,))
            
            audit_record = cursor.fetchone()
            
            # 根据审核记录确定状态
            compliance_status = "pending"  # 默认值
            audit_score = None
            last_audit_date = None
            last_auditor = None
            
            if audit_record:
                audit_status = audit_record[0]
                audit_score = audit_record[1]
                last_audit_date = audit_record[2]
                last_auditor = audit_record[3]
                
                # 根据审核状态和分数确定显示状态
                if audit_status == "completed":
                    if audit_score is not None:
                        if audit_score >= 80:
                            compliance_status = "compliant"  # 优秀：分数≥80
                        elif audit_score >= 60:
                            compliance_status = "compliant"  # 合格：分数60-79
                        else:
                            compliance_status = "non-compliant"  # 不合格：分数<60
                    else:
                        compliance_status = "reviewing"  # 已完成但无分数
                elif audit_status == "in_progress":
                    compliance_status = "reviewing"  # 审核中
                elif audit_status == "failed":
                    compliance_status = "non-compliant"  # 审核失败
                else:
                    # 如果有审核记录但状态未知，视为已审核
                    compliance_status = "compliant" if audit_score is not None else "reviewing"
            
            sop_dict = {
                "id": sop_id,
                "name": sop[1],
                "version": sop[2],
                "file_path": sop[3],
                "category": sop[4],
                "department": sop[5],  # 使用实际的department值
                "last_review_date": sop[6],
                "content": sop[7],
                "file_size": sop[8],
                "created_at": sop[9],
                "updated_at": sop[10],
                # 添加前端兼容字段
                "sop_id": sop_id,
                "file_name": os.path.basename(sop[3]) if sop[3] else "",
                "compliance_status": compliance_status,  # 从审核记录获取
                "audit_score": audit_score,  # 从审核记录获取
                "last_audit_date": last_audit_date,  # 最近审核日期
                "last_auditor": last_auditor,  # 最近审核人
                "last_updated": sop[9],
                # 添加关联标准数量
                "standards_count": standards_count
            }
            result.append(sop_dict)
        
        conn.close()
        
        return {
            "status": "success",
            "message": f"成功搜索到 {len(result)} 条SOP记录",
            "data": result
        }
        
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"搜索SOP失败: {str(e)}")
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"搜索SOP失败: {str(e)}")

@app.post("/api/sops")
async def create_sop(
    name: str = Form(...),
    version: str = Form(...),
    category: str = Form(...),
    department: str = Form(None),  # 改为None，不设默认值
    file: UploadFile = File(...)
):
    """创建新SOP"""
    print(f"\n{'='*60}")
    print("创建SOP - 紧急修复版本")
    print(f"{'='*60}")
    print(f"接收到的参数:")
    print(f"  name: {name}")
    print(f"  version: {version}")
    print(f"  category: {category}")
    print(f"  department参数值: {department} (类型: {type(department)})")
    print(f"  file: {file.filename}")
    
    # 如果department为None，使用"安全部"作为默认值
    if department is None:
        department = "安全部"
        print(f"  注意: department参数为None，使用默认值: {department}")
    else:
        print(f"  使用前端提供的department值: {department}")
    
    print(f"{'='*60}\n")
    
    try:
        # 检查文件类型 - 只允许PDF
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext != '.pdf':
            raise HTTPException(status_code=400, detail="只支持PDF格式的文件，请上传PDF文档")
        
        # 检查文件大小 (10MB限制)
        content = await file.read()
        file_size = len(content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="文件大小超过10MB限制")
        
        # 生成唯一ID
        import uuid
        new_id = f"SOP-{uuid.uuid4().hex[:12]}"
        
        # 保存文件到上传目录
        upload_dir = os.path.join(os.path.dirname(__file__), "..", "data", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成安全的文件名
        safe_filename = f"{new_id}_{file.filename}"
        file_path = os.path.join("data", "uploads", safe_filename)
        actual_path = os.path.join(os.path.dirname(__file__), "..", file_path)
        
        # 保存文件
        with open(actual_path, 'wb') as f:
            f.write(content)
        
        # 保存到数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 调试：打印要插入的数据
        print(f"\n=== 插入数据库的数据 ===")
        print(f"  id: {new_id}")
        print(f"  name: {name}")
        print(f"  version: {version}")
        print(f"  file_path: {file_path}")
        print(f"  category: {category}")
        print(f"  department: {department}")
        print(f"  last_review_date: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"  content: 新创建的SOP: {name}")
        print(f"  file_size: {file_size}")
        print("=====================\n")
        
        cursor.execute('''
        INSERT INTO safety_operation_procedures 
        (id, name, version, file_path, category, department, last_review_date, content, file_size)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            new_id, name, version, file_path, 
            category, department, datetime.now().strftime('%Y-%m-%d'), 
            f"新创建的SOP: {name}",
            file_size
        ))
        
        # 获取刚插入的记录
        cursor.execute('''
        SELECT 
            id, name, version, file_path, category, department,
            last_review_date, content, file_size,
            created_at, updated_at
        FROM safety_operation_procedures
        WHERE id = ?
        ''', (new_id,))
        
        sop_data = cursor.fetchone()
        conn.commit()
        conn.close()
        
        # 转换为字典
        print(f"\n=== 创建返回字典 ===")
        print(f"从数据库查询到的数据:")
        for i, value in enumerate(sop_data):
            print(f"  [{i}]: {value}")
        
        sop_dict = {
            "id": sop_data[0],
            "name": sop_data[1],
            "version": sop_data[2],
            "file_path": sop_data[3],
            "category": sop_data[4],
            "department": sop_data[5],  # 使用实际的department值
            "last_review_date": sop_data[6],
            "content": sop_data[7],
            "file_size": sop_data[8],
            "created_at": sop_data[9],
            "updated_at": sop_data[10],
            # 添加前端兼容字段
            "sop_id": sop_data[0],
            "file_name": os.path.basename(sop_data[3]) if sop_data[3] else "",
            "compliance_status": "pending",
            "audit_score": None,
            "last_updated": sop_data[10]
        }
        
        print(f"\n创建的字典中的department字段: {sop_dict['department']}")
        print(f"{'='*60}\n")
        
        return {
            "status": "success",
            "message": "SOP创建成功",
            "data": sop_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建SOP失败: {str(e)}")

@app.put("/api/sops/{sop_id}")
async def update_sop(
    sop_id: str,
    name: str = Form(None),
    version: str = Form(None),
    category: str = Form(None),
    department: str = Form(None)
):
    """更新SOP信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查SOP是否存在
        cursor.execute('SELECT id FROM safety_operation_procedures WHERE id = ?', (sop_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"未找到SOP: {sop_id}")
        
        # 构建更新语句
        update_fields = []
        params = []
        
        if name is not None:
            update_fields.append("name = ?")
            params.append(name)
        
        if version is not None:
            update_fields.append("version = ?")
            params.append(version)
        
        if category is not None:
            update_fields.append("category = ?")
            params.append(category)
        
        if department is not None:
            update_fields.append("department = ?")
            params.append(department)
        
        # 如果没有要更新的字段
        if not update_fields:
            conn.close()
            raise HTTPException(status_code=400, detail="没有提供要更新的字段")
        
        # 添加更新时间
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        # 执行更新
        update_query = f"UPDATE safety_operation_procedures SET {', '.join(update_fields)} WHERE id = ?"
        params.append(sop_id)
        
        cursor.execute(update_query, params)
        conn.commit()
        
        # 获取更新后的记录
        cursor.execute('''
        SELECT id, name, version, file_path, category, department,
               last_review_date, content, file_size,
               created_at, updated_at
        FROM safety_operation_procedures
        WHERE id = ?
        ''', (sop_id,))
        
        sop_data = cursor.fetchone()
        conn.close()
        
        # 转换为字典
        sop_dict = {
            "id": sop_data[0],
            "name": sop_data[1],
            "version": sop_data[2],
            "file_path": sop_data[3],
            "category": sop_data[4],
            "department": sop_data[5],
            "last_review_date": sop_data[6],
            "content": sop_data[7],
            "file_size": sop_data[8],
            "created_at": sop_data[9],
            "updated_at": sop_data[10],
            # 添加前端兼容字段
            "sop_id": sop_data[0],
            "file_name": os.path.basename(sop_data[3]) if sop_data[3] else "",
            "compliance_status": "pending",  # 需要从审核记录获取
            "audit_score": None,
            "last_updated": sop_data[10]
        }
        
        return {
            "status": "success",
            "message": "SOP更新成功",
            "data": sop_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新SOP失败: {str(e)}")

@app.get("/api/sops/{sop_id}")
async def get_sop_by_id(sop_id: str):
    """根据ID获取SOP"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 只查询实际存在的字段
        cursor.execute('SELECT id, name, version, file_path, category, department, last_review_date, content, created_at, updated_at, file_size FROM safety_operation_procedures WHERE id = ?', (sop_id,))
        
        sop = cursor.fetchone()
        
        if not sop:
            conn.close()
            raise HTTPException(status_code=404, detail=f"未找到SOP: {sop_id}")
        
        # 获取该SOP的最新审核状态
        cursor.execute('''
            SELECT status, overall_score, audit_date, auditor
            FROM audit_results 
            WHERE sop_id = ? 
            ORDER BY audit_date DESC, created_at DESC 
            LIMIT 1
        ''', (sop_id,))
        
        audit_record = cursor.fetchone()
        
        # 根据审核记录确定状态
        compliance_status = "pending"  # 默认值
        audit_score = None
        last_audit_date = None
        last_auditor = None
        
        if audit_record:
            audit_status = audit_record[0]
            audit_score = audit_record[1]
            last_audit_date = audit_record[2]
            last_auditor = audit_record[3]
            
            # 根据审核状态和分数确定显示状态
            if audit_status == "completed":
                if audit_score is not None:
                    if audit_score >= 80:
                        compliance_status = "compliant"  # 优秀：分数≥80
                    elif audit_score >= 60:
                        compliance_status = "compliant"  # 合格：分数60-79
                    else:
                        compliance_status = "non-compliant"  # 不合格：分数<60
                else:
                    compliance_status = "reviewing"  # 已完成但无分数
            elif audit_status == "in_progress":
                compliance_status = "reviewing"  # 审核中
            elif audit_status == "failed":
                compliance_status = "non-compliant"  # 审核失败
            else:
                # 如果有审核记录但状态未知，视为已审核
                compliance_status = "compliant" if audit_score is not None else "reviewing"
        
        # 构建完整的SOP对象
        import os
        sop_dict = {
            "id": sop[0],
            "name": sop[1],
            "version": sop[2],
            "file_path": sop[3],
            "category": sop[4],
            "department": sop[5],  # 使用实际的department值
            "last_review_date": sop[6],
            "content": sop[7],
            "created_at": sop[8],
            "updated_at": sop[9],
            "file_size": sop[10],
            # 添加缺失的字段，使用默认值
            "sop_id": sop[0],  # 使用id作为sop_id
            "file_name": os.path.basename(sop[3]) if sop[3] else "",  # 从file_path提取文件名
            "compliance_status": compliance_status,  # 从审核记录获取
            "audit_score": audit_score,  # 从审核记录获取
            "last_audit_date": last_audit_date,  # 最近审核日期
            "last_auditor": last_auditor,  # 最近审核人
            "last_updated": sop[9]  # 使用updated_at
        }
        
        conn.close()
        return {
            "status": "success",
            "message": "获取SOP成功",
            "data": sop_dict
        }
        
    except HTTPException:
        if conn:
            conn.close()
        raise
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"获取SOP失败: {str(e)}")

@app.delete("/api/sops/{sop_id}")
async def delete_sop(sop_id: str):
    """删除SOP"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 先获取要删除的SOP信息
        cursor.execute('SELECT file_path FROM safety_operation_procedures WHERE id = ?', (sop_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="SOP not found")
        
        file_path = row['file_path']
        
        # 从数据库删除
        cursor.execute('DELETE FROM safety_operation_procedures WHERE id = ?', (sop_id,))
        
        # 尝试删除文件
        try:
            if file_path:
                # 构建完整的文件路径
                import os
                from pathlib import Path
                base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                full_path = base_dir / file_path
                if full_path.exists():
                    full_path.unlink()
                    print(f"已删除文件: {full_path}")
        except Exception as e:
            print(f"删除文件时出错，继续执行: {e}")
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": f"SOP {sop_id} 删除成功"
        }
        
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"数据库删除失败: {str(e)}")

@app.get("/api/sops/{sop_id}/pdf-content")
async def get_sop_pdf_content(sop_id: str, preview: bool = True):
    """获取SOP的PDF内容（简化版，用于前端显示）"""
    try:
        # 1. 从数据库获取SOP信息
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_path FROM safety_operation_procedures WHERE id = ?
        """, (sop_id,))
        
        sop_data = cursor.fetchone()
        conn.close()
        
        if not sop_data:
            return {
                "status": "error",
                "message": f"未找到SOP: {sop_id}",
                "data": None
            }
        
        file_path = sop_data[0]
        
        # 从文件路径中提取文件名
        file_name = os.path.basename(file_path) if file_path else "未知文件"
        
        # 2. 构建文件路径
        # 处理相对路径
        if file_path and not os.path.isabs(file_path):
            # 尝试多种路径
            base_dir = os.path.dirname(__file__)
            possible_paths = [
                os.path.join(base_dir, "..", file_path),
                os.path.join(base_dir, "..", "data", file_path),
                os.path.join(base_dir, "..", "data", "uploads", os.path.basename(file_path)),
            ]
            
            actual_path = None
            for path in possible_paths:
                path = os.path.normpath(path)
                if os.path.exists(path):
                    actual_path = path
                    break
            
            if not actual_path:
                return {
                    "status": "error",
                    "message": f"PDF文件不存在: {file_path}",
                    "data": None
                }
        else:
            actual_path = file_path
        
        # 规范化路径
        actual_path = os.path.normpath(actual_path)
        
        if not os.path.exists(actual_path):
            return {
                "status": "error",
                "message": f"PDF文件不存在: {actual_path}",
                "data": None
            }
        
        # 3. 检查文件类型
        if not file_name.lower().endswith('.pdf'):
            return {
                "status": "error",
                "message": "只支持PDF文件",
                "data": None
            }
        
        # 4. 提取文本（简化版）
        try:
            import pdfplumber
            
            with pdfplumber.open(actual_path) as pdf:
                total_pages = len(pdf.pages)
                
                # 只提取第一页作为预览
                preview_text = ""
                if total_pages > 0:
                    first_page = pdf.pages[0]
                    page_text = first_page.extract_text()
                    if page_text:
                        if preview:
                            # 预览模式：只返回前500字符
                            preview_text = page_text[:500]
                            if len(page_text) > 500:
                                preview_text += "..."
                        else:
                            preview_text = page_text
                
                result = {
                    "sop_id": sop_id,
                    "file_name": file_name,
                    "total_pages": total_pages,
                    "has_content": bool(preview_text),
                    "content_preview": preview_text,
                    "content_length": len(preview_text) if preview_text else 0,
                    "extracted_at": datetime.now().isoformat()
                }
                
                return {
                    "status": "success",
                    "message": "PDF内容获取成功",
                    "data": result
                }
                
        except ImportError:
            return {
                "status": "error",
                "message": "pdfplumber库未安装",
                "data": None
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"PDF内容提取失败: {str(e)}",
                "data": None
            }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取PDF内容失败: {str(e)}",
            "data": None
        }

# ========== 标准PDF内容提取API ==========
@app.get("/api/standards/{standard_id}/pdf-content")
async def get_standard_pdf_content(standard_id: str, preview: bool = True):
    """获取标准的PDF内容（简化版，用于前端显示）"""
    try:
        # 1. 从数据库获取标准信息
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_path FROM core_standards WHERE id = ?
        """, (standard_id,))
        
        standard_data = cursor.fetchone()
        conn.close()
        
        if not standard_data:
            return {
                "status": "error",
                "message": f"未找到标准: {standard_id}",
                "data": None
            }
        
        file_path = standard_data[0]
        
        if not file_path:
            return {
                "status": "error",
                "message": f"标准没有关联PDF文件: {standard_id}",
                "data": None
            }
        
        # 从文件路径中提取文件名
        if '\\' in file_path or '/' in file_path:
            file_name = os.path.basename(file_path)
        else:
            file_name = file_path
        
        # 2. 构建文件路径
        base_dir = os.path.dirname(__file__)
        uploads_dir = os.path.join(base_dir, "..", "data", "uploads")
        
        # 处理文件名中的+号
        actual_file_name = file_name.replace('+', '%2B')
        actual_path = os.path.join(uploads_dir, actual_file_name)
        
        # 如果文件不存在，尝试原始文件名
        if not os.path.exists(actual_path):
            actual_path = os.path.join(uploads_dir, file_name)
        
        if not os.path.exists(actual_path):
            return {
                "status": "error",
                "message": f"PDF文件不存在: {file_name}",
                "data": None
            }
        
        # 3. 检查文件类型
        if not file_name.lower().endswith('.pdf'):
            return {
                "status": "error",
                "message": "只支持PDF文件",
                "data": None
            }
        
        # 4. 提取文本（改进版，处理编码问题）
        try:
            import pdfplumber
            import re
            
            with pdfplumber.open(actual_path) as pdf:
                total_pages = len(pdf.pages)
                
                # 提取文本（尝试多种方法）
                preview_text = ""
                full_content = ""
                
                if total_pages > 0:
                    # 方法1：使用pdfplumber的extract_text
                    first_page = pdf.pages[0]
                    page_text = first_page.extract_text()
                    
                    if page_text:
                        # 清理文本：移除多余空格和换行
                        page_text = re.sub(r'\s+', ' ', page_text).strip()
                        
                        if preview:
                            # 预览模式：只返回前500字符
                            preview_text = page_text[:500]
                            if len(page_text) > 500:
                                preview_text += "..."
                        else:
                            preview_text = page_text
                    
                    # 如果方法1提取失败或质量差，尝试方法2：使用extract_words
                    if not page_text or len(page_text.strip()) < 50:
                        words = first_page.extract_words()
                        if words:
                            page_text = ' '.join([word['text'] for word in words])
                            page_text = re.sub(r'\s+', ' ', page_text).strip()
                            
                            if preview:
                                preview_text = page_text[:500]
                                if len(page_text) > 500:
                                    preview_text += "..."
                            else:
                                preview_text = page_text
                    
                    # 如果不是预览模式，提取所有页面
                    if not preview and total_pages > 1:
                        all_text_parts = []
                        for i, page in enumerate(pdf.pages):
                            page_text = page.extract_text()
                            if not page_text or len(page_text.strip()) < 10:
                                # 尝试使用extract_words
                                words = page.extract_words()
                                if words:
                                    page_text = ' '.join([word['text'] for word in words])
                            
                            if page_text:
                                # 清理文本
                                page_text = re.sub(r'\s+', ' ', page_text).strip()
                                all_text_parts.append(f"=== 第 {i+1} 页 ===\n{page_text}\n")
                        
                        if all_text_parts:
                            full_content = "\n".join(all_text_parts)
                
                result = {
                    "standard_id": standard_id,
                    "file_name": file_name,
                    "total_pages": total_pages,
                    "has_content": bool(preview_text and len(preview_text.strip()) > 10),
                    "content_preview": preview_text,
                    "content_length": len(preview_text) if preview_text else 0,
                    "extracted_at": datetime.now().isoformat(),
                    "file_size": os.path.getsize(actual_path),
                    "file_path": actual_path,
                    "is_preview": preview,
                    "extraction_method": "pdfplumber"
                }
                
                if full_content:
                    result["full_content"] = full_content
                    result["content_length"] = len(full_content)
                
                # 检查文本质量
                if preview_text:
                    # 检查是否包含中文字符
                    chinese_chars = re.findall(r'[\u4e00-\u9fff]', preview_text)
                    if len(chinese_chars) < 5 and len(preview_text) > 50:
                        result["warning"] = "提取的文本可能包含编码问题，PDF可能是扫描版或使用特殊字体"
                        result["text_quality"] = "low"
                    else:
                        result["text_quality"] = "good"
        
        except ImportError:
            # 如果没有pdfplumber，返回基本信息
            result = {
                "standard_id": standard_id,
                "file_name": file_name,
                "total_pages": 0,
                "has_content": False,
                "content_preview": "PDF处理库未安装，无法提取文本内容",
                "content_length": 0,
                "extracted_at": datetime.now().isoformat(),
                "file_size": os.path.getsize(actual_path) if os.path.exists(actual_path) else 0,
                "file_path": actual_path,
                "is_preview": preview,
                "warning": "请安装pdfplumber库以提取PDF文本内容: pip install pdfplumber"
            }
        
        return {
            "status": "success",
            "message": "PDF内容提取成功",
            "data": result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"PDF处理错误: {str(e)}",
            "data": None
        }

# ========== 文件下载API ==========
def resolve_file_path(file_path: str) -> str:
    """解析文件路径，尝试多种可能性"""
    if not file_path:
        return None
    
    if os.path.isabs(file_path):
        return file_path
    
    # 基础目录
    base_dir = os.path.dirname(__file__)
    
    # 尝试多种路径
    possible_paths = [
        # 原始路径
        os.path.join(base_dir, "..", file_path),
        # 如果路径以uploads开头，尝试映射到data/uploads
        os.path.join(base_dir, "..", "data", file_path.replace("uploads\\", "uploads\\")),
        # 直接到data/uploads目录查找
        os.path.join(base_dir, "..", "data", "uploads", os.path.basename(file_path)),
        # 相对路径
        file_path,
    ]
    
    for path in possible_paths:
        path = os.path.normpath(path)
        if os.path.exists(path):
            return path
    
    return None

@app.get("/api/files/{sop_id}/download")
async def download_sop_file(sop_id: str):
    """下载SOP文件"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_path FROM safety_operation_procedures 
            WHERE id = ?
        """, (sop_id,))
        
        sop_data = cursor.fetchone()
        conn.close()
        
        if not sop_data:
            raise HTTPException(status_code=404, detail=f"未找到SOP: {sop_id}")
        
        file_path = sop_data[0]
        file_name = os.path.basename(file_path) if file_path else f"{sop_id}.pdf"
        
        # 解析文件路径
        actual_path = resolve_file_path(file_path)
        
        if not actual_path or not os.path.exists(actual_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
        # 返回文件
        return FileResponse(
            actual_path,
            filename=file_name,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载错误: {str(e)}")

# ========== 标准文件下载端点 ==========
@app.get("/api/standards/{standard_id}/download")
async def download_standard_file(standard_id: str):
    """下载标准文件"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_path FROM core_standards 
            WHERE id = ?
        """, (standard_id,))
        
        standard_data = cursor.fetchone()
        conn.close()
        
        if not standard_data:
            raise HTTPException(status_code=404, detail=f"未找到标准: {standard_id}")
        
        file_path = standard_data[0]
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"标准没有关联文件: {standard_id}")
        
        # 提取文件名
        if '\\' in file_path or '/' in file_path:
            file_name = os.path.basename(file_path)
        else:
            file_name = file_path
        
        # 解析文件路径
        actual_path = resolve_file_path(file_path)
        
        if not actual_path or not os.path.exists(actual_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
        # 返回文件
        return FileResponse(
            actual_path,
            filename=file_name,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载错误: {str(e)}")

# ========== 标准文件查看端点 ==========
@app.get("/api/standards/{standard_id}/view")
async def view_standard_file(standard_id: str):
    """查看标准文件（返回文件URL）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_path FROM core_standards 
            WHERE id = ?
        """, (standard_id,))
        
        standard_data = cursor.fetchone()
        conn.close()
        
        if not standard_data:
            raise HTTPException(status_code=404, detail=f"未找到标准: {standard_id}")
        
        file_path = standard_data[0]
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"标准没有关联文件: {standard_id}")
        
        # 提取文件名
        if '\\' in file_path or '/' in file_path:
            file_name = os.path.basename(file_path)
        else:
            file_name = file_path
        
        # URL编码文件名（只编码+号）
        encoded_file_name = file_name.replace('+', '%2B')
        
        # 返回文件信息
        return {
            "standard_id": standard_id,
            "file_name": file_name,
            "encoded_file_name": encoded_file_name,
            "file_url": f"/static/uploads/{encoded_file_name}",
            "direct_url": f"/api/files/standard/{encoded_file_name}",  # 新增的直接访问端点
            "download_url": f"/api/standards/{standard_id}/download",
            "message": "使用file_url访问文件，或使用download_url下载文件"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件信息错误: {str(e)}")

# ========== 直接文件访问端点 ==========
@app.get("/api/files/standard/{file_name:path}")
async def get_standard_file(file_name: str):
    """直接访问标准文件（绕过StaticFiles的URL编码问题）"""
    try:
        # 解码文件名
        decoded_file_name = file_name.replace('%2B', '+')
        
        # 构建文件路径
        base_dir = os.path.dirname(__file__)
        uploads_dir = os.path.join(base_dir, "..", "data", "uploads")
        file_path = os.path.join(uploads_dir, decoded_file_name)
        
        if not os.path.exists(file_path):
            # 尝试查找文件（不区分大小写）
            files = os.listdir(uploads_dir)
            matching_files = [f for f in files if f.lower() == decoded_file_name.lower()]
            
            if matching_files:
                file_path = os.path.join(uploads_dir, matching_files[0])
            else:
                raise HTTPException(status_code=404, detail=f"文件不存在: {decoded_file_name}")
        
        # 返回文件
        return FileResponse(
            file_path,
            filename=decoded_file_name,
            media_type='application/pdf'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件访问错误: {str(e)}")

@app.get("/api/files/{sop_id}/info")
async def get_sop_file_info(sop_id: str):
    """获取SOP文件信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_path, file_size FROM safety_operation_procedures 
            WHERE id = ?
        """, (sop_id,))
        
        sop_data = cursor.fetchone()
        conn.close()
        
        if not sop_data:
            return {
                "status": "error",
                "message": f"未找到SOP: {sop_id}",
                "data": None
            }
        
        file_path = sop_data[0]
        file_name = os.path.basename(file_path) if file_path else f"{sop_id}.pdf"
        file_size = sop_data[1]
        
        # 解析文件路径
        actual_path = resolve_file_path(file_path)
        
        file_exists = os.path.exists(actual_path) if actual_path else False
        
        # 如果文件存在但数据库中没有大小，重新计算
        if file_exists and (not file_size or file_size == 0):
            file_size = os.path.getsize(actual_path)
        
        result = {
            "sop_id": sop_id,
            "file_path": file_path,
            "actual_path": actual_path,
            "file_name": file_name,
            "file_size": file_size,
            "file_exists": file_exists,
            "file_type": os.path.splitext(file_name)[1] if file_name else None
        }
        
        return {
            "status": "success",
            "message": "File info retrieved",
            "data": result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取文件信息失败: {str(e)}",
            "data": None
        }

# ========== 完整PDF提取API ==========
@app.post("/api/pdf/extract")
async def extract_pdf_content(request: dict = None):
    """完整提取PDF内容（用于智能审核）"""
    try:
        # 获取请求参数
        if request and isinstance(request, dict):
            sop_id = request.get("sop_id")
        else:
            # 如果没有请求体，尝试从表单获取
            sop_id = None
        
        if not sop_id:
            raise HTTPException(status_code=400, detail="需要提供sop_id参数")
        
        print(f"完整提取PDF内容，SOP ID: {sop_id}")
        
        # 1. 从数据库获取SOP信息
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_path FROM safety_operation_procedures WHERE id = ?
        """, (sop_id,))
        
        sop_data = cursor.fetchone()
        conn.close()
        
        if not sop_data:
            raise HTTPException(status_code=404, detail=f"未找到SOP: {sop_id}")
        
        file_path = sop_data[0]
        
        # 2. 解析文件路径
        actual_path = resolve_file_path(file_path)
        
        if not actual_path or not os.path.exists(actual_path):
            raise HTTPException(status_code=404, detail=f"PDF文件不存在: {file_path}")
        
        # 3. 检查文件类型
        file_name = os.path.basename(file_path) if file_path else "未知文件"
        if not file_name.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持PDF文件")
        
        # 4. 完整提取PDF内容
        try:
            import pdfplumber
            
            print(f"开始提取PDF: {actual_path}")
            
            with pdfplumber.open(actual_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"PDF总页数: {total_pages}")
                
                all_text = ""
                page_texts = []
                
                # 提取每一页的内容
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    all_text += page_text + "\n\n"
                    
                    page_texts.append({
                        "page": i + 1,
                        "text": page_text,
                        "char_count": len(page_text),
                        "has_content": bool(page_text.strip())
                    })
                    
                    # 每5页打印一次进度
                    if (i + 1) % 5 == 0 or (i + 1) == total_pages:
                        print(f"  已提取 {i + 1}/{total_pages} 页")
                
                # 提取表格（如果有）
                tables = []
                for i, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table_idx, table in enumerate(page_tables):
                            tables.append({
                                "page": i + 1,
                                "table_index": table_idx + 1,
                                "rows": len(table),
                                "columns": len(table[0]) if table else 0,
                                "has_data": bool(table)
                            })
                
                # 统计信息
                total_chars = len(all_text)
                non_empty_pages = sum(1 for page in page_texts if page["has_content"])
                
                result = {
                    "sop_id": sop_id,
                    "file_name": file_name,
                    "file_path": file_path,
                    "actual_path": actual_path,
                    "total_pages": total_pages,
                    "total_chars": total_chars,
                    "non_empty_pages": non_empty_pages,
                    "has_tables": len(tables) > 0,
                    "table_count": len(tables),
                    "extraction_time": datetime.now().isoformat(),
                    "pages": page_texts,
                    "tables": tables if tables else [],
                    "full_text": all_text[:10000] if all_text else "",  # 限制返回前10000字符
                    "full_text_preview": all_text[:1000] if all_text else ""  # 预览前1000字符
                }
                
                print(f"PDF提取完成: {total_pages}页, {total_chars}字符")
                
                return {
                    "status": "success",
                    "message": "PDF完整内容提取成功",
                    "data": result
                }
                
        except ImportError:
            raise HTTPException(status_code=500, detail="pdfplumber库未安装")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF内容提取失败: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提取PDF内容失败: {str(e)}")

# ========== 测试端点 ==========
@app.get("/api/test/pdf")
async def test_pdf_api():
    """测试PDF API是否工作"""
    return {
        "status": "success",
        "message": "PDF API测试成功",
        "data": {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "endpoints": [
                "POST /api/pdf/extract - 完整提取PDF内容",
                "GET /api/sops/{sop_id}/pdf-content - 预览PDF内容",
                "GET /api/files/{sop_id}/download - 下载文件",
                "GET /api/files/{sop_id}/info - 文件信息"
            ]
        }
    }

# ========== 标准库管理API ==========
@app.get("/api/standards")
async def get_all_standards():
    """获取所有技术标准"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, standard_no, category, 
                   effective_date, file_path, created_at
            FROM core_standards
            ORDER BY created_at DESC
        """)
        
        standards = cursor.fetchall()
        conn.close()
        
        # 转换为字典列表
        result = []
        for std in standards:
            result.append({
                "id": std[0],
                "name": std[1],
                "standard_no": std[2],
                "category": std[3],
                "effective_date": std[4],
                "file_path": std[5],
                "created_at": std[6]
            })
        
        return {
            "status": "success",
            "count": len(result),
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")

@app.get("/api/standards/search")
async def search_standards(
    q: Optional[str] = None,
    category: Optional[str] = None
):
    """搜索技术标准"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT id, name, standard_no, category, effective_date, file_path, created_at FROM core_standards WHERE 1=1"
        params = []
        
        if q:
            query += " AND (name LIKE ? OR standard_no LIKE ? OR category LIKE ?)"
            search_term = f"%{q}%"
            params.extend([search_term, search_term, search_term])
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        standards = cursor.fetchall()
        conn.close()
        
        # 转换为字典列表
        result = []
        for std in standards:
            result.append({
                "id": std[0],
                "name": std[1],
                "standard_no": std[2],
                "category": std[3],
                "effective_date": std[4],
                "file_path": std[5],
                "created_at": std[6]
            })
        
        return {
            "status": "success",
            "count": len(result),
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")

@app.post("/api/standards")
async def create_standard(
    name: str = Form(...),
    standard_no: str = Form(...),
    category: str = Form(...),
    effective_date: str = Form(None),  # 改为可选
    file: UploadFile = File(None)
):
    """创建新标准"""
    try:
        # 生成唯一ID
        import uuid
        standard_id = f"STD-{uuid.uuid4().hex[:12]}"
        
        # 处理文件上传
        file_path = None
        if file and file.filename:
            # 确保uploads目录存在
            uploads_dir = os.path.join(os.path.dirname(__file__), "..", "data", "uploads")
            os.makedirs(uploads_dir, exist_ok=True)
            
            # 生成安全的文件名
            safe_filename = f"{standard_id}_{file.filename}"
            file_path = os.path.join("data", "uploads", safe_filename)
            actual_path = os.path.join(os.path.dirname(__file__), "..", file_path)
            
            # 保存文件
            with open(actual_path, "wb") as f:
                content = await file.read()
                f.write(content)
        
        # 如果没有提供生效日期，使用当前日期
        if not effective_date:
            effective_date = datetime.now().strftime("%Y-%m-%d")
        
        # 插入数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO core_standards (id, name, standard_no, category, effective_date, file_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (standard_id, name, standard_no, category, effective_date, file_path))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": "标准创建成功",
            "data": {
                "id": standard_id,
                "name": name,
                "standard_no": standard_no,
                "category": category,
                "effective_date": effective_date,
                "file_path": file_path
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建标准失败: {str(e)}")

@app.get("/api/standards/{standard_id}")
async def get_standard(standard_id: str):
    """根据ID获取单个标准"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, standard_no, category, effective_date, file_path, created_at
            FROM core_standards
            WHERE id = ?
        """, (standard_id,))
        
        std = cursor.fetchone()
        conn.close()
        
        if not std:
            raise HTTPException(status_code=404, detail=f"未找到标准: {standard_id}")
        
        return {
            "status": "success",
            "message": "获取标准成功",
            "data": {
                "id": std[0],
                "name": std[1],
                "standard_no": std[2],
                "category": std[3],
                "effective_date": std[4],
                "file_path": std[5],
                "created_at": std[6]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询标准失败: {str(e)}")

@app.delete("/api/standards/{standard_id}")
async def delete_standard(standard_id: str):
    """删除标准"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 先检查标准是否存在
        cursor.execute("SELECT file_path FROM core_standards WHERE id = ?", (standard_id,))
        std = cursor.fetchone()
        
        if not std:
            raise HTTPException(status_code=404, detail=f"未找到标准: {standard_id}")
        
        # 删除关联的文件（如果有）
        file_path = std[0]
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass  # 如果文件删除失败，继续删除数据库记录
        
        # 删除数据库记录
        cursor.execute("DELETE FROM core_standards WHERE id = ?", (standard_id,))
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": "标准删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除标准失败: {str(e)}")

@app.put("/api/standards/{standard_id}")
async def update_standard(
    standard_id: str,
    name: str = Form(...),
    standard_no: str = Form(...),
    category: str = Form(...),
    effective_date: str = Form(None),
    file: UploadFile = File(None)
):
    """更新标准"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查标准是否存在
        cursor.execute("SELECT file_path FROM core_standards WHERE id = ?", (standard_id,))
        std = cursor.fetchone()
        
        if not std:
            raise HTTPException(status_code=404, detail=f"未找到标准: {standard_id}")
        
        current_file_path = std[0]
        
        # 处理文件更新
        new_file_path = current_file_path
        if file and file.filename:
            # 删除旧文件（如果有）
            if current_file_path and os.path.exists(current_file_path):
                try:
                    os.remove(current_file_path)
                except:
                    pass
            
            # 保存新文件
            uploads_dir = os.path.join(os.path.dirname(__file__), "..", "data", "uploads")
            os.makedirs(uploads_dir, exist_ok=True)
            
            safe_filename = f"{standard_id}_{file.filename}"
            new_file_path = os.path.join("data", "uploads", safe_filename)
            actual_path = os.path.join(os.path.dirname(__file__), "..", new_file_path)
            
            with open(actual_path, "wb") as f:
                content = await file.read()
                f.write(content)
        
        # 如果没有提供生效日期，保持原值
        if not effective_date:
            cursor.execute("SELECT effective_date FROM core_standards WHERE id = ?", (standard_id,))
            effective_date = cursor.fetchone()[0]
        
        # 更新数据库
        cursor.execute("""
            UPDATE core_standards 
            SET name = ?, standard_no = ?, category = ?, effective_date = ?, file_path = ?
            WHERE id = ?
        """, (name, standard_no, category, effective_date, new_file_path, standard_id))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": "标准更新成功",
            "data": {
                "id": standard_id,
                "name": name,
                "standard_no": standard_no,
                "category": category,
                "effective_date": effective_date,
                "file_path": new_file_path
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新标准失败: {str(e)}")

# ========== 标准与SOP关联API ==========
@app.get("/api/standards/{standard_id}/sops")
async def get_standard_sops(standard_id: str):
    """获取标准关联的所有SOP"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 首先检查标准是否存在
        cursor.execute("SELECT id, standard_no, name FROM core_standards WHERE id = ?", (standard_id,))
        standard_data = cursor.fetchone()
        
        if not standard_data:
            conn.close()
            return {
                "status": "success",
                "message": f"标准 {standard_id} 不存在",
                "data": []
            }
        
        # 查询关联的SOP
        cursor.execute("""
            SELECT DISTINCT m.sop_id, s.id, s.name, s.version, s.department, s.category, s.created_at
            FROM mapping_matrix m
            JOIN safety_operation_procedures s ON m.sop_id = s.id
            WHERE m.standard_id = ?
        """, (standard_id,))
        
        sops = cursor.fetchall()
        conn.close()
        
        result = []
        for sop in sops:
            result.append({
                "id": sop[1] if sop[1] else sop[0],  # 使用s.id，如果不存在则使用m.sop_id
                "name": sop[2],  # 使用s.name作为标题
                "version": sop[3],  # 版本号
                "department": sop[4],  # 部门
                "category": sop[5],  # 分类
                "created_at": sop[6]  # 创建时间
            })
        
        return {
            "status": "success",
            "count": len(result),
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询标准关联SOP失败: {str(e)}")

# ========== 直接PDF文件服务端点（绕过StaticFiles问题） ==========
@app.get("/api/files/pdf/{standard_id}")
async def get_pdf_file(standard_id: str):
    """直接提供PDF文件服务，解决StaticFiles的编码问题"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取标准信息
        cursor.execute("SELECT file_path FROM core_standards WHERE id = ?", (standard_id,))
        standard_data = cursor.fetchone()
        conn.close()
        
        if not standard_data:
            raise HTTPException(status_code=404, detail=f"标准 {standard_id} 不存在")
        
        file_path = standard_data[0]
        if not file_path:
            raise HTTPException(status_code=404, detail=f"标准 {standard_id} 没有关联PDF文件")
        
        # 提取文件名
        if '\\' in file_path or '/' in file_path:
            file_name = os.path.basename(file_path)
        else:
            file_name = file_path
        
        # 构建实际文件路径
        base_dir = os.path.dirname(__file__)
        uploads_dir = os.path.join(base_dir, "..", "data", "uploads")
        actual_path = os.path.join(uploads_dir, file_name)
        
        # 检查文件是否存在
        if not os.path.exists(actual_path):
            # 尝试解码+号
            decoded_file_name = file_name.replace('%2B', '+')
            actual_path = os.path.join(uploads_dir, decoded_file_name)
            
            if not os.path.exists(actual_path):
                # 尝试原始文件名
                actual_path = os.path.join(uploads_dir, file_name.replace('+', ' '))
                
                if not os.path.exists(actual_path):
                    raise HTTPException(status_code=404, detail=f"PDF文件不存在: {file_name}")
        
        # 返回文件 - 设置为inline以便在浏览器中显示
        return FileResponse(
            path=actual_path,
            filename=file_name,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'inline; filename="{file_name}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件服务错误: {str(e)}")

# ========== SOP与标准关联管理API ==========
@app.post("/api/mappings")
async def create_mapping(
    sop_id: str = Form(...),
    standard_id: str = Form(...),
    sop_clause: Optional[str] = Form(None),
    standard_clause: Optional[str] = Form(None),
    relevance_score: Optional[float] = Form(0.5)
):
    """创建SOP与标准的关联"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查SOP是否存在
        cursor.execute("SELECT id FROM safety_operation_procedures WHERE id = ?", (sop_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="SOP未找到")
        
        # 检查标准是否存在
        cursor.execute("SELECT id FROM core_standards WHERE id = ?", (standard_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="标准未找到")
        
        # 检查是否已存在关联
        cursor.execute("""
            SELECT id FROM mapping_matrix 
            WHERE sop_id = ? AND standard_id = ? 
            AND sop_clause = ? AND standard_clause = ?
        """, (sop_id, standard_id, sop_clause, standard_clause))
        
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="关联已存在")
        
        # 创建关联
        cursor.execute("""
            INSERT INTO mapping_matrix 
            (sop_id, standard_id, sop_clause, standard_clause, relevance_score, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (sop_id, standard_id, sop_clause, standard_clause, relevance_score))
        
        conn.commit()
        mapping_id = cursor.lastrowid
        conn.close()
        
        return {
            "status": "success",
            "message": "关联创建成功",
            "data": {
                "mapping_id": mapping_id,
                "sop_id": sop_id,
                "standard_id": standard_id,
                "sop_clause": sop_clause,
                "standard_clause": standard_clause,
                "relevance_score": relevance_score
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建关联失败: {str(e)}")

@app.delete("/api/mappings/{mapping_id}")
async def delete_mapping(mapping_id: int):
    """删除SOP与标准的关联"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM mapping_matrix WHERE id = ?", (mapping_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="关联未找到")
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": "关联删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除关联失败: {str(e)}")

@app.get("/api/mappings")
async def get_all_mappings(
    sop_id: Optional[str] = None,
    standard_id: Optional[str] = None
):
    """获取所有关联，支持按SOP或标准过滤"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT m.id, m.sop_id, m.standard_id, m.sop_clause, 
                   m.standard_clause, m.relevance_score, m.created_at,
                   s.name as sop_name, std.name as standard_name
            FROM mapping_matrix m
            LEFT JOIN safety_operation_procedures s ON m.sop_id = s.id
            LEFT JOIN core_standards std ON m.standard_id = std.id
            WHERE 1=1
        """
        params = []
        
        if sop_id:
            query += " AND m.sop_id = ?"
            params.append(sop_id)
        
        if standard_id:
            query += " AND m.standard_id = ?"
            params.append(standard_id)
        
        query += " ORDER BY m.created_at DESC"
        
        cursor.execute(query, params)
        mappings = cursor.fetchall()
        conn.close()
        
        # 转换为字典列表
        result = []
        for mapping in mappings:
            result.append({
                "id": mapping[0],
                "sop_id": mapping[1],
                "standard_id": mapping[2],
                "sop_clause": mapping[3],
                "standard_clause": mapping[4],
                "relevance_score": mapping[5],
                "created_at": mapping[6],
                "sop_name": mapping[7],
                "standard_name": mapping[8]
            })
        
        return {
            "status": "success",
            "count": len(result),
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询关联失败: {str(e)}")

# ========== SOP关联的标准API ==========
@app.get("/api/sops/{sop_id}/standards")
async def get_sop_standards(sop_id: str):
    """获取SOP关联的所有标准"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询关联的标准（包含关联ID）
        cursor.execute("""
            SELECT DISTINCT m.id, m.standard_id, s.name, s.standard_no, s.category, 
                   s.effective_date, s.file_path, m.relevance_score
            FROM mapping_matrix m
            LEFT JOIN core_standards s ON m.standard_id = s.id
            WHERE m.sop_id = ?
            ORDER BY m.relevance_score DESC
        """, (sop_id,))
        
        standards = cursor.fetchall()
        conn.close()
        
        result = []
        for std in standards:
            result.append({
                "mapping_id": std[0],  # 关联ID
                "standard_id": std[1],
                "name": std[2],
                "standard_no": std[3],
                "category": std[4],
                "effective_date": std[5],
                "file_path": std[6],
                "relevance_score": std[7]
            })
        
        return {
            "status": "success",
            "count": len(result),
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询SOP关联标准失败: {str(e)}")

# ========== 审核记录API ==========
@app.get("/api/audit-results")
async def get_audit_results(
    sop_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """获取审核记录，支持按SOP ID过滤"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询
        query = """
            SELECT id, sop_id, audit_date, auditor, 
                   overall_score, status, report_path, created_at
            FROM audit_results
            WHERE 1=1
        """
        params = []
        
        if sop_id:
            query += " AND sop_id = ?"
            params.append(sop_id)
        
        # 添加排序和分页
        query += " ORDER BY audit_date DESC, created_at DESC"
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        audits = cursor.fetchall()
        
        # 获取总数
        count_query = "SELECT COUNT(*) FROM audit_results"
        count_params = []
        
        if sop_id:
            count_query += " WHERE sop_id = ?"
            count_params.append(sop_id)
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        # 转换为字典列表
        result = []
        for audit in audits:
            result.append({
                "id": audit[0],
                "sop_id": audit[1],
                "audit_date": audit[2],
                "auditor": audit[3],
                "overall_score": audit[4],
                "status": audit[5],
                "report_path": audit[6],
                "created_at": audit[7]
            })
        
        return {
            "status": "success",
            "message": f"成功获取 {len(result)} 条审核记录",
            "data": result,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取审核记录失败: {str(e)}")

@app.get("/api/sops/{sop_id}/audit-records")
async def get_sop_audit_records(sop_id: str, limit: int = 20):
    """获取特定SOP的审核记录（简化版）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, sop_id, audit_date, auditor, 
                   overall_score, status, report_path, created_at
            FROM audit_results
            WHERE sop_id = ?
            ORDER BY audit_date DESC, created_at DESC
            LIMIT ?
        """, (sop_id, limit))
        
        audits = cursor.fetchall()
        conn.close()
        
        # 转换为字典列表
        result = []
        for audit in audits:
            result.append({
                "id": audit[0],
                "sop_id": audit[1],
                "audit_date": audit[2],
                "auditor": audit[3],
                "overall_score": audit[4],
                "status": audit[5],
                "report_path": audit[6],
                "created_at": audit[7]
            })
        
        return {
            "status": "success",
            "message": f"成功获取 {len(result)} 条审核记录",
            "data": result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取审核记录失败: {str(e)}",
            "data": []
        }

# ========== 审核明细API ==========
@app.get("/api/audit-details/{audit_id}")
async def get_audit_details(audit_id: int):
    """获取特定审核记录的详细审核结论"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取审核明细
        cursor.execute("""
            SELECT id, audit_id, standard_id, sop_clause, standard_clause,
                   compliance_score, comments, recommendations
            FROM audit_details
            WHERE audit_id = ?
            ORDER BY id
        """, (audit_id,))
        
        details = cursor.fetchall()
        
        # 获取审核记录基本信息
        cursor.execute("""
            SELECT id, sop_id, audit_date, auditor, overall_score, status
            FROM audit_results
            WHERE id = ?
        """, (audit_id,))
        
        audit_info = cursor.fetchone()
        
        conn.close()
        
        if not audit_info:
            raise HTTPException(status_code=404, detail=f"未找到审核记录: {audit_id}")
        
        # 转换为字典列表
        details_list = []
        for detail in details:
            details_list.append({
                "id": detail[0],
                "audit_id": detail[1],
                "standard_id": detail[2],
                "sop_clause": detail[3],
                "standard_clause": detail[4],
                "compliance_score": detail[5],
                "comments": detail[6],
                "recommendations": detail[7]
            })
        
        # 计算统计信息
        total_details = len(details_list)
        avg_score = sum(d['compliance_score'] for d in details_list) / total_details if total_details > 0 else 0
        
        return {
            "status": "success",
            "message": f"成功获取 {total_details} 条审核明细",
            "data": {
                "audit_info": {
                    "id": audit_info[0],
                    "sop_id": audit_info[1],
                    "audit_date": audit_info[2],
                    "auditor": audit_info[3],
                    "overall_score": audit_info[4],
                    "status": audit_info[5]
                },
                "details": details_list,
                "statistics": {
                    "total_details": total_details,
                    "average_score": round(avg_score, 2),
                    "max_score": max(d['compliance_score'] for d in details_list) if details_list else 0,
                    "min_score": min(d['compliance_score'] for d in details_list) if details_list else 0
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取审核明细失败: {str(e)}")

@app.get("/api/audits/{audit_id}/summary")
async def get_audit_summary(audit_id: int):
    """获取审核摘要（简化版，用于列表中的快速查看）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取审核记录基本信息
        cursor.execute("""
            SELECT ar.id, ar.sop_id, ar.audit_date, ar.auditor, 
                   ar.overall_score, ar.status, s.name as sop_name
            FROM audit_results ar
            LEFT JOIN safety_operation_procedures s ON ar.sop_id = s.id
            WHERE ar.id = ?
        """, (audit_id,))
        
        audit_info = cursor.fetchone()
        
        if not audit_info:
            raise HTTPException(status_code=404, detail=f"未找到审核记录: {audit_id}")
        
        # 获取审核明细数量
        cursor.execute("SELECT COUNT(*) FROM audit_details WHERE audit_id = ?", (audit_id,))
        detail_count = cursor.fetchone()[0]
        
        # 获取符合性统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN compliance_score >= 0.8 THEN 1 ELSE 0 END) as good_count,
                SUM(CASE WHEN compliance_score >= 0.6 AND compliance_score < 0.8 THEN 1 ELSE 0 END) as medium_count,
                SUM(CASE WHEN compliance_score < 0.6 THEN 1 ELSE 0 END) as poor_count
            FROM audit_details 
            WHERE audit_id = ?
        """, (audit_id,))
        
        stats = cursor.fetchone()
        
        conn.close()
        
        return {
            "status": "success",
            "data": {
                "audit_id": audit_info[0],
                "sop_id": audit_info[1],
                "sop_name": audit_info[6],
                "audit_date": audit_info[2],
                "auditor": audit_info[3],
                "overall_score": audit_info[4],
                "status": audit_info[5],
                "detail_count": detail_count,
                "compliance_stats": {
                    "total": stats[0] if stats else 0,
                    "good": stats[1] if stats else 0,
                    "medium": stats[2] if stats else 0,
                    "poor": stats[3] if stats else 0
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取审核摘要失败: {str(e)}",
            "data": None
        }

# ========== 部门管理API ==========

@app.get("/api/departments")
async def get_departments(active_only: bool = False, include_inactive: bool = False):
    """获取部门列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if active_only:
            query = "SELECT * FROM departments WHERE is_active = 1 ORDER BY sort_order, name"
        elif include_inactive:
            query = "SELECT * FROM departments ORDER BY sort_order, name"
        else:
            query = "SELECT * FROM departments WHERE is_active = 1 ORDER BY sort_order, name"
        
        cursor.execute(query)
        departments = cursor.fetchall()
        conn.close()
        
        departments_list = []
        for dept in departments:
            departments_list.append({
                "id": dept["id"],
                "name": dept["name"],
                "code": dept["code"],
                "description": dept["description"],
                "is_active": bool(dept["is_active"]),
                "sort_order": dept["sort_order"],
                "created_at": dept["created_at"],
                "updated_at": dept["updated_at"]
            })
        
        return {
            "status": "success",
            "message": "获取部门列表成功",
            "data": departments_list,
            "count": len(departments_list)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取部门列表失败: {str(e)}",
            "data": None
        }

@app.get("/api/departments/active")
async def get_active_departments():
    """获取启用的部门列表（用于下拉框）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, code 
            FROM departments 
            WHERE is_active = 1 
            ORDER BY sort_order, name
        """)
        
        departments = cursor.fetchall()
        conn.close()
        
        departments_list = []
        for dept in departments:
            departments_list.append({
                "id": dept["id"],
                "name": dept["name"],
                "code": dept["code"]
            })
        
        return {
            "status": "success",
            "message": "获取启用的部门列表成功",
            "data": departments_list
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取启用的部门列表失败: {str(e)}",
            "data": None
        }

@app.get("/api/departments/{department_id}")
async def get_department(department_id: int):
    """获取单个部门详情"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM departments WHERE id = ?", (department_id,))
        dept = cursor.fetchone()
        conn.close()
        
        if not dept:
            raise HTTPException(status_code=404, detail=f"部门不存在: {department_id}")
        
        return {
            "status": "success",
            "message": "获取部门详情成功",
            "data": {
                "id": dept["id"],
                "name": dept["name"],
                "code": dept["code"],
                "description": dept["description"],
                "is_active": bool(dept["is_active"]),
                "sort_order": dept["sort_order"],
                "created_at": dept["created_at"],
                "updated_at": dept["updated_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取部门详情失败: {str(e)}",
            "data": None
        }

@app.post("/api/departments")
async def create_department(
    name: str = Form(...),
    code: str = Form(...),
    description: str = Form(None),
    is_active: bool = Form(True),
    sort_order: int = Form(0)
):
    """创建新部门"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查部门名称是否已存在
        cursor.execute("SELECT id FROM departments WHERE name = ? OR code = ?", (name, code))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="部门名称或代码已存在")
        
        # 插入新部门
        cursor.execute("""
            INSERT INTO departments (name, code, description, is_active, sort_order, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (name, code, description, 1 if is_active else 0, sort_order))
        
        department_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": "部门创建成功",
            "data": {
                "id": department_id,
                "name": name,
                "code": code
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "error",
            "message": f"创建部门失败: {str(e)}",
            "data": None
        }

@app.put("/api/departments/{department_id}")
async def update_department(
    department_id: int,
    name: str = Form(None),
    code: str = Form(None),
    description: str = Form(None),
    is_active: bool = Form(None),
    sort_order: int = Form(None)
):
    """更新部门信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查部门是否存在
        cursor.execute("SELECT id FROM departments WHERE id = ?", (department_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"部门不存在: {department_id}")
        
        # 检查名称和代码是否与其他部门冲突
        if name:
            cursor.execute("SELECT id FROM departments WHERE name = ? AND id != ?", (name, department_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="部门名称已存在")
        
        if code:
            cursor.execute("SELECT id FROM departments WHERE code = ? AND id != ?", (code, department_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="部门代码已存在")
        
        # 构建更新语句
        update_fields = []
        update_values = []
        
        if name is not None:
            update_fields.append("name = ?")
            update_values.append(name)
        
        if code is not None:
            update_fields.append("code = ?")
            update_values.append(code)
        
        if description is not None:
            update_fields.append("description = ?")
            update_values.append(description)
        
        if is_active is not None:
            update_fields.append("is_active = ?")
            update_values.append(1 if is_active else 0)
        
        if sort_order is not None:
            update_fields.append("sort_order = ?")
            update_values.append(sort_order)
        
        # 总是更新updated_at
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        if update_fields:
            update_values.append(department_id)
            update_query = f"UPDATE departments SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(update_query, update_values)
            conn.commit()
        
        conn.close()
        
        return {
            "status": "success",
            "message": "部门更新成功",
            "data": {
                "id": department_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "error",
            "message": f"更新部门失败: {str(e)}",
            "data": None
        }

@app.delete("/api/departments/{department_id}")
async def delete_department(department_id: int):
    """删除部门（软删除，设置为未启用）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查部门是否存在
        cursor.execute("SELECT id FROM departments WHERE id = ?", (department_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"部门不存在: {department_id}")
        
        # 检查是否有SOP使用此部门
        cursor.execute("SELECT COUNT(*) FROM safety_operation_procedures WHERE department = (SELECT name FROM departments WHERE id = ?)", (department_id,))
        sop_count = cursor.fetchone()[0]
        
        if sop_count > 0:
            raise HTTPException(status_code=400, detail=f"有 {sop_count} 个SOP使用此部门，无法删除")
        
        # 软删除：设置为未启用
        cursor.execute("UPDATE departments SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (department_id,))
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": "部门已禁用",
            "data": {
                "id": department_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "error",
            "message": f"删除部门失败: {str(e)}",
            "data": None
        }

# ========== 标准分类管理API ==========

# 导入分类管理API
try:
    from category_api import router as category_router
    app.include_router(category_router)
    print("[SUCCESS] 标准分类管理API路由注册成功")
except Exception as e:
    print(f"[WARNING] 标准分类管理API路由注册失败: {e}")

if __name__ == "__main__":
    import uvicorn
    print("启动安全智能审核系统后端服务...")
    print("服务地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    
    # 导入并设置仪表板API路由
    try:
        from dashboard_api import setup_dashboard_routes
        setup_dashboard_routes(app)
        print("[SUCCESS] 仪表板API路由已注册")
    except ImportError as e:
        print(f"[WARNING] 无法导入仪表板API: {e}")
    except Exception as e:
        print(f"[WARNING] 设置仪表板API路由失败: {e}")
    
    # 打印路由
    print("\n已注册的路由:")
    for route in app.routes:
        if hasattr(route, "path") and not route.path.startswith("/static"):
            methods = getattr(route, "methods", ["未知"])
            print(f"  {route.path} - {methods}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)