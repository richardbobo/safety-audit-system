# Mac Mini部署 - 文件存储指南

## 📍 **文件存储位置详解**

### **核心原则**
**文件存储在服务运行的位置**
- 服务运行在Mac Mini → 文件存储在Mac Mini
- 服务运行在云服务器 → 文件存储在云服务器
- 服务运行在你的电脑 → 文件存储在你的电脑

### **Mac Mini部署场景**

#### **场景1：纯本地使用（无外网访问）**
```
你的电脑（浏览器） → Mac Mini（服务） → Mac Mini硬盘
       ↑                              ↑
   用户操作                        文件存储
```
- **文件位置**: `~/safety-audit-system/data/uploads/`
- **访问方式**: 只能通过 `http://Mac的IP:8000` 访问
- **文件共享**: 不能直接访问文件，需要通过服务

#### **场景2：外网访问（通过ngrok等）**
```
任何设备（浏览器） → ngrok域名 → Mac Mini（服务） → Mac Mini硬盘
       ↑                              ↑                    ↑
   用户操作                        服务处理            文件存储
```
- **文件位置**: `~/safety-audit-system/data/uploads/` (Mac Mini)
- **访问方式**: 通过ngrok提供的公网URL
- **关键点**: 文件**始终**存储在Mac Mini，无论从哪里访问

---

## 💾 **文件存储目录结构**

### **项目目录结构**
```
~/safety-audit-system/
├── backend/                    # 后端代码
├── frontend/                   # 前端代码
├── data/                       # 数据目录
│   ├── safety_audit.db        # SQLite数据库
│   └── uploads/               # 上传文件存储
│       ├── standards/         # 技术标准文件（自动分类）
│       ├── sops/              # SOP文件
│       └── temp/              # 临时文件
├── logs/                       # 日志文件
├── backups/                    # 备份文件
└── .env                        # 环境配置
```

### **上传文件命名规则**
```
标准文件: STD-{uuid}.pdf
SOP文件: SOP-{uuid}.pdf
临时文件: temp-{timestamp}.tmp
```

### **文件访问URL**
```
# 通过服务访问文件
http://localhost:8000/static/uploads/standards/STD-abc123.pdf
http://your-ngrok-domain.ngrok.io/static/uploads/sops/SOP-def456.pdf
```

---

## 🔄 **文件同步和备份方案**

### **方案1：本地备份（推荐）**
```bash
# 创建备份脚本
cat > ~/backup_uploads.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="$HOME/safety-audit-backups"
DATE=$(date +%Y%m%d_%H%M%S)
SOURCE_DIR="$HOME/safety-audit-system/data"

mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" -C "$SOURCE_DIR" uploads
cp "$SOURCE_DIR/safety_audit.db" "$BACKUP_DIR/safety_audit_$DATE.db"

echo "备份完成: $BACKUP_DIR/uploads_$DATE.tar.gz"
echo "数据库备份: $BACKUP_DIR/safety_audit_$DATE.db"

# 保留最近30天的备份
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.db" -mtime +30 -delete
EOF

chmod +x ~/backup_uploads.sh

# 每天凌晨2点自动备份
(crontab -l 2>/dev/null; echo "0 2 * * * ~/backup_uploads.sh") | crontab -
```

### **方案2：同步到云存储**
```bash
# 使用rclone同步到Google Drive/OneDrive等
brew install rclone

# 配置rclone
rclone config

# 同步脚本
cat > ~/sync_to_cloud.sh << 'EOF'
#!/bin/bash
SOURCE="$HOME/safety-audit-system/data/uploads"
DEST="your-cloud-drive:safety-audit/uploads"

# 增量同步
rclone sync "$SOURCE" "$DEST" --progress

# 记录同步日志
echo "$(date): 同步完成" >> ~/sync.log
EOF

chmod +x ~/sync_to_cloud.sh
```

### **方案3：NAS网络存储**
```bash
# 挂载NAS到Mac
sudo mkdir /Volumes/NAS
sudo mount_smbfs //username:password@nas-ip/share /Volumes/NAS

# 创建符号链接
ln -s /Volumes/NAS/safety-audit-uploads ~/safety-audit-system/data/uploads
```

---

## 📱 **多设备访问文件方案**

### **需求场景**
- 你在办公室用电脑上传文件
- 回家后用手机查看文件
- 同事也需要访问某些文件

### **解决方案**

#### **方案A：通过服务访问（推荐）**
- **优点**: 安全、有权限控制、有日志记录
- **缺点**: 需要服务一直运行

```bash
# 确保Mac Mini一直开机运行服务
# 使用外网访问方案（ngrok/Cloudflare Tunnel）
```

#### **方案B：文件共享服务**
```bash
# 1. 启用Mac文件共享
# 系统偏好设置 → 共享 → 文件共享

# 2. 共享上传目录
sudo sharing -a ~/safety-audit-system/data/uploads

# 3. 从其他设备访问
# Windows: \\mac-ip\safety-audit-uploads
# Mac: smb://mac-ip/safety-audit-uploads
```

#### **方案C：WebDAV服务器**
```bash
# 安装WebDAV服务器
brew install apache

# 配置WebDAV
sudo tee /usr/local/etc/httpd/extra/httpd-dav.conf << 'EOF'
Alias /uploads "/Users/$(whoami)/safety-audit-system/data/uploads"

<Directory "/Users/$(whoami)/safety-audit-system/data/uploads">
    DAV On
    Options Indexes
    Require all granted
</Directory>
EOF
```

---

## 🔒 **文件安全配置**

### **1. 访问权限设置**
```bash
# 设置正确的文件权限
chmod 755 ~/safety-audit-system/data/uploads
chmod 644 ~/safety-audit-system/data/uploads/*

# 设置所有权
sudo chown -R $(whoami):staff ~/safety-audit-system/data
```

### **2. 防病毒扫描**
```bash
# 安装ClamAV进行病毒扫描
brew install clamav

# 配置自动扫描
cat > ~/scan_uploads.sh << 'EOF'
#!/bin/bash
UPLOADS_DIR="$HOME/safety-audit-system/data/uploads"
LOG_FILE="$HOME/safety-audit-system/logs/virus-scan.log"

freshclam  # 更新病毒库
clamscan -r -i "$UPLOADS_DIR" >> "$LOG_FILE" 2>&1

if [ $? -eq 1 ]; then
    echo "发现病毒！" >> "$LOG_FILE"
    # 发送警报
    osascript -e 'display notification "发现可疑文件" with title "安全警报"'
fi
EOF

chmod +x ~/scan_uploads.sh
```

### **3. 文件类型验证**
```python
# 在backend/main_fixed.py中添加文件类型检查
ALLOWED_MIME_TYPES = {
    'application/pdf': '.pdf',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'image/png': '.png',
    'image/jpeg': '.jpg'
}
```

---

## 🗂️ **文件管理最佳实践**

### **1. 定期清理**
```bash
# 清理30天前的临时文件
find ~/safety-audit-system/data/uploads/temp -type f -mtime +30 -delete

# 清理空目录
find ~/safety-audit-system/data/uploads -type d -empty -delete
```

### **2. 存储空间监控**
```bash
# 监控磁盘空间
cat > ~/check_disk_space.sh << 'EOF'
#!/bin/bash
THRESHOLD=90  # 百分比
USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

if [ "$USAGE" -gt "$THRESHOLD" ]; then
    echo "警告：磁盘空间不足 ($USAGE%)" >> ~/disk-alert.log
    # 发送通知
    osascript -e 'display notification "磁盘空间不足，请清理文件" with title "存储警报"'
fi
EOF

chmod +x ~/check_disk_space.sh
```

### **3. 文件索引和搜索**
```bash
# 使用Spotlight建立索引
mdimport ~/safety-audit-system/data/uploads

# 搜索文件
mdfind -onlyin ~/safety-audit-system/data/uploads "安全规程"
```

---

## 🔄 **迁移和恢复**

### **从Windows迁移到Mac**
```bash
# 1. 备份Windows上的文件
# 将整个data目录复制到Mac

# 2. 在Mac上恢复
cp -r /path/to/windows/data ~/safety-audit-system/

# 3. 修复权限
chmod -R 755 ~/safety-audit-system/data/uploads
```

### **文件恢复流程**
```bash
# 1. 停止服务
./stop.sh

# 2. 恢复备份
tar -xzf ~/safety-audit-backups/uploads_20260402.tar.gz -C ~/safety-audit-system/data/
cp ~/safety-audit-backups/safety_audit_20260402.db ~/safety-audit-system/data/safety_audit.db

# 3. 重新启动
./start.sh
```

---

## ❓ **常见问题解答**

### **Q1：文件上传后在哪里？**
**A**: 文件存储在Mac Mini的 `~/safety-audit-system/data/uploads/` 目录下。

### **Q2：如何从其他电脑访问这些文件？**
**A**: 有几种方式：
1. **通过Web服务**：访问ngrok域名，通过页面下载
2. **文件共享**：启用Mac文件共享
3. **云同步**：使用rclone同步到云盘

### **Q3：文件安全吗？**
**A**: 默认配置下：
- ✅ 文件有基本权限控制
- ✅ 通过服务访问有日志记录
- ⚠️ 建议配置SSL和访问控制
- ⚠️ 重要文件建议额外加密

### **Q4：Mac关机后文件还能访问吗？**
**A**: 不能。服务停止后，文件无法通过Web访问。如果需要24小时访问：
1. 保持Mac Mini开机
2. 配置唤醒定时任务
3. 或迁移到云服务器

### **Q5：如何备份文件？**
**A**: 使用提供的备份脚本，建议：
- 每日自动备份到本地
- 每周同步到云存储
- 重要文件手动额外备份

---

## 🎯 **推荐配置方案**

### **个人使用**
```
存储位置: Mac Mini本地硬盘
备份方案: 每日自动备份到外置硬盘
访问方式: ngrok外网访问 + 本地文件共享
安全配置: 基础权限 + 定期病毒扫描
```

### **团队使用**
```
存储位置: Mac Mini + 云存储同步
备份方案: 实时同步到云 + 本地备份
访问方式: Cloudflare Tunnel + 权限控制
安全配置: SSL + 访问日志 + 文件加密
```

### **生产环境**
```
存储位置: 专业NAS或云存储
备份方案: 多地点冗余备份
访问方式: 专业CDN + 负载均衡
安全配置: 完整安全审计 + 监控告警
```

---

## 📞 **技术支持**

### **文件访问问题**
```bash
# 检查服务是否运行
curl http://localhost:8000/health

# 检查文件是否存在
ls -la ~/safety-audit-system/data/uploads/

# 检查权限
stat ~/safety-audit-system/data/uploads/
```

### **磁盘空间问题**
```bash
# 查看磁盘使用
df -h

# 查看大文件
du -sh ~/safety-audit-system/data/uploads/*
find ~/safety-audit-system/data/uploads -type f -size +100M
```

### **性能问题**
```bash
# 监控I/O
iostat 1

# 查看进程
top -o cpu

# 网络监控
nettop -P
```

---
*Mac Mini文件存储指南版本: 1.0*
*最后更新: 2026-04-02*