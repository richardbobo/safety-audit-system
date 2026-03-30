# 安全智能审核系统

一个基于FastAPI和现代Web技术构建的企业安全操作规程(SOP)智能审核系统。

## 🎯 系统功能

### 核心功能
1. **SOP管理** - 创建、查看、搜索、管理安全操作规程
2. **标准库管理** - 管理安全标准和规范
3. **智能关联** - SOP与标准的智能关联管理
4. **文件管理** - PDF文件上传、下载、预览
5. **智能审核** - AI驱动的SOP合规性审核
6. **报告生成** - 自动生成审核报告

### 技术特性
- **前后端分离** - 现代化Web架构
- **RESTful API** - 完整的API接口设计
- **响应式设计** - 适配各种设备屏幕
- **实时搜索** - 快速检索SOP和标准
- **文件预览** - 在线PDF预览功能
- **智能分析** - 基于AI的合规性分析

## 🚀 快速开始

### 环境要求
- Python 3.8+
- SQLite3
- 现代浏览器（Chrome/Firefox/Edge）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/richardbobo/safety-audit-system.git
cd safety-audit-system
```

2. **安装依赖**
```bash
pip install -r backend/requirements.txt
```

3. **配置环境变量**
```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件，设置你的DeepSeek API密钥
# DEEPSEEK_API_KEY=your_actual_api_key_here
```

4. **初始化数据库**
```bash
python backend/init_database.py
```

5. **启动后端服务**
```bash
# Windows - 使用安全启动脚本
start-safe.bat

# 或手动启动
cd backend
python main_fixed.py
```

5. **访问前端**
```
打开浏览器访问：http://localhost:8000/static/index.html
```

### 主要页面
- **SOP管理**: `http://localhost:8000/static/sops.html`
- **标准库**: `http://localhost:8000/static/standards.html`
- **SOP详情**: `http://localhost:8000/static/sop-detail-fixed-v2.html?sop_id=SOP-xxx`
- **智能审核**: `http://localhost:8000/static/smart-audit.html`

## 📁 项目结构

```
safety-audit-system/
├── backend/                    # 后端代码
│   ├── main_fixed.py          # 主API服务（修复完整版）
│   ├── main.py               # 原始API服务
│   ├── config.py             # 配置文件
│   ├── database.py           # 数据库操作
│   ├── requirements.txt      # Python依赖
│   └── static/              # 静态文件服务
├── frontend/                 # 前端代码
│   ├── sops.html            # SOP管理页面
│   ├── standards.html       # 标准库页面
│   ├── sop-detail-fixed-v2.html  # SOP详情页（修复版）
│   ├── smart-audit.html     # 智能审核页面
│   ├── config.js            # 前端配置
│   └── styles.css           # 样式文件
├── data/                    # 数据目录
│   ├── safety_audit.db     # SQLite数据库
│   └── uploads/            # 上传文件存储
├── tools/                  # 工具脚本
├── README.md              # 项目说明
└── .gitignore            # Git忽略配置
```

## 🔧 API接口

### 核心API端点

#### 健康检查
- `GET /health` - 服务健康状态

#### SOP管理
- `GET /api/sops` - 获取所有SOP
- `POST /api/sops` - 创建新SOP
- `GET /api/sops/{id}` - 获取SOP详情
- `GET /api/sops/search` - 搜索SOP

#### 文件管理
- `GET /api/files/{id}/download` - 下载文件
- `GET /api/files/{id}/info` - 获取文件信息
- `GET /api/sops/{id}/pdf-content` - PDF预览

#### 标准库管理
- `GET /api/standards` - 获取所有标准
- `POST /api/standards` - 创建新标准
- `GET /api/standards/search` - 搜索标准

#### 关联管理
- `GET /api/mappings` - 获取所有关联
- `POST /api/mappings` - 创建关联
- `DELETE /api/mappings/{id}` - 删除关联
- `GET /api/sops/{id}/standards` - 获取SOP关联的标准

#### 智能审核
- `POST /api/audit/smart` - 智能审核
- `GET /api/audit/results/{id}` - 获取审核结果
- `GET /api/audit/history` - 审核历史记录

## 🛠️ 开发指南

### 后端开发
1. **API开发**: 在`backend/main_fixed.py`中添加新的API端点
2. **数据库操作**: 使用`backend/database.py`中的数据库连接函数
3. **文件处理**: 参考现有的文件上传和下载实现

### 前端开发
1. **页面开发**: 在`frontend/`目录下创建新的HTML文件
2. **API调用**: 使用`frontend/config.js`中的API配置
3. **样式设计**: 修改`frontend/styles.css`文件

### 数据库设计
系统使用SQLite数据库，主要表结构：
- `safety_operation_procedures` - SOP表
- `core_standards` - 标准表
- `mapping_matrix` - 关联表
- `audit_results` - 审核结果表
- `audit_details` - 审核详情表

## 📊 系统特性

### 已完成功能
- ✅ 完整的SOP管理功能（增删改查）
- ✅ 标准库管理功能
- ✅ SOP与标准关联管理
- ✅ 文件上传、下载、预览
- ✅ 智能搜索功能
- ✅ 响应式Web界面
- ✅ 完整的API接口
- ✅ 数据库设计优化
- ✅ 错误处理和验证

### 技术栈
- **后端**: FastAPI, SQLite, Python
- **前端**: HTML5, CSS3, JavaScript
- **文件处理**: pdfplumber, python-docx
- **AI集成**: DeepSeek API（可配置）
- **部署**: 支持Docker容器化

## 🔒 安全注意事项

### API密钥安全
1. **永远不要硬编码API密钥**：不要在代码或脚本中直接写入API密钥
2. **使用环境变量**：通过环境变量或.env文件管理敏感信息
3. **不要提交敏感信息**：确保.gitignore包含.env和包含敏感信息的文件
4. **定期轮换密钥**：定期更新API密钥以提高安全性

### 文件安全
1. **上传文件验证**：系统会对上传的文件进行安全检查
2. **文件存储安全**：上传的文件存储在安全的目录中
3. **访问控制**：确保只有授权用户可以访问敏感文件

### 网络安全
1. **局域网部署**：建议在受信任的局域网内部署
2. **防火墙配置**：只开放必要的端口（8000, 8002）
3. **HTTPS支持**：生产环境建议启用HTTPS

## 🔍 故障排除

### 常见问题

#### 1. 服务启动失败
```bash
# 检查端口占用
netstat -ano | findstr :8000

# 停止占用进程
taskkill /PID <PID> /F
```

#### 2. 数据库连接问题
```bash
# 检查数据库文件
python backend/verify_database.py

# 重新初始化数据库
python backend/init_database.py
```

#### 3. 文件下载问题
- 确保`data/uploads/`目录存在且有写入权限
- 检查数据库中的文件路径是否正确
- 清除浏览器缓存（Ctrl+F5）

#### 4. API调用404错误
- 确保后端服务正在运行
- 检查API端点URL是否正确
- 查看后端日志获取详细错误信息

### 调试工具
- **API测试**: `tools/test_all_apis.py`
- **数据库检查**: `tools/check_db_schema.py`
- **文件验证**: `tools/check_specific_file.py`

## 📈 性能优化

### 数据库优化
- 使用索引优化查询性能
- 定期清理临时数据
- 数据库连接池管理

### 文件处理优化
- 文件分块上传支持
- 图片和PDF压缩
- 缓存机制减少重复处理

### 前端优化
- 资源压缩和合并
- 懒加载图片和组件
- 本地存储缓存数据

## 🤝 贡献指南

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

感谢所有为项目做出贡献的开发者！

## 📞 支持

如有问题或建议，请：
1. 查看 [Issues](https://github.com/yourusername/safety-audit-system/issues)
2. 提交新的Issue
3. 或通过邮件联系维护者

---

**最后更新**: 2026-03-18
**版本**: v1.0.0
**状态**: ✅ 生产就绪  
## ?? �޸���ʷ 
  
### 2026��3��20�� - ϵͳȫ���޸� 
**�޸�����**�� 


## 修复历史

### 2026年3月20日 - 系统全面修复
**修复内容**：
1. **启动脚本修复**：统一使用 `main_fixed.py`，解决编码问题
2. **AI审核API修复**：修复损坏的API文件，添加静态文件服务
3. **前端界面修复**：修复端口配置和API端点不匹配问题
4. **服务启动修复**：确保所有必需服务正常运行

**详细记录**：查看 [修复日志-2026-03-20.md](修复日志-2026-03-20.md)
