// API配置
const API_CONFIG = {
    // 开发环境：本地服务器
    development: {
        baseUrl: 'http://localhost:8000',
        apiPrefix: '/api'
    },
    // 生产环境：实际部署地址
    production: {
        baseUrl: 'https://your-production-domain.com',
        apiPrefix: '/api'
    }
};

// 自动检测环境
function getApiConfig() {
    const currentProtocol = window.location.protocol;
    const currentHost = window.location.host;
    
    // 强制使用开发环境（因为后端在localhost:8000）
    // 这样可以避免file://协议访问时的问题
    return API_CONFIG.development;
    
    // 原来的逻辑保留但不使用
    // // 如果是file://协议或localhost，使用开发环境
    // if (currentProtocol === 'file:' || currentHost.includes('localhost') || currentHost.includes('127.0.0.1')) {
    //     return API_CONFIG.development;
    // }
    // 
    // // 否则使用生产环境
    // return API_CONFIG.production;
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