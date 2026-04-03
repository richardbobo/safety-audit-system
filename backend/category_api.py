#!/usr/bin/env python3
"""
标准分类管理API
"""

from fastapi import APIRouter, HTTPException, Form, Query
from typing import List, Optional
import sqlite3
from datetime import datetime

router = APIRouter(prefix="/api/categories", tags=["categories"])

def get_db_connection():
    """获取数据库连接"""
    import os
    from pathlib import Path
    
    db_path = Path(__file__).parent.parent / "data" / "safety_audit.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/")
async def get_categories(include_inactive: bool = Query(False, description="是否包含禁用的分类")):
    """获取所有分类"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if include_inactive:
            cursor.execute('''
                SELECT id, name, code, description, is_active, sort_order, 
                       created_at, updated_at
                FROM categories
                ORDER BY sort_order, id
            ''')
        else:
            cursor.execute('''
                SELECT id, name, code, description, is_active, sort_order, 
                       created_at, updated_at
                FROM categories
                WHERE is_active = 1
                ORDER BY sort_order, id
            ''')
        
        categories = cursor.fetchall()
        
        result = []
        for cat in categories:
            result.append({
                "id": cat["id"],
                "name": cat["name"],
                "code": cat["code"],
                "description": cat["description"],
                "is_active": bool(cat["is_active"]),
                "sort_order": cat["sort_order"],
                "created_at": cat["created_at"],
                "updated_at": cat["updated_at"]
            })
        
        return {
            "status": "success",
            "message": "获取分类列表成功",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类列表失败: {str(e)}")
    finally:
        conn.close()

@router.get("/active")
async def get_active_categories():
    """获取启用的分类列表（用于下拉框）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, code
            FROM categories
            WHERE is_active = 1
            ORDER BY sort_order, name
        ''')
        
        categories = cursor.fetchall()
        
        result = []
        for cat in categories:
            result.append({
                "id": cat["id"],
                "name": cat["name"],
                "code": cat["code"]
            })
        
        return {
            "status": "success",
            "message": "获取启用的分类列表成功",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类列表失败: {str(e)}")
    finally:
        conn.close()

@router.get("/{category_id}")
async def get_category(category_id: int):
    """获取单个分类详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, code, description, is_active, sort_order, 
                   created_at, updated_at
            FROM categories
            WHERE id = ?
        ''', (category_id,))
        
        cat = cursor.fetchone()
        
        if not cat:
            raise HTTPException(status_code=404, detail="分类不存在")
        
        return {
            "status": "success",
            "message": "获取分类成功",
            "data": {
                "id": cat["id"],
                "name": cat["name"],
                "code": cat["code"],
                "description": cat["description"],
                "is_active": bool(cat["is_active"]),
                "sort_order": cat["sort_order"],
                "created_at": cat["created_at"],
                "updated_at": cat["updated_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类失败: {str(e)}")
    finally:
        conn.close()

@router.post("/")
async def create_category(
    name: str = Form(...),
    code: str = Form(...),
    description: str = Form(""),
    sort_order: int = Form(0),
    is_active: bool = Form(True)
):
    """创建新分类"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 验证分类代码格式
        if not code.islower() or not code.replace('_', '').isalnum():
            raise HTTPException(status_code=400, detail="分类代码只能包含小写字母、数字和下划线")
        
        # 检查名称和代码是否已存在
        cursor.execute('SELECT id FROM categories WHERE name = ? OR code = ?', (name, code))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="分类名称或代码已存在")
        
        # 插入新分类
        cursor.execute('''
            INSERT INTO categories (name, code, description, sort_order, is_active, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, code, description, sort_order, 1 if is_active else 0, datetime.now()))
        
        category_id = cursor.lastrowid
        
        conn.commit()
        
        return {
            "status": "success",
            "message": "分类创建成功",
            "data": {"id": category_id}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"创建分类失败: {str(e)}")
    finally:
        conn.close()

@router.put("/{category_id}")
async def update_category(
    category_id: int,
    name: str = Form(None),
    code: str = Form(None),
    description: str = Form(None),
    sort_order: int = Form(None),
    is_active: bool = Form(None)
):
    """更新分类信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查分类是否存在
        cursor.execute('SELECT id FROM categories WHERE id = ?', (category_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="分类不存在")
        
        # 构建更新语句
        updates = []
        params = []
        
        if name is not None:
            # 检查名称是否已被其他分类使用
            cursor.execute('SELECT id FROM categories WHERE name = ? AND id != ?', (name, category_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="分类名称已被使用")
            updates.append("name = ?")
            params.append(name)
        
        if code is not None:
            # 验证分类代码格式
            if not code.islower() or not code.replace('_', '').isalnum():
                raise HTTPException(status_code=400, detail="分类代码只能包含小写字母、数字和下划线")
            # 检查代码是否已被其他分类使用
            cursor.execute('SELECT id FROM categories WHERE code = ? AND id != ?', (code, category_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="分类代码已被使用")
            updates.append("code = ?")
            params.append(code)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if sort_order is not None:
            updates.append("sort_order = ?")
            params.append(sort_order)
        
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)
        
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now())
            
            params.append(category_id)
            
            sql = f"UPDATE categories SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, params)
            
            conn.commit()
        
        return {
            "status": "success",
            "message": "分类更新成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"更新分类失败: {str(e)}")
    finally:
        conn.close()

@router.delete("/{category_id}")
async def delete_category(category_id: int):
    """删除分类（软删除，设置为禁用）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查分类是否存在
        cursor.execute('SELECT id FROM categories WHERE id = ?', (category_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="分类不存在")
        
        # 检查是否有标准使用此分类
        cursor.execute('SELECT COUNT(*) FROM core_standards WHERE category = (SELECT name FROM categories WHERE id = ?)', (category_id,))
        standard_count = cursor.fetchone()[0]
        
        if standard_count > 0:
            raise HTTPException(status_code=400, detail=f"无法删除分类，有 {standard_count} 个标准正在使用此分类")
        
        # 软删除：设置为禁用
        cursor.execute('''
            UPDATE categories 
            SET is_active = 0, updated_at = ?
            WHERE id = ?
        ''', (datetime.now(), category_id))
        
        conn.commit()
        
        return {
            "status": "success",
            "message": "分类已禁用"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"删除分类失败: {str(e)}")
    finally:
        conn.close()