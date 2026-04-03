"""
部门管理API模块
提供部门分类的自定义管理功能
"""

from fastapi import APIRouter, HTTPException, Form
from typing import List, Optional
import sqlite3
from datetime import datetime

router = APIRouter(prefix="/api/departments", tags=["departments"])

def get_db_connection():
    """获取数据库连接"""
    import os
    from pathlib import Path
    db_path = Path("E:/openclaw/projects/safety-audit-system/data/safety_audit.db")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # 返回字典格式的行
    return conn

# ========== 部门管理API ==========

@router.get("")
async def get_departments(
    active_only: bool = False,
    include_inactive: bool = False
):
    """获取部门列表
    
    Args:
        active_only: 是否只返回启用的部门（默认false，返回所有）
        include_inactive: 是否包含未启用的部门（默认false）
    """
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
        raise HTTPException(status_code=500, detail=f"获取部门列表失败: {str(e)}")

@router.get("/active")
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
        raise HTTPException(status_code=500, detail=f"获取启用的部门列表失败: {str(e)}")

@router.get("/{department_id}")
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
        raise HTTPException(status_code=500, detail=f"获取部门详情失败: {str(e)}")

@router.post("")
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
        raise HTTPException(status_code=500, detail=f"创建部门失败: {str(e)}")

@router.put("/{department_id}")
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
        raise HTTPException(status_code=500, detail=f"更新部门失败: {str(e)}")

@router.delete("/{department_id}")
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
        raise HTTPException(status_code=500, detail=f"删除部门失败: {str(e)}")

def setup_department_routes(app):
    """设置部门管理路由"""
    app.include_router(router)
    print("[DEPARTMENT API] 部门管理API路由已注册")