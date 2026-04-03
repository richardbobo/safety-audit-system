# 安全配置
SECRET_KEY=$(openssl rand -hex 32)

# AI审核配置（可选）
# DEEPSEEK_API_KEY=your_api_key_here
# DEEPSEEK_BASE_URL=https://api.deepseek.com

# 文件上传配置
MAX_UPLOAD_SIZE=10485760
ALLOWED_EXTENSIONS=pdf,doc,docx
EOF
        log_info "已创建基础.env文件"
    fi
    
    # 提示用户编辑
    log_warn "请编辑 $PROJECT_DIR/.env 文件配置环境变量"
    log_warn "重要: 设置 DEBUG=false, HOST=0.0.0.0"
}

# 创建启动脚本
create_startup_script() {
    log_step "创建启动脚本..."
    
    cd "$PROJECT_DIR"
    
    # 创建启动脚本
    cat > start.sh << 'EOF'
#!/bin/bash
# 安全审核系统启动脚本

cd "$(dirname "$0")"

# 检查Python虚拟环境
if [ ! -f "venv/bin/activate" ]; then
    echo "错误: 未找到Python虚拟环境"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "端口 $port 已被占用"
        return 1
    fi
    return 0
}

# 检查8000端口
if ! check_port 8000; then
    echo "请停止占用8000端口的进程，或修改.env中的PORT配置"
    exit 1
fi

# 检查8002端口（AI服务）
if ! check_port 8002; then
    echo "警告: 端口8002已被占用，AI服务可能无法启动"
fi

echo "========================================"
echo "启动安全智能审核系统..."
echo "========================================"

# 启动主服务
echo "启动主后端服务 (端口: 8000)..."
python backend/main_fixed.py &
PID1=$!

# 等待主服务启动
sleep 3

# 检查主服务是否启动成功
if ps -p $PID1 > /dev/null; then
    echo "✅ 主后端服务启动成功 (PID: $PID1)"
else
    echo "❌ 主后端服务启动失败"
    exit 1
fi

# 启动AI服务（如果配置了API密钥）
if grep -q "DEEPSEEK_API_KEY=" .env && ! grep -q "DEEPSEEK_API_KEY=your_api_key" .env; then
    echo "启动AI审核服务 (端口: 8002)..."
    python backend/ai_audit_api_deterministic.py &
    PID2=$!
    sleep 2
    
    if ps -p $PID2 > /dev/null; then
        echo "✅ AI审核服务启动成功 (PID: $PID2)"
    else
        echo "⚠️ AI审核服务启动失败（可能是API密钥问题）"
    fi
else
    echo "⚠️ 未配置AI审核服务（跳过启动）"
    PID2=""
fi

echo ""
echo "========================================"
echo "服务启动完成！"
echo "========================================"
echo ""
echo "🌐 访问地址:"
echo "   本地访问: http://localhost:8000"
echo "   局域网访问: http://$(ipconfig getifaddr en0):8000"
echo ""
echo "📱 默认账号:"
echo "   用户名: admin"
echo "   密码: admin123"
echo ""
echo "🔧 管理命令:"
echo "   停止服务: kill $PID1 ${PID2:+$PID2}"
echo "   查看日志: tail -f logs/app.log"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "========================================"

# 保存PID到文件
echo $PID1 > .service_pid
[ -n "$PID2" ] && echo $PID2 >> .service_pid

# 等待中断
trap 'kill $PID1 ${PID2:+$PID2} 2>/dev/null; echo "服务已停止"; rm -f .service_pid' INT TERM
wait
EOF
    
    chmod +x start.sh
    
    # 创建停止脚本
    cat > stop.sh << 'EOF'
#!/bin/bash
# 停止服务脚本

cd "$(dirname "$0")"

if [ -f .service_pid ]; then
    echo "停止安全审核系统服务..."
    while read pid; do
        if ps -p $pid > /dev/null; then
            kill $pid 2>/dev/null
            echo "已停止进程: $pid"
        fi
    done < .service_pid
    rm -f .service_pid
    echo "所有服务已停止"
else
    echo "未找到运行中的服务"
    
    # 尝试查找并停止相关进程
    PIDS=$(ps aux | grep -E "main_fixed.py|ai_audit_api" | grep -v grep | awk '{print $2}')
    if [ -n "$PIDS" ]; then
        echo "发现相关进程: $PIDS"
        kill $PIDS 2>/dev/null
        echo "已停止相关进程"
    fi
fi
EOF
    
    chmod +x stop.sh
    
    log_info "启动脚本创建完成"
}

# 配置Nginx（可选）
setup_nginx() {
    log_step "配置Nginx反向代理..."
    
    read -p "是否配置Nginx反向代理？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 创建Nginx配置
        NGINX_CONF="/usr/local/etc/nginx/servers/safety-audit.conf"
        
        sudo tee "$NGINX_CONF" << EOF
# 安全智能审核系统 - Nginx配置
server {
    listen       80;
    server_name  localhost;
    
    # 主服务代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件
    location /static/ {
        alias $PROJECT_DIR/frontend/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 文件大小限制
    client_max_body_size 10M;
    
    # 访问日志
    access_log $PROJECT_DIR/logs/nginx-access.log;
    error_log $PROJECT_DIR/logs/nginx-error.log;
}
EOF
        
        # 测试Nginx配置
        if sudo nginx -t; then
            # 启动或重载Nginx
            if brew services list | grep -q nginx; then
                sudo brew services restart nginx
            else
                sudo brew services start nginx
            fi
            log_info "Nginx配置完成并已启动"
        else
            log_error "Nginx配置测试失败"
        fi
    else
        log_info "跳过Nginx配置"
    fi
}

# 配置开机自启动
setup_autostart() {
    log_step "配置开机自启动..."
    
    read -p "是否配置开机自启动？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 创建LaunchAgent
        LAUNCH_AGENT="$HOME/Library/LaunchAgents/com.safetyaudit.system.plist"
        
        cat > "$LAUNCH_AGENT" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.safetyaudit.system</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$PROJECT_DIR/start.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/launchd-error.log</string>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF
        
        # 加载LaunchAgent
        launchctl load -w "$LAUNCH_AGENT"
        
        log_info "开机自启动配置完成"
        log_info "启动项位置: $LAUNCH_AGENT"
    else
        log_info "跳过开机自启动配置"
    fi
}

# 配置外网访问
setup_external_access() {
    log_step "配置外网访问..."
    
    echo ""
    echo "请选择外网访问方案:"
    echo "1. 端口转发 + 动态DNS (有公网IP推荐)"
    echo "2. 内网穿透工具 (无公网IP)"
    echo "3. 暂不配置"
    echo ""
    read -p "请选择 (1/2/3): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            setup_port_forwarding
            ;;
        2)
            setup_internal_tunnel
            ;;
        *)
            log_info "跳过外网访问配置"
            ;;
    esac
}

# 配置端口转发
setup_port_forwarding() {
    log_info "配置端口转发方案..."
    
    # 获取本机IP
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1)
    
    echo ""
    echo "📡 端口转发配置指南"
    echo "========================"
    echo "1. 登录路由器管理界面"
    echo "   地址: 通常为 192.168.1.1 或 192.168.0.1"
    echo "   账号密码: 查看路由器背面"
    echo ""
    echo "2. 找到端口转发设置"
    echo "   通常在: 高级设置 → NAT转发 → 虚拟服务器"
    echo ""
    echo "3. 添加转发规则:"
    echo "   - 外部端口: 80 (HTTP) 或 443 (HTTPS)"
    echo "   - 内部IP地址: $LOCAL_IP"
    echo "   - 内部端口: 8000"
    echo "   - 协议: TCP"
    echo ""
    echo "4. 动态DNS配置（解决动态公网IP）:"
    echo "   推荐服务: no-ip.com, duckdns.org"
    echo ""
    
    read -p "是否配置动态DNS？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "请访问以下网站注册动态DNS服务:"
        log_info "  - https://www.noip.com (免费)"
        log_info "  - https://www.duckdns.org (免费)"
        log_info "  - https://dyn.com (付费)"
    fi
    
    log_info "端口转发配置说明已显示"
}

# 配置内网穿透
setup_internal_tunnel() {
    log_info "配置内网穿透方案..."
    
    echo ""
    echo "🔗 内网穿透工具选择"
    echo "========================"
    echo "1. ngrok (最简单)"
    echo "   命令: brew install ngrok/ngrok/ngrok"
    echo "   使用: ngrok http 8000"
    echo ""
    echo "2. Cloudflare Tunnel (免费)"
    echo "   命令: brew install cloudflare/cloudflare/cloudflared"
    echo "   使用: cloudflared tunnel create safety-audit"
    echo ""
    echo "3. frp (需要VPS)"
    echo "   需要一台有公网IP的服务器"
    echo ""
    
    read -p "请选择工具 (1/2/3): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            install_ngrok
            ;;
        2)
            install_cloudflared
            ;;
        3)
            setup_frp
            ;;
        *)
            log_info "跳过内网穿透配置"
            ;;
    esac
}

# 安装ngrok
install_ngrok() {
    log_info "安装ngrok..."
    
    brew install ngrok/ngrok/ngrok
    
    echo ""
    echo "ngrok安装完成，下一步:"
    echo "1. 注册账号: https://ngrok.com"
    echo "2. 获取认证令牌"
    echo "3. 配置: ngrok config add-authtoken YOUR_TOKEN"
    echo "4. 启动: ngrok http 8000"
    echo ""
    
    log_info "ngrok安装完成，请按上述步骤配置"
}

# 安装Cloudflare Tunnel
install_cloudflared() {
    log_info "安装Cloudflare Tunnel..."
    
    brew install cloudflare/cloudflare/cloudflared
    
    echo ""
    echo "Cloudflare Tunnel安装完成，下一步:"
    echo "1. 登录: cloudflared tunnel login"
    echo "2. 创建隧道: cloudflared tunnel create safety-audit"
    echo "3. 配置路由: cloudflared tunnel route dns safety-audit yourdomain.com"
    echo "4. 运行: cloudflared tunnel run safety-audit"
    echo ""
    
    log_info "Cloudflare Tunnel安装完成，请按上述步骤配置"
}

# 配置frp
setup_frp() {
    log_info "配置frp..."
    
    echo ""
    echo "frp配置需要:"
    echo "1. 一台有公网IP的VPS服务器"
    echo "2. 在VPS上安装frp服务端"
    echo "3. 在Mac上配置frp客户端"
    echo ""
    echo "详细教程: https://github.com/fatedier/frp"
    echo ""
    
    log_info "frp配置说明已显示"
}

# 显示部署总结
show_summary() {
    echo ""
    echo "========================================="
    echo "           Mac Mini部署完成"
    echo "========================================="
    echo ""
    echo "📁 项目目录: $PROJECT_DIR"
    echo "🐍 Python环境: $PROJECT_DIR/venv"
    echo "🗄️  数据库: $PROJECT_DIR/data/safety_audit.db"
    echo ""
    echo "🚀 启动服务:"
    echo "  cd $PROJECT_DIR"
    echo "  ./start.sh"
    echo ""
    echo "🛑 停止服务:"
    echo "  ./stop.sh"
    echo ""
    echo "🌐 访问地址:"
    echo "  本地: http://localhost:8000"
    echo "  局域网: http://$(ipconfig getifaddr en0 2>/dev/null || echo '本地IP'):8000"
    echo ""
    echo "🔧 管理命令:"
    echo "  查看日志: tail -f $PROJECT_DIR/logs/app.log"
    echo "  备份数据库: cp data/safety_audit.db backups/"
    echo ""
    echo "⚠️  重要提醒:"
    echo "  1. 编辑 $PROJECT_DIR/.env 配置环境变量"
    echo "  2. 修改默认管理员密码"
    echo "  3. 配置外网访问（如果需要）"
    echo "  4. 考虑配置SSL证书"
    echo ""
    echo "========================================="
}

# 主函数
main() {
    log_info "开始Mac Mini部署..."
    
    check_homebrew
    install_dependencies
    deploy_project
    setup_python_env
    create_directories
    setup_environment
    create_startup_script
    setup_nginx
    setup_autostart
    setup_external_access
    show_summary
    
    log_info "部署完成！"
}

# 执行主函数
main "$@"