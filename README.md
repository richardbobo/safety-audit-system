# 安全智能审核系统 - 纯净版

## 项目概述
安全智能审核系统是一个用于管理安全操作规程(SOP)和标准的智能系统，包含AI审核功能。本版本为纯净版，已移除所有测试和调试文件，只保留核心功能文件。

## 系统架构

### 后端服务
1. **主后端服务** (端口8000)
   - 文件: `backend/main_fixed.py`
   - 功能: SOP管理、标准管理、审核记录、用户管理、部门管理、分类管理
   - 特点: 已修复所有已知问题，API响应格式统一

2. **AI审核服务** (端口8002) - 可选
   - 文件: `backend/ai_audit_api_deterministic.py`
   - 功能: AI智能审核、任务管理、审核历史
   - 特点: 确定性输出、DeepSeek集成

### 前端界面
1. **仪表板** - `frontend/dashboard.html`
2. **SOP管理** - `frontend/sops.html` (已修复部门字段和编辑功能)
3. **标准库管理** - `frontend/standards.html` (已修复编辑功能和分类管理)
4. **部门管理** - `frontend/departments.html` (部门自定义管理)
5. **分类管理** - `frontend/categories.html` (标准分类自定义管理)
6. **标准详情** - `frontend/standard-detail-clean.html`
7. **SOP详情** - `frontend/sop-detail-clean-fixed.html`

### 核心功能模块
1. **AI审核模块** - `frontend/ai-audit-fixed.js`
2. **配置模块** - `frontend/config.js`
3. **仪表板逻辑** - `frontend/dashboard.js`
4. **标准详情逻辑** - `frontend/standard-detail-final.js`
5. **部门工具** - `frontend/department-utils.js`
6. **分类工具** - `frontend/category-utils.js`
7. **样式文件** - `frontend/styles.css`

## 已实现的核心功能

### 1. SOP管理功能
- ✅ 创建SOP（支持文件上传）
- ✅ 编辑SOP（支持不重新上传文件）
- ✅ 删除SOP（安全删除）
- ✅ 查看SOP详情
- ✅ 部门字段管理（自定义部门）

### 2. 标准库管理功能
- ✅ 上传标准文件（PDF/DOC/DOCX）
- ✅ 编辑标准信息
- ✅ 删除标准
- ✅ 查看标准详情
- ✅ 分类管理（自定义分类）

### 3. 自定义管理功能
- ✅ 部门自定义管理（增删改查）
- ✅ 分类自定义管理（增删改查）
- ✅ 显示顺序控制
- ✅ 启用/禁用状态管理

### 4. AI审核功能
- ✅ AI智能审核
- ✅ 审核历史记录
- ✅ 审核结果统计
- ✅ 确定性输出

### 5. 系统管理功能
- ✅ 用户管理
- ✅ 仪表板统计
- ✅ 文件管理
- ✅ 系统健康检查

## 启动指南

### 1. 启动主后端服务
```bash
cd projects/safety-audit-system
python backend/main_fixed.py
```
访问: http://localhost:8000

**注意**: 首次运行会自动创建必要的目录结构。

### 2. 启动AI审核服务（可选）
```bash
cd projects/safety-audit-system
python backend/ai_audit_api_deterministic.py
```
访问: http://localhost:8002/health

### 3. 访问前端界面
- 仪表板: http://localhost:8000/static/dashboard.html
- SOP管理: http://localhost:8000/static/sops.html
- 标准库: http://localhost:8000/static/standards.html
- 部门管理: http://localhost:8000/static/departments.html
- 分类管理: http://localhost:8000/static/categories.html

## 快速开始

### Windows用户
1. 确保已安装Python 3.7+
2. 安装依赖: `pip install -r requirements.txt`
3. 双击 `start.bat` 启动服务
4. 访问 http://localhost:8000/static/dashboard.html

### 默认账号
- **用户名**: admin
- **密码**: admin123

## 文件结构
```
safety-audit-system/
├── backend/                    # 后端服务
│   ├── main_fixed.py          # 主后端服务（已修复所有问题）
│   ├── ai_audit_api_deterministic.py  # AI审核服务
│   ├── dashboard_api.py       # 仪表板API
│   ├── department_api.py      # 部门管理API
│   └── category_api.py        # 分类管理API
├── frontend/                  # 前端界面
│   ├── dashboard.html         # 仪表板
│   ├── sops.html             # SOP管理（已修复）
│   ├── standards.html        # 标准库管理（已修复）
│   ├── departments.html      # 部门管理
│   ├── categories.html       # 分类管理
│   ├── sop-detail-clean-fixed.html # SOP详情
│   ├── standard-detail-clean.html  # 标准详情
│   ├── ai-audit-fixed.js     # AI审核模块
│   ├── config.js             # 配置模块
│   ├── dashboard.js          # 仪表板逻辑
│   ├── standard-detail-final.js  # 标准详情逻辑
│   ├── department-utils.js   # 部门工具函数
│   ├── category-utils.js     # 分类工具函数
│   ├── styles.css            # 主样式文件
│   ├── favicon.ico           # 网站图标
│   ├── lib/                  # 第三方库（PDF.js等）
│   └── modules/              # 系统模块
├── data/                     # 数据文件
│   ├── safety_audit.db      # SQLite数据库
│   └── uploads/             # 上传文件存储
├── .env                      # 环境配置
├── .env.example             # 环境配置示例
├── .gitignore               # Git忽略文件
├── requirements.txt         # Python依赖
├── start.bat                # Windows启动脚本
├── PROJECT_STRUCTURE.md     # 项目结构文档
└── README.md                # 本项目说明
```

## 技术特点

### 后端特点
- **轻量级**: 基于SQLite，无需复杂配置
- **高性能**: FastAPI框架，异步支持
- **安全**: 参数化查询，文件验证
- **可扩展**: 模块化设计，易于扩展

### 前端特点
- **响应式**: 适配不同屏幕尺寸
- **现代化**: 简洁直观的界面设计
- **高效**: 数据缓存，减少API调用
- **健壮**: 完善的错误处理

### 数据库特点
- **简单**: SQLite单文件数据库
- **便携**: 易于备份和迁移
- **完整**: 包含所有核心数据表
- **可维护**: 清晰的表结构设计

## 注意事项

### 环境要求
1. Python 3.7+ 环境
2. 必要的Python包（见requirements.txt）
3. 足够的磁盘空间（用于文件上传）

### 配置要求
1. 复制 `.env.example` 为 `.env`
2. 配置DeepSeek API密钥（如需AI审核）
3. 根据需要修改其他配置

### 安全建议
1. 首次登录后修改默认密码
2. 定期备份数据库文件
3. 限制上传文件类型和大小
4. 在生产环境使用HTTPS

## 维护指南

### 日常维护
1. **监控服务**: 确保服务正常运行
2. **备份数据**: 定期备份数据库和上传文件
3. **清理日志**: 清理不必要的日志文件
4. **更新依赖**: 定期更新Python包

### 故障排除
1. **服务无法启动**: 检查Python版本和依赖
2. **页面无法访问**: 检查服务端口和网络
3. **数据库错误**: 检查数据库文件权限
4. **上传失败**: 检查uploads目录权限

### 数据迁移
1. 停止所有服务
2. 备份当前数据库和上传文件
3. 复制到新环境
4. 更新配置文件
5. 重启服务

## 版本信息
- **当前版本**: 1.0.0 (纯净版)
- **生成时间**: 2026-04-02
- **文件数量**: 核心文件约30个
- **数据库**: 包含测试数据，可清空后重新初始化

## 支持与反馈
如有问题或建议，请参考项目文档或联系开发团队。

---
*纯净版已准备就绪，可直接用于生产环境*