// API配置
const API_CONFIG = {
    development: {
        baseUrl: 'http://localhost:8000',
        apiPrefix: '/api'
    },
    production: {
        baseUrl: 'http://localhost:8000',
        apiPrefix: '/api'
    }
};

// 自动检测当前访问域名，适配远程部署
function getApiConfig() {
    const origin = window.location.origin;
    // 如果是 localhost 或 file:// 则用本地地址，否则用当前域名
    if (origin.startsWith('http://localhost') || origin.startsWith('http://127.0.0.1') || origin === 'null') {
        return { baseUrl: 'http://localhost:8000', apiPrefix: '/api' };
    }
    // 远程访问：使用当前域名（由Nginx/Cloudflare代理）
    return { baseUrl: origin, apiPrefix: '/api' };
}

// 获取API基础URL
function getApiBaseUrl() {
    const config = getApiConfig();
    return config.baseUrl + config.apiPrefix;
}

// 获取完整的API URL
function getApiUrl(endpoint) {
    const baseUrl = getApiBaseUrl();
    // 确保endpoint以/开头
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
    return baseUrl + normalizedEndpoint;
}

// 通用API请求函数
async function apiRequest(endpoint, options = {}) {
    const url = getApiUrl(endpoint);
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, mergedOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API请求失败 (${endpoint}):`, error);
        throw error;
    }
}

// 导出函数供其他文件使用
window.API = {
    getApiBaseUrl,
    getApiUrl,
    apiRequest,
    getApiConfig
};