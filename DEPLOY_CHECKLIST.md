# Linux服务器部署检查清单

## 📋 部署前准备

### 服务器要求
- [ ] **操作系统**: Ubuntu 20.04/22.04, CentOS 7/8, Debian 11+
- [ ] **内存**: 至少2GB RAM
- [ ] **存储**: 至少10GB可用空间
- [ ] **网络**: 公网IP或内网访问权限
- [ ] **权限**: root或sudo权限

### 域名和SSL（生产环境必需）
- [ ] **域名**: 已注册并解析到服务器IP
- [ ] **SSL证书**: 准备获取（Let's Encrypt免费）
- [ ] **防火墙**: 开放80和443端口

## 🔧 部署步骤

### 第一阶段：服务器初始化
- [ ] 更新系统: `sudo apt update && sudo apt upgrade -y`
- [ ] 安装基础工具: git, curl, wget, vim
- [ ] 安装Python 3.7+: `sudo apt install python3 python3-pip python3-venv`
- [ ] 验证安装: `python3 --version` (应该显示3.7+)

### 第二阶段：项目部署
- [ ] 传输项目文件到服务器
  - 方法A: Git克隆
  - 方法B: SCP传输
  - 方法C: 压缩包传输
- [ ] 设置项目目录: `/opt/safety-audit-system`
- [ ] 创建必要目录: `mkdir -p data/uploads logs backups`
- [ ] 设置权限: `chown -R www-data:www-data /opt/safety-audit-system`

### 第三阶段：环境配置
- [ ] 创建Python虚拟环境: `python3 -m venv venv`
- [ ] 激活环境: `source venv/bin/activate`
- [ ] 安装依赖: `pip install -r requirements.txt`
- [ ] 复制环境配置: `cp .env.example .env`
- [ ] 编辑环境配置: `vim .env`
  - [ ] 设置 `DEBUG=false`
  - [ ] 设置 `HOST=0.0.0.0`
  - [ ] 配置DeepSeek API密钥（如果需要AI功能）
  - [ ] 设置安全密钥

### 第四阶段：服务配置
- [ ] 配置systemd服务文件:
  - [ ] `/etc/systemd/system/safety-audit.service`
  - [ ] `/etc/systemd/system/safety-audit-ai.service`
- [ ] 重新加载systemd: `systemctl daemon-reload`
- [ ] 启用服务: `systemctl enable safety-audit.service`
- [ ] 启用AI服务: `systemctl enable safety-audit-ai.service`

### 第五阶段：Web服务器配置
- [ ] 安装Nginx: `sudo apt install nginx`
- [ ] 创建Nginx配置: `/etc/nginx/sites-available/safety-audit`
- [ ] 启用站点: `ln -s /etc/nginx/sites-available/safety-audit /etc/nginx/sites-enabled/`
- [ ] 测试配置: `nginx -t`
- [ ] 重启Nginx: `systemctl restart nginx`

### 第六阶段：安全配置
- [ ] 配置防火墙:
  - Ubuntu/Debian: `ufw allow 22,80,443`
  - CentOS/RHEL: `firewall-cmd --add-service={http,https,ssh}`
- [ ] 获取SSL证书（生产环境）:
  ```bash
  sudo apt install certbot python3-certbot-nginx
  sudo certbot --nginx -d your_domain.com
  ```
- [ ] 配置自动续期: `sudo certbot renew --dry-run`

### 第七阶段：启动和验证
- [ ] 启动主服务: `systemctl start safety-audit.service`
- [ ] 启动AI服务: `systemctl start safety-audit-ai.service`
- [ ] 检查服务状态:
  ```bash
  systemctl status safety-audit.service
  systemctl status safety-audit-ai.service
  ```
- [ ] 验证部署:
  ```bash
  curl http://localhost/health
  curl http://localhost:8002/health
  ```

## 🛠️ 快速部署命令

### 完整部署脚本
```bash
# 1. 上传部署脚本到服务器
scp deploy_linux.sh user@server_ip:/tmp/

# 2. 在服务器上执行
ssh user@server_ip
sudo bash /tmp/deploy_linux.sh
```

### 手动部署关键命令
```bash
# 项目目录设置
sudo mkdir -p /opt/safety-audit-system
sudo chown -R $USER:$USER /opt/safety-audit-system

# 环境配置
cd /opt/safety-audit-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动测试
python backend/main_fixed.py
# 在另一个终端
python backend/ai_audit_api_deterministic.py
```

## 🔍 部署验证

### 服务状态检查
```bash
# 检查服务运行状态
sudo systemctl status safety-audit.service
sudo systemctl status safety-audit-ai.service
sudo systemctl status nginx

# 检查端口监听
sudo netstat -tuln | grep -E ':80|:8000|:8002'

# 检查日志
sudo journalctl -u safety-audit.service -n 20
sudo journalctl -u safety-audit-ai.service -n 20
sudo tail -f /var/log/nginx/error.log
```

### 功能测试
```bash
# 健康检查
curl http://localhost/health
curl http://localhost:8002/health

# API测试
curl http://localhost/api/departments/active
curl http://localhost/api/categories/active
curl http://localhost/api/standards

# 页面访问测试
curl -I http://localhost/static/dashboard.html
curl -I http://localhost/static/sops.html
```

## 🚨 故障排除

### 常见问题及解决方案

#### 1. 服务启动失败
```bash
# 查看详细错误
sudo journalctl -u safety-audit.service --no-pager -n 50

# 常见原因：
# - Python依赖未安装：运行 pip install -r requirements.txt
# - 端口被占用：netstat -tuln | grep :8000
# - 权限问题：chown -R www-data:www-data /opt/safety-audit-system
```

#### 2. Nginx配置错误
```bash
# 测试配置
sudo nginx -t

# 查看错误日志
sudo tail -f /var/log/nginx/error.log

# 重新加载配置
sudo systemctl reload nginx
```

#### 3. 数据库问题
```bash
# 检查数据库文件
ls -la /opt/safety-audit-system/data/safety_audit.db

# 检查权限
stat /opt/safety-audit-system/data/safety_audit.db

# 备份和修复
cp /opt/safety-audit-system/data/safety_audit.db /opt/safety-audit-system/data/safety_audit.db.backup
```

#### 4. 文件上传问题
```bash
# 检查上传目录
ls -la /opt/safety-audit-system/data/uploads/

# 检查权限
stat /opt/safety-audit-system/data/uploads/

# 设置正确权限
sudo chown -R www-data:www-data /opt/safety-audit-system/data/uploads
sudo chmod 755 /opt/safety-audit-system/data/uploads
```

## 📊 生产环境优化

### 性能优化
- [ ] 配置Nginx缓存
- [ ] 启用Gzip压缩
- [ ] 配置数据库索引
- [ ] 设置适当的超时时间

### 安全加固
- [ ] 配置HTTPS重定向
- [ ] 设置安全头部
- [ ] 限制请求频率
- [ ] 配置WAF规则

### 监控和日志
- [ ] 配置日志轮转
- [ ] 设置监控告警
- [ ] 定期备份数据
- [ ] 性能监控设置

### 维护计划
- [ ] 定期更新系统
- [ ] 定期更新Python包
- [ ] 定期检查日志
- [ ] 定期测试备份恢复

## 📞 支持信息

### 紧急联系方式
- 服务器管理员: [填写联系方式]
- 应用开发人员: [填写联系方式]
- 系统监控: [填写监控平台]

### 重要文件位置
- 项目目录: `/opt/safety-audit-system`
- 配置文件: `/opt/safety-audit-system/.env`
- 日志文件: `/opt/safety-audit-system/logs/`
- 备份文件: `/opt/safety-audit-system/backups/`
- Nginx配置: `/etc/nginx/sites-available/safety-audit`
- 服务配置: `/etc/systemd/system/safety-audit*.service`

### 恢复步骤
1. 停止所有服务
2. 恢复数据库备份
3. 检查配置文件
4. 重新启动服务
5. 验证功能

---
*部署检查清单版本: 1.0*
*最后更新: 2026-04-02*