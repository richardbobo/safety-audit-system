/**
 * 标准分类工具函数
 * 提供分类数据缓存和动态加载功能
 */

let categoriesCache = null;
let cacheTimestamp = 0;
const CACHE_DURATION = 5 * 60 * 1000; // 5分钟缓存

/**
 * 获取分类列表（带缓存）
 * @param {boolean} forceRefresh - 是否强制刷新缓存
 * @returns {Promise<Array>} 分类列表
 */
async function getCategories(forceRefresh = false) {
    const now = Date.now();
    
    // 检查缓存是否有效
    if (!forceRefresh && categoriesCache && (now - cacheTimestamp) < CACHE_DURATION) {
        console.log('使用缓存的分类数据');
        return categoriesCache;
    }
    
    try {
        console.log('从API获取分类数据...');
        const response = await fetch('/api/categories/active');
        
        if (!response.ok) {
            throw new Error(`API请求失败: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.status === 'success') {
            categoriesCache = result.data;
            cacheTimestamp = now;
            console.log('分类数据获取成功，已缓存');
            return categoriesCache;
        } else {
            throw new Error(result.message || '获取分类数据失败');
        }
    } catch (error) {
        console.error('获取分类数据失败:', error);
        
        // 返回默认分类作为降级方案
        return getDefaultCategories();
    }
}

/**
 * 获取默认分类（降级方案）
 * @returns {Array} 默认分类列表
 */
function getDefaultCategories() {
    return [
        { id: 1, name: '国家标准', code: 'national' },
        { id: 2, name: '行业标准', code: 'industry' },
        { id: 3, name: '企业标准', code: 'enterprise' },
        { id: 4, name: '国际标准', code: 'international' },
        { id: 5, name: '地方标准', code: 'local' },
        { id: 6, name: '团体标准', code: 'group' },
        { id: 7, name: '其他标准', code: 'other' }
    ];
}

/**
 * 填充分类下拉框
 * @param {string} selectId - 下拉框元素ID
 * @param {string} selectedValue - 选中的值
 * @param {boolean} includeEmpty - 是否包含空选项
 */
async function populateCategorySelect(selectId, selectedValue = '', includeEmpty = true) {
    const selectElement = document.getElementById(selectId);
    
    if (!selectElement) {
        console.error(`未找到下拉框元素: ${selectId}`);
        return;
    }
    
    // 保存当前选中的值
    const currentValue = selectedValue || selectElement.value;
    
    // 清空下拉框
    selectElement.innerHTML = '';
    
    // 添加空选项（如果需要）
    if (includeEmpty) {
        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = '选择分类';
        selectElement.appendChild(emptyOption);
    }
    
    try {
        // 获取分类数据
        const categories = await getCategories();
        
        // 添加分类选项
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.name; // 使用名称作为值，与现有数据兼容
            option.textContent = category.name;
            option.dataset.code = category.code;
            option.dataset.id = category.id;
            
            // 如果当前值匹配，则选中
            if (currentValue === category.name) {
                option.selected = true;
            }
            
            selectElement.appendChild(option);
        });
        
        // 如果当前值不在选项中，尝试设置为空
        if (currentValue && !selectElement.value) {
            selectElement.value = '';
        }
        
    } catch (error) {
        console.error('填充分类下拉框失败:', error);
        
        // 使用默认分类作为降级
        const defaultCategories = getDefaultCategories();
        defaultCategories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.name;
            option.textContent = category.name;
            selectElement.appendChild(option);
        });
    }
}

/**
 * 根据分类代码获取分类名称
 * @param {string} code - 分类代码
 * @returns {Promise<string>} 分类名称
 */
async function getCategoryNameByCode(code) {
    try {
        const categories = await getCategories();
        const category = categories.find(cat => cat.code === code);
        return category ? category.name : code;
    } catch (error) {
        console.error('根据代码获取分类名称失败:', error);
        return code;
    }
}

/**
 * 根据分类名称获取分类代码
 * @param {string} name - 分类名称
 * @returns {Promise<string>} 分类代码
 */
async function getCategoryCodeByName(name) {
    try {
        const categories = await getCategories();
        const category = categories.find(cat => cat.name === name);
        return category ? category.code : name;
    } catch (error) {
        console.error('根据名称获取分类代码失败:', error);
        return name;
    }
}

/**
 * 清除分类缓存
 */
function clearCategoryCache() {
    categoriesCache = null;
    cacheTimestamp = 0;
    console.log('分类缓存已清除');
}

/**
 * 从文件名自动识别分类
 * @param {string} fileName - 文件名
 * @returns {string} 识别的分类名称
 */
function detectCategoryFromFileName(fileName) {
    if (!fileName) return '其他标准';
    
    const fileNameLower = fileName.toLowerCase();
    
    // 根据关键词识别分类
    if (fileNameLower.includes('gb') || fileNameLower.includes('国标') || fileNameLower.includes('国家标准')) {
        return '国家标准';
    } else if (fileNameLower.includes('iso') || fileNameLower.includes('iec') || fileNameLower.includes('国际标准')) {
        return '国际标准';
    } else if (fileNameLower.includes('jb') || fileNameLower.includes('hg') || fileNameLower.includes('行业标准')) {
        return '行业标准';
    } else if (fileNameLower.includes('企标') || fileNameLower.includes('企业标准')) {
        return '企业标准';
    } else if (fileNameLower.includes('地标') || fileNameLower.includes('地方标准')) {
        return '地方标准';
    } else if (fileNameLower.includes('团标') || fileNameLower.includes('团体标准')) {
        return '团体标准';
    } else {
        return '其他标准';
    }
}

// 导出函数（如果使用模块）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getCategories,
        populateCategorySelect,
        getCategoryNameByCode,
        getCategoryCodeByName,
        clearCategoryCache,
        detectCategoryFromFileName
    };
}