// 标准详情页面JavaScript - 最终版本

// 全局变量
let currentStandardId = null;
let currentStandard = null;
let pdfUrl = null;
let currentZoom = 100;

// API配置
const API_CONFIG = {
    baseUrl: 'http://localhost:8000'
};

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 从URL获取标准ID
    const urlParams = new URLSearchParams(window.location.search);
    currentStandardId = urlParams.get('id');
    
    if (!currentStandardId) {
        showError('未指定标准ID');
        return;
    }
    
    // 初始化事件监听器
    initEventListeners();
    
    // 加载标准信息
    loadStandardInfo();
});

// 初始化事件监听器
function initEventListeners() {
    // 返回按钮
    document.getElementById('backBtn').addEventListener('click', function() {
        window.history.back();
    });
    
    // 重试按钮
    document.getElementById('retryBtn').addEventListener('click', function() {
        loadStandardInfo();
    });
    
    // 下载PDF按钮
    document.getElementById('downloadPDFBtn').addEventListener('click', function() {
        downloadPDF();
    });
    
    // 新窗口打开按钮
    document.getElementById('newWindowBtn').addEventListener('click', function() {
        newWindowPDF();
    });
    
    // 标签页切换
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            switchTab(tabId);
        });
    });
    
    // PDF控制按钮
    document.getElementById('zoomInBtn').addEventListener('click', zoomIn);
    document.getElementById('zoomOutBtn').addEventListener('click', zoomOut);
    document.getElementById('fitWidthBtn').addEventListener('click', fitWidth);
    document.getElementById('fitPageBtn').addEventListener('click', fitPage);
    document.getElementById('printBtn').addEventListener('click', printPDF);
}

// 加载标准信息
async function loadStandardInfo() {
    showLoading();
    
    try {
        console.log('正在加载标准信息，ID:', currentStandardId);
        console.log('API URL:', `${API_CONFIG.baseUrl}/api/standards/${currentStandardId}`);
        
        const response = await fetch(`${API_CONFIG.baseUrl}/api/standards/${currentStandardId}`);
        
        console.log('响应状态:', response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('API响应数据:', data);
        
        // 智能数据提取 - 处理所有可能的API响应结构
        let standardData = null;
        
        if (data.status === 'success' && data.data) {
            // 标准成功响应结构
            standardData = data.data;
            console.log('使用标准成功响应结构');
        } else if (data.data) {
            // 有些API可能直接返回数据，没有status字段
            standardData = data.data;
            console.log('使用data字段结构');
        } else if (data && typeof data === 'object' && !Array.isArray(data)) {
            // 有些API可能直接返回标准对象
            standardData = data;
            console.log('使用直接对象结构');
        } else if (Array.isArray(data) && data.length > 0) {
            // 有些API可能返回数组
            standardData = data[0];
            console.log('使用数组结构');
        } else {
            console.log('无法识别的响应结构:', data);
            throw new Error(data.message || '无法识别的API响应结构');
        }
        
        currentStandard = standardData;
        
        // 显示标准信息
        displayStandardInfo(standardData);
        
        // 构建PDF URL
        pdfUrl = `${API_CONFIG.baseUrl}/api/files/pdf/${currentStandardId}`;
        
        // 加载PDF
        loadPDF();
        
        // 加载关联SOP
        loadRelatedSOPs();
        
        showMainContent();
        
    } catch (error) {
        console.error('加载标准信息失败:', error);
        showError(error.message);
    }
}

// 显示标准信息
function displayStandardInfo(standard) {
    // 更新页面标题
    document.getElementById('standardName').textContent = standard.name || standard.standard_no || '未命名标准';
    
    // 构建标准元数据HTML
    let metaHtml = '';
    
    // 基本信息
    metaHtml += `
        <div class="meta-item">
            <div class="meta-label">标准编号</div>
            <div class="meta-value">${standard.standard_no || '未设置'}</div>
        </div>
    `;
    
    metaHtml += `
        <div class="meta-item">
            <div class="meta-label">标准分类</div>
            <div class="meta-value">${standard.category || '未设置'}</div>
        </div>
    `;
    
    metaHtml += `
        <div class="meta-item">
            <div class="meta-label">生效日期</div>
            <div class="meta-value">${standard.effective_date || '未设置'}</div>
        </div>
    `;
    
    metaHtml += `
        <div class="meta-item">
            <div class="meta-label">文件路径</div>
            <div class="meta-value">${standard.file_path || '未设置'}</div>
        </div>
    `;
    
    // 状态信息
    if (standard.status) {
        metaHtml += `
            <div class="meta-item">
                <div class="meta-label">标准状态</div>
                <div class="meta-value">${standard.status}</div>
            </div>
        `;
    }
    
    if (standard.is_obsolete !== undefined) {
        metaHtml += `
            <div class="meta-item">
                <div class="meta-label">是否废止</div>
                <div class="meta-value">${standard.is_obsolete ? '是' : '否'}</div>
            </div>
        `;
    }
    
    document.getElementById('standardMeta').innerHTML = metaHtml;
}



// 加载PDF
function loadPDF() {
    try {
        const pdfEmbed = document.getElementById('pdfEmbed');
        pdfEmbed.src = pdfUrl;
        
        console.log('加载PDF URL:', pdfUrl);
        
    } catch (error) {
        console.error('加载PDF失败:', error);
        document.getElementById('pdf-tab').innerHTML = `
            <div class="error-state">
                <div class="error-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div class="error-text">
                    <h3>PDF加载失败</h3>
                    <p>${error.message}</p>
                    <p>请尝试以下解决方案：</p>
                    <ol>
                        <li><a href="${pdfUrl}" target="_blank">直接下载PDF文件</a></li>
                        <li>检查网络连接</li>
                        <li>刷新页面重试</li>
                    </ol>
                </div>
            </div>
        `;
    }
}

// 放大
function zoomIn() {
    currentZoom = Math.min(currentZoom + 25, 200);
    updateZoom();
}

// 缩小
function zoomOut() {
    currentZoom = Math.max(currentZoom - 25, 50);
    updateZoom();
}

// 更新缩放
function updateZoom() {
    const pdfEmbed = document.getElementById('pdfEmbed');
    pdfEmbed.style.transform = `scale(${currentZoom / 100})`;
    pdfEmbed.style.transformOrigin = '0 0';
    pdfEmbed.style.width = `${100 / (currentZoom / 100)}%`;
    pdfEmbed.style.height = `${700 / (currentZoom / 100)}px`;
    
    document.getElementById('zoomLevel').textContent = `${currentZoom}%`;
}

// 适应宽度
function fitWidth() {
    currentZoom = 100;
    updateZoom();
}

// 适应页面
function fitPage() {
    currentZoom = 100;
    updateZoom();
}

// 打印PDF
function printPDF() {
    try {
        window.open(pdfUrl, '_blank');
    } catch (error) {
        console.error('打印PDF失败:', error);
        alert('打印PDF失败: ' + error.message);
    }
}

// 下载PDF
function downloadPDF() {
    try {
        const link = document.createElement('a');
        link.href = pdfUrl;
        link.download = `${currentStandardId}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (error) {
        console.error('下载PDF失败:', error);
        alert('下载PDF失败: ' + error.message);
    }
}

// 新窗口打开PDF
function newWindowPDF() {
    try {
        window.open(pdfUrl, '_blank');
    } catch (error) {
        console.error('新窗口打开失败:', error);
        alert('新窗口打开失败: ' + error.message);
    }
}

// 加载关联SOP
async function loadRelatedSOPs() {
    try {
        console.log('正在加载关联SOP，标准ID:', currentStandardId);
        const response = await fetch(`${API_CONFIG.baseUrl}/api/standards/${currentStandardId}/sops`);
        
        console.log('SOP API响应状态:', response.status, response.statusText);
        
        if (!response.ok) {
            // 如果API返回错误，显示友好提示而不是崩溃
            console.warn('获取关联SOP失败，显示空状态');
            document.getElementById('sopsContent').innerHTML = `
                <div class="info-state">
                    <i class="fas fa-info-circle"></i>
                    <h3>暂无关联SOP</h3>
                    <p>当前标准尚未关联任何SOP，或者SOP数据暂时不可用。</p>
                    <p>状态码: ${response.status} ${response.statusText}</p>
                </div>
            `;
            return;
        }
        
        const data = await response.json();
        console.log('SOP API响应数据:', data);
        
        let html = '';
        if (data.data && data.data.length > 0) {
            html = '<h3>关联的安全操作规程</h3>';
            html += '<div class="sops-list">';
            
            data.data.forEach(sop => {
                html += `
                    <div class="sop-item">
                        <div class="sop-info">
                            <h4>${sop.title || sop.name || '未命名SOP'}</h4>
                            <div class="sop-meta">
                                <span><i class="fas fa-hashtag"></i> ${sop.sop_code || sop.id}</span>
                                <span><i class="fas fa-building"></i> ${sop.department || '未指定部门'}</span>
                                <span><i class="fas fa-exclamation-triangle"></i> 风险等级: ${sop.risk_level || '未指定'}</span>
                            </div>
                        </div>
                        <div class="sop-actions">
                            <button class="btn btn-sm btn-secondary" onclick="viewSOP('${sop.id}')">
                                <i class="fas fa-eye"></i> 查看
                            </button>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
        } else {
            html = '<div class="empty-state">';
            html += '<i class="fas fa-link"></i>';
            html += '<h3>没有关联的SOP</h3>';
            html += '<p>该标准目前没有关联的安全操作规程。</p>';
            html += '<p>您可以在SOP管理页面创建SOP，并将其与标准关联。</p>';
            html += '</div>';
        }
        
        document.getElementById('sopsContent').innerHTML = html;
        
    } catch (error) {
        console.error('加载关联SOP失败:', error);
        // 显示友好错误信息
        document.getElementById('sopsContent').innerHTML = `
            <div class="error-state">
                <div class="error-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div class="error-text">
                    <h3>加载关联SOP失败</h3>
                    <p>${error.message}</p>
                    <p>请检查网络连接或稍后重试。</p>
                </div>
            </div>
        `;
    }
}

// 查看SOP
function viewSOP(sopId) {
    window.open(`sop-detail-clean-fixed.html?sop_id=${sopId}`, '_blank');
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (!bytes) return '0 B';
    bytes = parseInt(bytes);
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 切换标签页
function switchTab(tabId) {
    // 更新标签页按钮
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.tab-button[data-tab="${tabId}"]`).classList.add('active');
    
    // 更新标签页内容
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabId).classList.add('active');
}

// 显示加载状态
function showLoading() {
    document.getElementById('loadingState').style.display = 'block';
    document.getElementById('errorState').style.display = 'none';
    document.getElementById('mainContent').style.display = 'none';
}

// 显示错误状态
function showError(message) {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('errorState').style.display = 'block';
    document.getElementById('mainContent').style.display = 'none';
    document.getElementById('errorMessage').textContent = message;
}

// 显示主要内容
function showMainContent() {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('errorState').style.display = 'none';
    document.getElementById('mainContent').style.display = 'block';
}