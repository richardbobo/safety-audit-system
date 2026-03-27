// AI审核系统修复版 - JavaScript部分

// API配置
const API_BASE = 'http://localhost:8000';
const AI_AUDIT_API = 'http://localhost:8002';

// 全局状态
let currentAuditTask = null;
let taskPollInterval = null;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI审核系统修复版加载...');
    checkAIEngine();
});

// 检查AI引擎状态
async function checkAIEngine() {
    try {
        // 修复：使用正确的健康检查端点 /health 而不是 /api/ai-audit/health
        const response = await fetch(`${AI_AUDIT_API}/health`);
        const data = await response.json();
        
        const aiReadyElement = document.getElementById('ai-ready');
        if (aiReadyElement) {
            if (data.status === 'healthy') {
                aiReadyElement.textContent = '就绪';
                aiReadyElement.style.color = '#10b981';
                
                // 更新统计
                const sopCountElement = document.getElementById('sop-count');
                if (sopCountElement) {
                    sopCountElement.textContent = data.sop_count || 0;
                }
                
                if (!data.api_key_configured) {
                    showMessage('warning', 'DeepSeek API密钥未配置，AI审核功能将受限。请设置DEEPSEEK_API_KEY环境变量。');
                } else {
                    showMessage('success', 'DeepSeek API密钥配置成功！AI审核功能已完全启用。');
                }
            } else {
                aiReadyElement.textContent = '异常';
                aiReadyElement.style.color = '#ef4444';
                showMessage('error', `AI引擎异常: ${data.message}`);
            }
        }
    } catch (error) {
        const aiReadyElement = document.getElementById('ai-ready');
        if (aiReadyElement) {
            aiReadyElement.textContent = '未连接';
            aiReadyElement.style.color = '#f59e0b';
        }
        showMessage('error', `无法连接AI审核API: ${error.message}`);
    }
}

// 显示消息
function showMessage(type, message) {
    console.log(`${type}: ${message}`);
    
    // 尝试在页面上显示消息
    const messageContainer = document.getElementById('statusMessage') || document.getElementById('messageContainer');
    if (messageContainer) {
        let className = '';
        switch(type) {
            case 'success': className = 'status-success'; break;
            case 'error': className = 'status-error'; break;
            case 'warning': className = 'status-warning'; break;
            default: className = 'status-info';
        }
        
        messageContainer.innerHTML = `<div class="${className}">${message}</div>`;
        
        // 3秒后自动清除
        setTimeout(() => {
            messageContainer.innerHTML = '';
        }, 3000);
    }
}

// 启动AI审核
async function startAIaudit(sopId) {
    try {
        showMessage('info', '正在启动AI审核...');
        
        const response = await fetch(`${AI_AUDIT_API}/api/ai-audit/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sop_id: sopId,
                force_new: true,
                auditor: 'AI审核系统'
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.task_id) {
            currentAuditTask = data.task_id;
            showMessage('success', `AI审核任务已启动，任务ID: ${data.task_id}`);
            
            // 开始轮询任务状态
            startPollingTaskStatus(data.task_id);
            
            return data.task_id;
        } else {
            throw new Error('未收到任务ID');
        }
        
    } catch (error) {
        console.error('启动AI审核失败:', error);
        showMessage('error', `启动AI审核失败: ${error.message}`);
        return null;
    }
}

// 开始轮询任务状态
function startPollingTaskStatus(taskId) {
    if (taskPollInterval) {
        clearInterval(taskPollInterval);
    }
    
    let attempts = 0;
    const maxAttempts = 60; // 最多轮询5分钟（5秒一次）
    
    taskPollInterval = setInterval(async () => {
        attempts++;
        
        try {
            const response = await fetch(`${AI_AUDIT_API}/api/ai-audit/status/${taskId}`);
            const data = await response.json();
            
            // 更新进度显示
            updateProgressDisplay(data);
            
            if (data.status === 'completed') {
                clearInterval(taskPollInterval);
                showMessage('success', 'AI审核完成！');
                showAuditResults(data);
            } else if (data.status === 'failed') {
                clearInterval(taskPollInterval);
                showMessage('error', `AI审核失败: ${data.error || '未知错误'}`);
            }
            
            // 检查超时
            if (attempts >= maxAttempts) {
                clearInterval(taskPollInterval);
                showMessage('warning', 'AI审核超时，请稍后查看结果');
            }
            
        } catch (error) {
            console.error('轮询任务状态失败:', error);
            
            if (attempts >= maxAttempts) {
                clearInterval(taskPollInterval);
                showMessage('warning', 'AI审核超时，请稍后查看结果');
            }
        }
    }, 5000); // 每5秒轮询一次
}

// 更新进度显示
function updateProgressDisplay(taskData) {
    const progressElement = document.getElementById('auditProgress');
    const progressTextElement = document.getElementById('auditProgressText');
    
    if (progressElement) {
        const progress = taskData.progress || 0;
        progressElement.style.width = `${progress}%`;
        progressElement.textContent = `${progress}%`;
    }
    
    if (progressTextElement) {
        progressTextElement.textContent = taskData.message || taskData.step || '正在处理...';
    }
}

// 显示审核结果
function showAuditResults(taskData) {
    console.log('审核结果:', taskData);
    
    // 这里可以根据需要显示审核结果
    const resultElement = document.getElementById('auditResult');
    if (resultElement && taskData.result) {
        resultElement.innerHTML = `
            <h3>审核结果</h3>
            <p>总体评分: ${taskData.result.overall_score || '未知'}</p>
            <p>符合性: ${taskData.result.compliance_level || '未知'}</p>
        `;
    }
}

// 获取审核历史
async function getAuditHistory(sopId, limit = 20) {
    try {
        const response = await fetch(`${AI_AUDIT_API}/api/ai-audit/history?sop_id=${sopId}&limit=${limit}`);
        const data = await response.json();
        
        if (data.status === 'success' && data.history) {
            return data.history;
        } else {
            throw new Error(data.message || '获取审核历史失败');
        }
        
    } catch (error) {
        console.error('获取审核历史失败:', error);
        showMessage('error', `获取审核历史失败: ${error.message}`);
        return [];
    }
}

// 获取任务列表
async function getTaskList() {
    try {
        const response = await fetch(`${AI_AUDIT_API}/api/ai-audit/tasks`);
        const data = await response.json();
        
        if (data.status === 'success' && data.tasks) {
            return data.tasks;
        } else {
            throw new Error(data.message || '获取任务列表失败');
        }
        
    } catch (error) {
        console.error('获取任务列表失败:', error);
        showMessage('error', `获取任务列表失败: ${error.message}`);
        return [];
    }
}

// 辅助函数
function getStatusText(status) {
    const statusMap = {
        'pending': '等待中',
        'processing': '处理中',
        'completed': '已完成',
        'failed': '失败'
    };
    return statusMap[status] || status;
}

function getScoreColor(score) {
    if (score >= 90) return '#10b981'; // 绿色
    if (score >= 70) return '#f59e0b'; // 黄色
    if (score >= 60) return '#ef4444'; // 红色
    return '#6b7280'; // 灰色
}

// 导出函数供其他文件使用
window.AIAudit = {
    checkAIEngine,
    startAIaudit,
    getAuditHistory,
    getTaskList,
    getStatusText,
    getScoreColor,
    showMessage
};