# 安全智能审核系统 - 纯净版

## 📋 系统概述

这是一个为企业SOP（标准操作规程）提供智能化的合规性审核和管理平台。系统包含完整的SOP管理、技术标准关联、AI智能审核和审核记录查看功能。

## 🏗️ 系统架构

### 后端服务
1. **主后端服务** (端口: 8000)
   - 文件: `backend/main_fixed.py`
   - 功能: SOP管理、标准管理、审核记录API

2. **AI审核服务** (端口: 8002)
   - 文件: `backend/ai_audit_api_deterministic.py`
   - 功能: AI智能审核、进度查询、结果保存

### 前端页面
1. **SOP管理页面**
   - 文件: `frontend/sops.html`
   - 功能: SOP列表展示、搜索、状态显示

2. **SOP详情页面**
   - 文件: `frontend/sop-detail-clean-fixed.html`
   - 功能: SOP详情查看、关联标准管理、审核记录查看、AI审核

### 配置文件
- `frontend/config.js` - API配置
- `frontend/ai-audit-fixed.js` - AI审核前端库
- `frontend/styles.css` - 样式文件

## 🚀 快速启动

### 1. 启动后端服务
```bash
# 启动主后端服务 (端口8000)
cd projects/safety-audit-system
python backend/main_fixed.py

# 启动AI审核服务 (端口8002)
python backend/ai_audit_api_deterministic.py
```

或者使用启动脚本：
```bash
# Windows系统
start-fixed.bat
```

### 2. 访问前端页面
1. **SOP管理页面**: http://localhost:8000/static/sops.html
2. **SOP详情页面**: http://localhost:8000/static/sop-detail-clean-fixed.html?sop_id=SOP-d4a78d570a19

## 📊 数据库结构

### 核心表
1. **safety_operation_procedures** - SOP基本信息
2. **technical_standards** - 技术标准信息
3. **mapping_matrix** - SOP与标准关联关系
4. **audit_results** - 审核记录
5. **audit_details** - 审核明细

数据库文件: `data/safety_audit.db`

## 🔧 核心功能

### 1. SOP管理
- ✅ SOP列表展示（表格形式）
- ✅ 状态动态显示（已审核/待审核/未通过）
- ✅ 关联标准数量统计
- ✅ 搜索功能（按名称、编号）

### 2. SOP详情
- ✅ 基本信息展示（编号、版本、部门、创建时间）
- ✅ PDF内容提取（从PDF文件提取文本）
- ✅ 关联标准管理（关联/取消关联技术标准）
- ✅ 审核记录查看（历史审核记录）
- ✅ 审核明细查看（详细的审核结论）

### 3. AI审核
- ✅ 智能审核（基于关联标准进行AI审核）
- ✅ 进度条显示（实时显示审核进度）
- ✅ 结果展示（逐条款审核结果）
- ✅ 改进建议（提供具体的改进建议）

### 4. 审核记录
- ✅ 记录列表（按时间倒序显示）
- ✅ 审核明细（查看每条审核的详细结论）
- ✅ 统计信息（符合性统计、分数分布）

## 🔗 API接口

### 主后端API (端口8000)
```
GET    /api/sops                    # 获取所有SOP
GET    /api/sops/{sop_id}          # 获取单个SOP
GET    /api/sops/search            # 搜索SOP
GET    /api/sops/{sop_id}/standards # 获取SOP关联标准
GET    /api/sops/{sop_id}/pdf-content # 提取PDF内容
GET    /api/audit-results          # 获取审核记录
GET    /api/audit-details/{audit_id} # 获取审核明细
GET    /api/audits/{audit_id}/summary # 获取审核摘要
GET    /health                     # 健康检查
GET    /favicon.ico                # Favicon图标
```

### AI审核API (端口8002)
```
POST   /api/ai-audit/start         # 启动AI审核
GET    /api/ai-audit/status/{task_id} # 获取审核状态
GET    /api/ai-audit/history       # 获取AI审核历史
GET    /health                     # 健康检查
```

## 📁 文件结构

```
projects/safety-audit-system/
├── README.md                      # 项目说明
├── README-CLEAN.md               # 纯净版说明
├── start-fixed.bat               # 启动脚本
├── backend/
│   ├── main_fixed.py             # 主后端服务
│   ├── ai_audit_api_deterministic.py # AI审核服务
│   └── requirements.txt          # Python依赖
├── frontend/
│   ├── sops.html                 # SOP管理页面
│   ├── sop-detail-clean-fixed.html # SOP详情页面
│   ├── config.js                 # API配置
│   ├── ai-audit-fixed.js         # AI审核前端库
│   ├── styles.css                # 样式文件
│   ├── favicon.ico               # 网站图标
│   └── modules/
│       └── styles.css            # 模块样式
└── data/
    └── safety_audit.db           # SQLite数据库
```

## ⚙️ 技术栈

### 后端
- Python 3.8+
- FastAPI (Web框架)
- SQLite (数据库)
- pdfplumber (PDF处理)
- requests (HTTP请求)

### 前端
- HTML5/CSS3
- JavaScript (ES6)
- Font Awesome (图标)
- 原生API (无框架依赖)

### AI
- DeepSeek API (AI审核)
- 确定性输出 (temperature=0.1, top_p=0.9)
- 结构化输出 (JSON格式)

## 🎯 测试验证

### 1. 服务健康检查
```bash
# 主后端服务
curl http://localhost:8000/health

# AI审核服务
curl http://localhost:8002/health
```

### 2. 页面功能测试
1. 打开SOP管理页面，验证列表显示
2. 点击任意SOP，进入详情页面
3. 测试各个标签页功能
4. 启动AI审核，验证进度条显示
5. 查看审核记录和明细

### 3. API接口测试
```bash
# 获取SOP列表
curl http://localhost:8000/api/sops

# 获取单个SOP
curl http://localhost:8000/api/sops/SOP-d4a78d570a19

# 获取审核记录
curl http://localhost:8000/api/audit-results
```

## 🔄 备份与恢复

### 备份
项目已备份到: `projects/safety-audit-system-backup-20260327-221559`

### 恢复
如果需要恢复完整版本，请复制备份目录中的文件。

## 📞 技术支持

如果纯净版无法正常运行：
1. 检查服务是否正常启动（端口8000和8002）
2. 检查数据库文件是否存在（data/safety_audit.db）
3. 查看控制台错误信息
4. 从备份目录恢复完整版本

## 📈 版本信息

- **版本**: 纯净版 v1.0
- **清理时间**: 2026-03-27 22:15
- **文件数量**: 15个核心文件
- **状态**: 所有核心功能完整，测试文件已清理

---

**注意**: 此版本为纯净版，已移除所有测试文件和调试文件。如需完整版本，请从备份目录恢复。