$DATE.db"
gzip "$BACKUP_DIR/safety_audit_$DATE.db"

# 保留最近30天的备份
find $BACKUP_DIR -name "*.db.gz" -mtime +30 -delete

echo "备份完成: safety_audit_$DATE.db.gz"
EOF

chmod +x ~/backup_database.sh

# 每天凌晨3点备份
(crontab -l 2>/dev/null; echo "0 3 * * * ~/backup_database.sh") | crontab -
```

### 3. 日志管理
```bash
# 配置日志轮转
sudo tee /etc/newsyslog.d/safety-audit.conf << 'EOF'
# 安全审核系统日志配置
/Users/$(whoami)/safety-audit-system/logs/*.log {
    rotate 30
    daily
    compress
    delaycompress
    missingok
    notifempty
    create 644 $(whoami) staff
    postrotate
        # 重新打开日志文件
        kill -HUP $(cat /usr/local/var/run/nginx.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
EOF
```

---

## 🚨 故障排除

### 常见问题及解决方案

#### 1. 外网无法访问
```bash
# 诊断步骤
# 1. 检查本地服务是否运行
curl http://localhost:8000/health

# 2. 检查局域网访问
curl http://$(ipconfig getifaddr en0):8000/health

# 3. 检查路由器端口转发
# 登录路由器查看转发规则

# 4. 检查防火墙
sudo pfctl -s rules

# 5. 检查ISP是否封锁端口
# 尝试更换端口（如8080）
```

#### 2. 连接不稳定
```bash
# 优化SSH隧道（如果使用）
autossh -M 0 -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" \
        -o "ExitOnForwardFailure=yes" \
        -NR 18000:localhost:8000 user@vps-ip

# 调整TCP参数
sudo sysctl -w net.inet.tcp.keepidle=60000
sudo sysctl -w net.inet.tcp.keepintvl=3000
```

#### 3. 性能问题
```bash
# 监控资源使用
top -o cpu  # 按CPU排序
top -o rsize  # 按内存排序

# 检查网络延迟
ping yourdomain.com
mtr yourdomain.com

# 优化Nginx配置
# 增加worker_processes
# 启用gzip压缩
# 配置缓存
```

#### 4. 证书问题
```bash
# 更新Let's Encrypt证书
sudo certbot renew --dry-run

# 手动更新
sudo certbot renew --force-renewal

# 检查证书有效期
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -noout -dates
```

---

## 📱 移动端访问优化

### 1. 响应式设计检查
```html
<!-- 确保前端页面有响应式meta标签 -->
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

### 2. PWA支持（可选）
```javascript
// 创建manifest.json
{
  "name": "安全智能审核系统",
  "short_name": "安全审核",
  "start_url": "/static/dashboard.html",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2196F3",
  "icons": [
    {
      "src": "/static/favicon.ico",
      "sizes": "64x64",
      "type": "image/x-icon"
    }
  ]
}
```

### 3. 移动端测试
```bash
# 使用浏览器开发者工具模拟移动端
# 或使用真实手机测试
```

---

## 🎯 推荐部署方案

### 个人使用/测试环境
```
方案: Cloudflare Tunnel
理由: 免费、无需公网IP、配置简单、稳定性好
配置时间: 10-15分钟
```

### 小型团队使用
```
方案: 端口转发 + 动态DNS + SSL
理由: 性能好、延迟低、完全控制
配置时间: 30-60分钟
```

### 生产环境
```
方案: 云服务器反向代理 + 专业CDN
理由: 高可用、高安全、专业支持
配置时间: 2-4小时
```

---

## 📞 技术支持

### 获取帮助
1. **查看日志**: `tail -f ~/safety-audit-system/logs/app.log`
2. **检查服务状态**: `./stop.sh && ./start.sh`
3. **网络诊断**: 使用`curl`和`ping`命令
4. **社区支持**: 相关技术论坛

### 紧急恢复
```bash
# 1. 停止所有服务
./stop.sh

# 2. 备份当前状态
cp -r ~/safety-audit-system ~/safety-audit-system-backup-$(date +%Y%m%d)

# 3. 检查配置文件
cat ~/safety-audit-system/.env

# 4. 重新启动
./start.sh

# 5. 查看错误信息
tail -f ~/safety-audit-system/logs/error.log
```

### 联系信息
- **项目文档**: 查看README.md和部署指南
- **问题反馈**: [您的联系方式]
- **紧急支持**: [紧急联系方式]

---

## ✅ 部署检查清单

### 部署前检查
- [ ] Mac系统已更新到最新版本
- [ ] 已安装Homebrew
- [ ] 有稳定的网络连接
- [ ] 了解路由器管理员密码

### 本地部署检查
- [ ] 项目文件已复制到Mac
- [ ] Python虚拟环境创建成功
- [ ] 依赖包安装完成
- [ ] 数据库文件存在
- [ ] 本地访问正常 (http://localhost:8000)

### 外网访问检查
- [ ] 选择合适的外网访问方案
- [ ] 完成相应配置
- [ ] 从外网测试访问
- [ ] 配置SSL证书（生产环境）

### 安全配置检查
- [ ] 修改默认管理员密码
- [ ] 配置防火墙规则
- [ ] 设置访问限制（如IP白名单）
- [ ] 定期备份计划

### 监控维护检查
- [ ] 监控脚本配置
- [ ] 日志轮转设置
- [ ] 自动备份配置
- [ ] 故障恢复计划

---
*Mac Mini外网访问指南版本: 1.0*
*最后更新: 2026-04-02*