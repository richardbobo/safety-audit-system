# 快速部署指南 - Linux服务器

## 🚀 5分钟快速部署

### 前提条件
- Linux服务器（Ubuntu/CentOS/Debian）
- root或sudo权限
- 已安装Python 3.7+

### 步骤1：一键部署脚本
```bash
# 下载部署脚本
wget https://raw.githubusercontent.com/your-repo/safety-audit-system/main/deploy_linux.sh

# 赋予执行权限
chmod +x deploy_linux.sh

# 执行部署（需要root权限）
sudo ./deploy_linux.sh
```

### 步骤2：手动快速部署
```bash
# 1. 安装基础软件
sudo apt update && sudo apt install -y python3 python3-pip python3-venv nginx git

# 2. 克隆项目
cd /opt
sudo git clone https://github.com/your-repo/safety-audit-system.git
sudo chown -R $USER:$USER safety-audit-system
cd safety-audit-system

# 3. 设置环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. 配置环境
cp .env.example .env
# 编辑 .env 文件，设置必要的配置

# 5. 创建必要目录
mkdir -p data/uploads logs

# 6. 测试启动
python backend/main_fixed.py
# 在另一个终端测试AI服务
python backend/ai_audit_api_deterministic.py
```

## 📦 项目文件结构说明

### 需要上传到服务器的文件
```
必须上传的文件：
├── backend/                    # 后端代码（必须）
│   ├── main_fixed.py          # 主服务
│   ├── ai_audit_api_deterministic.py  # AI服务
│   ├── dashboard_api.py       # 仪表板API
│   ├── department_api.py      # 部门API
│   └── category_api.py        # 分类API
├── frontend/                  # 前端代码（必须）
│   ├── *.html                 # 所有HTML页面
│   ├── *.js                   # JavaScript文件
│   ├── styles.css             # 样式文件
│   ├── lib/                   # 第三方库
│   └── modules/               # 系统模块
├── data/                      # 数据目录（可选，可空）
│   └── uploads/               # 上传文件目录
├── .env.example               # 环境配置示例（必须）
├── requirements.txt           # Python依赖（必须）
└── README.md                  # 说明文档

可选文件：
├── deploy_linux.sh            # 部署脚本
├── DEPLOY_CHECKLIST.md        # 部署检查清单
└── SERVICE_STATUS.md          # 服务状态报告
```

## 🔧 最小化部署配置

### 1. 最基本的.env配置
```ini
# 必须配置项
DEBUG=false
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./data/safety_audit.db

# 安全配置（生成随机密钥）
SECRET_KEY=$(openssl rand -hex 32)
```

### 2. 最小化systemd服务配置
```bash
# 创建服务文件 /etc/systemd/system/safety-audit.service
sudo tee /etc/systemd/system/safety-audit.service << EOF
[Unit]
Description=Safety Audit System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/safety-audit-system
ExecStart=/opt/safety-audit-system/venv/bin/python backend/main_fixed.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

### 3. 最小化Nginx配置
```nginx
# /etc/nginx/sites-available/safety-audit
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static/ {
        alias /opt/safety-audit-system/frontend/;
    }
}
```

## 🐳 Docker部署（可选）

### Docker Compose部署
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./frontend:/app/frontend
    environment:
      - DEBUG=false
      - HOST=0.0.0.0
    restart: always

  ai-service:
    build: .
    command: python backend/ai_audit_api_deterministic.py
    ports:
      - "8002:8002"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend:/usr/share/nginx/html/static
    depends_on:
      - backend
```

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p data/uploads

# 暴露端口
EXPOSE 8000
EXPOSE 8002

# 启动命令
CMD ["python", "backend/main_fixed.py"]
```

## 🌐 域名和SSL配置

### 1. 域名解析
- 将域名A记录指向服务器IP
- 等待DNS生效（通常几分钟到几小时）

### 2. SSL证书获取
```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 测试自动续期
sudo certbot renew --dry-run
```

### 3. Nginx SSL配置
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL优化配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # 其他配置同HTTP
    location / {
        proxy_pass http://127.0.0.1:8000;
        # ... 其他代理配置
    }
}

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

## 🔍 部署后验证

### 快速验证命令
```bash
# 1. 检查服务状态
curl -I http://localhost/health
curl -I http://localhost:8002/health

# 2. 检查关键API
curl http://localhost/api/departments/active | jq '.data | length'
curl http://localhost/api/standards | jq '.data | length'

# 3. 检查页面访问
curl -I http://localhost/static/dashboard.html
curl -I http://localhost/static/sops.html

# 4. 检查端口监听
sudo netstat -tuln | grep -E ':(80|8000|8002)'

# 5. 检查日志
sudo tail -n 20 /var/log/nginx/access.log
sudo journalctl -u safety-audit.service -n 10
```

### 浏览器测试
1. 打开浏览器访问: `http://服务器IP` 或 `https://您的域名`
2. 使用默认账号登录: admin / admin123
3. 测试以下功能:
   - SOP创建和编辑
   - 标准文件上传
   - 部门管理
   - 分类管理
   - AI审核功能

## 🛠️ 维护命令

### 服务管理
```bash
# 启动/停止/重启服务
sudo systemctl start safety-audit.service
sudo systemctl stop safety-audit.service
sudo systemctl restart safety-audit.service

# 查看服务状态
sudo systemctl status safety-audit.service
sudo systemctl status safety-audit-ai.service

# 查看日志
sudo journalctl -u safety-audit.service -f
sudo journalctl -u safety-audit-ai.service -f
```

### 数据库备份
```bash
# 手动备份
cp /opt/safety-audit-system/data/safety_audit.db /opt/safety-audit-system/backups/safety_audit_$(date +%Y%m%d).db

# 使用备份脚本
/opt/safety-audit-system/backup.sh
```

### 日志管理
```bash
# 查看Nginx访问日志
sudo tail -f /var/log/nginx/access.log

# 查看Nginx错误日志
sudo tail -f /var/log/nginx/error.log

# 查看应用日志
sudo tail -f /opt/safety-audit-system/logs/app.log
```

## 🚨 故障快速恢复

### 服务无法启动
```bash
# 1. 检查错误
sudo journalctl -u safety-audit.service --no-pager -n 50

# 2. 常见问题解决
# 端口占用：sudo lsof -i :8000
# 权限问题：sudo chown -R www-data:www-data /opt/safety-audit-system
# 依赖问题：source venv/bin/activate && pip install -r requirements.txt

# 3. 重新启动
sudo systemctl daemon-reload
sudo systemctl restart safety-audit.service
```

### 页面无法访问
```bash
# 1. 检查Nginx
sudo nginx -t
sudo systemctl status nginx

# 2. 检查防火墙
sudo ufw status  # 或 sudo firewall-cmd --list-all

# 3. 检查后端服务
curl http://localhost:8000/health
```

### 数据库问题
```bash
# 1. 备份当前数据库
cp /opt/safety-audit-system/data/safety_audit.db /opt/safety-audit-system/data/safety_audit.db.backup

# 2. 检查数据库文件
ls -la /opt/safety-audit-system/data/safety_audit.db

# 3. 修复权限
sudo chown www-data:www-data /opt/safety-audit-system/data/safety_audit.db
sudo chmod 644 /opt/safety-audit-system/data/safety_audit.db
```

## 📞 获取帮助

### 文档资源
- 详细部署指南: `DEPLOY_CHECKLIST.md`
- 项目说明: `README.md`
- API文档: 访问 `http://服务器IP/docs`

### 问题排查
1. 查看日志文件获取错误信息
2. 检查服务状态和端口监听
3. 验证配置文件和权限
4. 测试网络连接和防火墙

### 联系支持
- GitHub Issues: [项目仓库地址]
- 电子邮件: [支持邮箱]
- 文档Wiki: [文档地址]

---
*快速部署指南版本: 1.0*
*最后更新: 2026-04-02*