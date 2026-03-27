# 安全操作规程智能审核系统 - 前端

## 技术栈
- **HTML5** - 语义化标签
- **CSS3** - 现代化样式  
- **JavaScript (ES6)** - 动态交互
- **Python HTTP Server** - 开发服务器

## 启动方法
```bash
# 进入前端目录
cd frontend

# 启动开发服务器
python -m http.server 3000
```

## 访问地址
- 前端界面: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 功能特点
1. **零依赖** - 无需Node.js/npm/React
2. **快速启动** - 单个HTML文件，无需编译
3. **实时状态** - 自动检测后端服务状态
4. **响应式设计** - 支持移动端

## 目录结构
```
frontend/
├── index.html          # 主页面
├── README.md           # 说明文档
└── start.bat          # Windows启动脚本
```

## 开发说明
- 修改index.html后直接刷新浏览器即可
- 无需构建工具，开发效率高
- 代码全部在一个文件中，易于维护
