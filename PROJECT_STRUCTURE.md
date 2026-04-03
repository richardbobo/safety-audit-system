# 安全智能审核系统 - 纯净版项目结构

## 项目概述
这是一个安全操作规程智能审核系统，包含完整的前后端功能。

## 文件结构

### 根目录
```
safety-audit-system/
├── .env                    # 环境变量配置
├── .env.example           # 环境变量配置示例
├── .gitignore            # Git忽略文件
├── README.md             # 项目说明文档
├── README-CLEAN.md       # 清理说明文档
├── check-security.py     # 安全检查脚本
├── check_db.py          # 数据库检查工具
└── start-safe.bat       # Windows启动脚本
```

### backend/ - 后端服务
```
backend/
├── main_fixed.py                    # 主后端服务文件
├── dashboard_api.py                 # 仪表板API接口
└── ai_audit_api_deterministic.py    # AI智能审核API
```

### frontend/ - 前端界面
```
frontend/
├── dashboard.html                  # 仪表板页面
├── dashboard.js                    # 仪表板JavaScript逻辑
├── sops.html                       # SOP管理页面
├── standards.html                  # 标准库管理页面
├── sop-detail-clean-fixed.html     # SOP详情页面
├── styles.css                      # 全局样式文件
├── config.js                       # 前端配置
├── ai-audit-fixed.js               # AI审核JavaScript逻辑
├── favicon.ico                     # 网站图标
└── README.md                       # 前端说明文档
```

### data/ - 数据存储
```
data/
├── safety_audit.db                 # SQLite数据库文件
└── uploads/                        # 上传文件存储
    ├── 67b758c6-05c7-4706-860f-65d26dc44f0f.pdf
    ├── AA-PFA3P-14.2-AQ-001 维修作业单位安全操作规程.pdf
    ├── AA-PFA3P-14.2-AQ-011 手动操作程序安全操作规程.pdf
    ├── AA-PFA3P-14.2-AQ-308 提供设备安全操作规程.pdf
    ├── AA-PFA3P-14.2-AQ-401 注塑设备安全操作规程.pdf
    ├── AA-PFA3P-14.2-AQ-502 PAD成型设备安全操作规程.pdf
    ├── AA-PFA3P-14.2-AQ-510 BA0成型设备安全操作规程.pdf
    ├── GB+5083-2023.pdf
    ├── SOP-92b98fa9c246_AA-PFA3P-14.2-AQ-701-操作员安全操作规程.pdf
    ├── SOP-a7d8c73838fa_AA-PFA3P-14.2-AQ-011 手动操作程序安全操作规程.pdf
    ├── SOP-fcd05df760ca_AA-PFA3P-14.2-AQ-703-新员工安全操作规程1.01.pdf
    ├── STD-1b4267ca8de2_GBT+44686-2024+危险化学品仓库.pdf
    ├── STD-94c0202ba112_AA-PFA3P-14.2-AQ-011 手动操作程序安全操作规程.pdf
    └── STD-fe1ab919d6d7_GB+39800.9-2024+个体防护装备配备规范+第9部分：焊工.pdf
```

## 系统功能

### 1. 仪表板 (dashboard.html)
- 系统概览和关键指标统计
- 图表展示SOP部门分布和级别分布
- 实时数据监控

### 2. SOP管理 (sops.html)
- SOP列表查看和搜索
- SOP详情查看
- SOP状态管理

### 3. 标准库管理 (standards.html)
- 技术标准库管理
- 标准状态跟踪
- 标准与SOP关联

### 4. SOP详情 (sop-detail-clean-fixed.html)
- SOP详细信息展示
- 关联标准查看
- 审核记录查看

## 技术栈

### 后端
- **框架**: FastAPI (Python)
- **数据库**: SQLite
- **API**: RESTful API设计
- **端口**: 8000

### 前端
- **HTML/CSS**: 原生HTML5 + CSS3
- **JavaScript**: ES6 + Chart.js
- **图标**: Font Awesome
- **样式**: 响应式设计

### 第三方依赖
- Chart.js: 数据可视化
- Font Awesome: 图标库

## 启动方式

### 后端服务
```bash
cd projects/safety-audit-system/backend
python main_fixed.py
```

### 访问地址
- 后端API文档: http://localhost:8000/docs
- 后端健康检查: http://localhost:8000/health
- 前端页面: http://localhost:8000/static/[page].html

### 主要页面
1. SOP管理: http://localhost:8000/static/sops.html
2. 标准库管理: http://localhost:8000/static/standards.html
3. 仪表板: http://localhost:8000/static/dashboard.html
4. SOP详情: http://localhost:8000/static/sop-detail-clean-fixed.html

## 数据库
- 文件: `data/safety_audit.db`
- 类型: SQLite
- 包含表: sops, standards, audits, files, mappings等

## 清理说明
已删除以下文件：
1. 所有测试HTML文件 (test-*.html)
2. 临时dashboard文件 (dashboard-*.html, 除了dashboard.html)
3. Python编译文件 (*.pyc)
4. 测试上传文件 (test_upload.txt)

## 注意事项
1. 确保Python环境已安装FastAPI、uvicorn等依赖
2. 首次运行前可能需要安装依赖：`pip install fastapi uvicorn sqlite3`
3. 数据库文件包含示例数据，可直接使用
4. 所有页面使用统一的导航栏和样式

---
*项目清理完成时间: 2026-04-01 10:16 (Asia/Shanghai)*
*清理者: 灰灰 🦊*