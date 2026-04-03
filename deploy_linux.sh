    # 测试Nginx配置
    nginx -t
    
    # 重启Nginx
    systemctl restart nginx
    
    log_info "Nginx配置完成"
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian使用UFW
        ufw allow 22/tcp
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw --force enable
        log_info "UFW防火墙已启用"
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL使用firewalld
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --reload
        log_info "Firewalld防火墙已配置"
    else
        log_warn "未找到支持的防火墙工具，请手动配置"
    fi
}

# 配置日志轮转
setup_logrotate() {
    log_info "配置日志轮转..."
    
    cat > /etc/logrotate.d/safety-audit << EOF
/opt/safety-audit-system/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload safety-audit.service > /dev/null 2>&1 || true
        systemctl reload safety-audit-ai.service > /dev/null 2>&1 || true
    endscript
}
EOF
    
    log_info "日志轮转配置完成"
}

# 配置数据库备份
setup_backup() {
    log_info "配置数据库备份..."
    
    # 创建备份脚本
    cat > /opt/safety-audit-system/backup.sh << 'EOF'
#!/bin/bash
# 数据库备份脚本

BACKUP_DIR="/opt/safety-audit-system/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="/opt/safety-audit-system/data/safety_audit.db"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp $DB_FILE "$BACKUP_DIR/safety_audit_$DATE.db"

# 压缩备份
gzip "$BACKUP_DIR/safety_audit_$DATE.db"

# 删除30天前的备份
find $BACKUP_DIR -name "*.db.gz" -mtime +30 -delete

echo "备份完成: safety_audit_$DATE.db.gz"
EOF
    
    chmod +x /opt/safety-audit-system/backup.sh
    
    # 添加到cron任务（每天凌晨2点备份）
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/safety-audit-system/backup.sh") | crontab -
    
    log_info "数据库备份配置完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 启动主服务
    systemctl start safety-audit.service
    sleep 2
    
    # 启动AI服务
    systemctl start safety-audit-ai.service
    sleep 2
    
    # 检查服务状态
    if systemctl is-active --quiet safety-audit.service; then
        log_info "主后端服务启动成功"
    else
        log_error "主后端服务启动失败"
        journalctl -u safety-audit.service --no-pager -n 20
    fi
    
    if systemctl is-active --quiet safety-audit-ai.service; then
        log_info "AI审核服务启动成功"
    else
        log_warn "AI审核服务启动失败（可能是API密钥未配置）"
        journalctl -u safety-audit-ai.service --no-pager -n 20
    fi
    
    # 重启Nginx
    systemctl restart nginx
}

# 验证部署
verify_deployment() {
    log_info "验证部署..."
    
    sleep 5
    
    # 检查服务端口
    if netstat -tuln | grep -q ":8000 "; then
        log_info "✅ 主服务端口8000监听正常"
    else
        log_error "❌ 主服务端口8000未监听"
    fi
    
    if netstat -tuln | grep -q ":8002 "; then
        log_info "✅ AI服务端口8002监听正常"
    else
        log_warn "⚠️ AI服务端口8002未监听（可能是未启动或配置问题）"
    fi
    
    if netstat -tuln | grep -q ":80 "; then
        log_info "✅ Nginx端口80监听正常"
    else
        log_error "❌ Nginx端口80未监听"
    fi
    
    # 测试HTTP访问
    if curl -s -o /dev/null -w "%{http_code}" http://localhost/health | grep -q "200"; then
        log_info "✅ 健康检查接口访问正常"
    else
        log_error "❌ 健康检查接口访问失败"
    fi
    
    log_info "部署验证完成"
}

# 显示部署总结
show_summary() {
    echo ""
    echo "========================================="
    echo "          部署完成总结"
    echo "========================================="
    echo ""
    echo "📁 项目目录: /opt/safety-audit-system"
    echo "🐍 Python环境: /opt/safety-audit-system/venv"
    echo "🗄️  数据库: /opt/safety-audit-system/data/safety_audit.db"
    echo "📄 日志目录: /opt/safety-audit-system/logs"
    echo ""
    echo "🚀 服务状态:"
    echo "  systemctl status safety-audit.service"
    echo "  systemctl status safety-audit-ai.service"
    echo ""
    echo "📊 服务日志:"
    echo "  journalctl -u safety-audit.service -f"
    echo "  journalctl -u safety-audit-ai.service -f"
    echo ""
    echo "🌐 访问地址:"
    echo "  本地访问: http://localhost"
    echo "  远程访问: http://服务器IP"
    echo "  API文档: http://服务器IP/docs"
    echo ""
    echo "🔧 管理命令:"
    echo "  重启服务: systemctl restart safety-audit.service"
    echo "  查看日志: journalctl -u safety-audit.service -n 50"
    echo "  备份数据库: /opt/safety-audit-system/backup.sh"
    echo ""
    echo "⚠️  重要提醒:"
    echo "  1. 编辑 /opt/safety-audit-system/.env 配置环境变量"
    echo "  2. 配置域名和SSL证书（生产环境必需）"
    echo "  3. 修改默认管理员密码"
    echo "  4. 定期检查备份和日志"
    echo ""
    echo "========================================="
}

# 主部署函数
main() {
    log_info "开始部署安全智能审核系统..."
    
    check_root
    check_system
    install_dependencies
    setup_project
    setup_python_env
    setup_environment
    setup_systemd_services
    setup_nginx
    setup_firewall
    setup_logrotate
    setup_backup
    start_services
    verify_deployment
    show_summary
    
    log_info "部署完成！"
}

# 执行主函数
main "$@"