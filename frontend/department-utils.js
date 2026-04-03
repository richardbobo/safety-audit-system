/**
 * 部门工具函数
 * 提供部门数据的加载和缓存功能
 */

let departmentCache = null;
let lastCacheTime = 0;
const CACHE_DURATION = 5 * 60 * 1000; // 5分钟缓存

/**
 * 获取部门列表（带缓存）
 * @returns {Promise<Array>} 部门列表
 */
async function getDepartments() {
    const now = Date.now();
    
    // 检查缓存是否有效
    if (departmentCache && (now - lastCacheTime) < CACHE_DURATION) {
        console.log('使用缓存的部门数据');
        return departmentCache;
    }
    
    try {
        console.log('从API加载部门数据');
        const response = await fetch('/api/departments/active');
        const result = await response.json();
        
        if (result.status === 'success') {
            departmentCache = result.data;
            lastCacheTime = now;
            return departmentCache;
        } else {
            console.error('获取部门列表失败:', result.message);
            return getDefaultDepartments();
        }
    } catch (error) {
        console.error('获取部门列表失败:', error);
        return getDefaultDepartments();
    }
}

/**
 * 获取默认部门列表（API失败时使用）
 * @returns {Array} 默认部门列表
 */
function getDefaultDepartments() {
    return [
        { id: 1, name: '安全部', code: 'safety' },
        { id: 2, name: '设备部', code: 'equipment' },
        { id: 3, name: '研发部', code: 'rd' },
        { id: 4, name: '生产部', code: 'production' },
        { id: 5, name: '工程部', code: 'engineering' },
        { id: 6, name: '质量部', code: 'quality' },
        { id: 7, name: '其他', code: 'other' }
    ];
}

/**
 * 填充部门下拉框
 * @param {string} selectId 下拉框元素ID
 * @param {string} selectedValue 选中的值
 */
async function populateDepartmentSelect(selectId, selectedValue = '') {
    const selectElement = document.getElementById(selectId);
    if (!selectElement) {
        console.error('找不到部门下拉框元素:', selectId);
        return;
    }
    
    // 保存当前选中的值
    const currentValue = selectedValue || selectElement.value;
    
    // 清空现有选项（保留第一个空选项）
    while (selectElement.options.length > 0) {
        selectElement.remove(0);
    }
    
    // 添加空选项
    const emptyOption = document.createElement('option');
    emptyOption.value = '';
    emptyOption.textContent = '请选择部门';
    selectElement.appendChild(emptyOption);
    
    // 获取部门列表
    const departments = await getDepartments();
    
    // 添加部门选项
    departments.forEach(dept => {
        const option = document.createElement('option');
        option.value = dept.name; // 使用部门名称作为值
        option.textContent = dept.name;
        option.dataset.code = dept.code;
        selectElement.appendChild(option);
    });
    
    // 恢复选中的值
    if (currentValue) {
        selectElement.value = currentValue;
    }
    
    // 如果没有匹配的选项，选择空选项
    if (!selectElement.value && selectElement.options.length > 0) {
        selectElement.selectedIndex = 0;
    }
}

/**
 * 根据文件名自动识别部门
 * @param {string} fileName 文件名
 * @returns {string} 部门名称
 */
function detectDepartmentFromFileName(fileName) {
    if (!fileName) return '';
    
    const fileNameLower = fileName.toLowerCase();
    
    // 关键词映射
    const keywordMap = {
        '安全': '安全部',
        '设备': '设备部',
        '生产': '生产部',
        '质量': '质量部',
        '工程': '工程部',
        '研发': '研发部',
        '维修': '设备部',
        '操作': '生产部',
        '检验': '质量部',
        '测试': '质量部'
    };
    
    // 英文关键词映射
    const englishMap = {
        'safety': '安全部',
        'equipment': '设备部',
        'production': '生产部',
        'quality': '质量部',
        'engineering': '工程部',
        'rd': '研发部',
        'r&d': '研发部',
        'maintenance': '设备部',
        'operation': '生产部',
        'inspection': '质量部',
        'test': '质量部'
    };
    
    // 检查中文关键词
    for (const [keyword, department] of Object.entries(keywordMap)) {
        if (fileNameLower.includes(keyword)) {
            return department;
        }
    }
    
    // 检查英文关键词
    for (const [keyword, department] of Object.entries(englishMap)) {
        if (fileNameLower.includes(keyword)) {
            return department;
        }
    }
    
    return ''; // 无法识别时返回空
}

/**
 * 清除部门缓存（当部门数据变化时调用）
 */
function clearDepartmentCache() {
    departmentCache = null;
    lastCacheTime = 0;
    console.log('部门缓存已清除');
}

/**
 * 初始化部门相关功能
 * @param {string} selectId 部门下拉框ID
 */
async function initDepartmentFeatures(selectId) {
    try {
        await populateDepartmentSelect(selectId);
        console.log('部门功能初始化完成');
    } catch (error) {
        console.error('部门功能初始化失败:', error);
    }
}

// 导出函数
window.departmentUtils = {
    getDepartments,
    populateDepartmentSelect,
    detectDepartmentFromFileName,
    clearDepartmentCache,
    initDepartmentFeatures
};