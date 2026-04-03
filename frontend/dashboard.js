/**
 * 仪表板页面JavaScript
 * 负责与后端API通信和数据展示
 */

class DashboardManager {
    constructor() {
        this.apiBaseUrl = window.API_BASE_URL || 'http://localhost:8000';
        this.charts = {};
        this.currentFilters = {
            timeRange: 'month',
            department: 'all',
            level: 'all'
        };
    }
    
    // 初始化仪表板
    async init() {
        console.log('初始化仪表板...');
        
        // 初始化筛选器
        this.initFilters();
        
        // 初始化图表
        this.initCharts();
        
        // 加载数据
        await this.loadDashboardData();
        
        // 设置自动刷新（可选）
        // this.setupAutoRefresh();
    }
    
    // 初始化筛选器
    initFilters() {
        // 时间范围筛选器
        const timeRangeSelect = document.getElementById('timeRange');
        if (timeRangeSelect) {
            timeRangeSelect.addEventListener('change', () => {
                this.currentFilters.timeRange = timeRangeSelect.value;
                this.loadDashboardData();
            });
        }
        
        // 部门筛选器
        const departmentSelect = document.getElementById('departmentFilter');
        if (departmentSelect) {
            // 从API获取部门列表
            this.loadDepartments().then(departments => {
                departments.forEach(dept => {
                    const option = document.createElement('option');
                    option.value = dept;
                    option.textContent = dept;
                    departmentSelect.appendChild(option);
                });
            });
            
            departmentSelect.addEventListener('change', () => {
                this.currentFilters.department = departmentSelect.value;
                this.loadDashboardData();
            });
        }
        
        // 级别筛选器
        const levelSelect = document.getElementById('levelFilter');
        if (levelSelect) {
            levelSelect.addEventListener('change', () => {
                this.currentFilters.level = levelSelect.value;
                this.loadDashboardData();
            });
        }
        
        // 刷新按钮
        const refreshBtn = document.querySelector('button[onclick*="loadDashboardData"]');
        if (refreshBtn) {
            refreshBtn.onclick = () => this.loadDashboardData();
        }
        
        // 导出按钮
        const exportBtn = document.querySelector('button[onclick*="exportDashboardData"]');
        if (exportBtn) {
            exportBtn.onclick = () => this.exportDashboardData();
        }
    }
    
    // 销毁所有图表
    destroyCharts() {
        Object.keys(this.charts).forEach(chartName => {
            if (this.charts[chartName]) {
                this.charts[chartName].destroy();
                this.charts[chartName] = null;
            }
        });
        this.charts = {};
    }
    
    // 重新初始化图表
    reinitCharts() {
        this.destroyCharts();
        this.initCharts();
    }
    
    // 初始化图表
    initCharts() {
        // 检查Chart.js是否已加载
        if (typeof Chart === 'undefined') {
            console.error('Chart.js未加载，无法初始化图表');
            return;
        }
        
        // SOP部门分布图
        const sopDepartmentCtx = document.getElementById('sopDepartmentChart');
        if (sopDepartmentCtx) {
            this.charts.sopDepartment = new Chart(sopDepartmentCtx.getContext('2d'), {
                type: 'pie',
                data: {
                    labels: ['加载中...'],
                    datasets: [{
                        data: [1],
                        backgroundColor: ['#3498db']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        title: {
                            display: true,
                            text: 'SOP部门分布'
                        }
                    }
                }
            });
        }
        
        // SOP级别分布图
        const sopLevelCtx = document.getElementById('sopLevelChart');
        if (sopLevelCtx) {
            this.charts.sopLevel = new Chart(sopLevelCtx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['一级', '二级', '三级'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: ['#2ecc71', '#3498db', '#9b59b6']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        title: {
                            display: true,
                            text: 'SOP级别分布'
                        }
                    }
                }
            });
        }
        
        // 标准状态分布图
        const standardStatusCtx = document.getElementById('standardStatusChart');
        if (standardStatusCtx) {
            this.charts.standardStatus = new Chart(standardStatusCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: ['有效', '待更新', '已过期'],
                    datasets: [{
                        label: '标准数量',
                        data: [0, 0, 0],
                        backgroundColor: ['#2ecc71', '#f39c12', '#e74c3c']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: '技术标准状态'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        // 审核状态分布图
        const auditStatusCtx = document.getElementById('auditStatusChart');
        if (auditStatusCtx) {
            this.charts.auditStatus = new Chart(auditStatusCtx.getContext('2d'), {
                type: 'pie',
                data: {
                    labels: ['待审核', '审核中', '已完成', '已驳回'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: ['#f39c12', '#3498db', '#2ecc71', '#e74c3c']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        title: {
                            display: true,
                            text: '审核任务状态'
                        }
                    }
                }
            });
        }
        
        // SOP增长趋势图
        const sopGrowthCtx = document.getElementById('sopGrowthChart');
        if (sopGrowthCtx) {
            this.charts.sopGrowth = new Chart(sopGrowthCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'SOP数量',
                        data: [],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'SOP增长趋势（最近12个月）'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        // 审核完成趋势图
        const auditTrendCtx = document.getElementById('auditTrendChart');
        if (auditTrendCtx) {
            this.charts.auditTrend = new Chart(auditTrendCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: '待审核',
                            data: [],
                            backgroundColor: '#f39c12'
                        },
                        {
                            label: '已完成',
                            data: [],
                            backgroundColor: '#2ecc71'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: '审核完成趋势（最近30天）'
                        }
                    },
                    scales: {
                        x: {
                            stacked: true
                        },
                        y: {
                            stacked: true,
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }
    
    // 加载仪表板数据
    async loadDashboardData() {
        this.showLoading();
        
        try {
            // 获取汇总数据
            const summary = await this.fetchDashboardSummary();
            
            // 更新统计卡片
            this.updateStatsCards(summary);
            
            // 重新初始化图表以避免Canvas重用错误
            this.reinitCharts();
            
            // 更新图表
            this.updateCharts(summary);
            
            // 更新数据表格
            await this.updateDataTables(summary);
            
            // 更新待办事项
            await this.updateTodoList();
            
            this.hideLoading();
            
        } catch (error) {
            console.error('加载仪表板数据失败:', error);
            this.showError('加载数据失败，请稍后重试');
            this.hideLoading();
        }
    }
    
    // 从API获取仪表板汇总数据
    async fetchDashboardSummary() {
        const params = new URLSearchParams({
            time_range: this.currentFilters.timeRange,
            department: this.currentFilters.department !== 'all' ? this.currentFilters.department : '',
            level: this.currentFilters.level !== 'all' ? this.currentFilters.level : ''
        });
        
        const url = `${this.apiBaseUrl}/api/dashboard/summary?${params}`;
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`API请求失败: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'API返回错误');
        }
        
        return result.data;
    }
    
    // 加载部门列表
    async loadDepartments() {
        try {
            // 这里可以从SOP数据中提取部门列表
            // 暂时返回固定列表
            return ['生产部', '质量部', '设备部', '安全部', '研发部', '行政部', '财务部'];
        } catch (error) {
            console.error('加载部门列表失败:', error);
            return [];
        }
    }
    
    // 更新统计卡片
    updateStatsCards(data) {
        const sopStats = data.sop_stats || {};
        const standardStats = data.standard_stats || {};
        const fileStats = data.file_stats || {};
        const mappingStats = data.mapping_stats || {};
        
        // SOP统计
        this.updateElement('sopTotal', sopStats.total || 0);
        this.updateElement('sopPending', sopStats.pending || 0);
        this.updateElement('sopReviewed', sopStats.by_status?.已审核 || 0);
        
        const sopPassRate = data.audit_stats?.pass_rate || 0;
        this.updateElement('sopPassRate', `${sopPassRate}%`);
        
        const sopPendingPercent = sopStats.total > 0 ? 
            ((sopStats.pending || 0) / sopStats.total * 100).toFixed(1) : 0;
        this.updateElement('sopPendingPercent', `${sopPendingPercent}%`);
        
        // 标准统计
        this.updateElement('standardTotal', standardStats.total || 0);
        this.updateElement('standardPendingUpdate', standardStats.pending_update || 0);
        this.updateElement('standardExpiredSoon', standardStats.expiring_soon || 0);
        
        // 文件统计
        const fileByType = fileStats.by_file_type || {};
        this.updateElement('superiorFiles', fileByType.上级文件 || 0);
        this.updateElement('companyProcedures', fileByType.公司程序文件 || 0);
        this.updateElement('operationGuides', fileByType.操作指导书 || 0);
        
        // 关联统计
        this.updateElement('sopStandardMappings', mappingStats.total_mappings || 0);
        this.updateElement('avgMappingsPerSop', (mappingStats.avg_mappings_per_sop || 0).toFixed(1));
        
        // 趋势数据
        this.updateElement('sopChange', `+${sopStats.monthly_new || 0} 本月新增`);
        this.updateElement('standardChange', `+${standardStats.monthly_new || 0} 本月新增`);
        
        // 最近更新
        const recentFiles = fileStats.recent_files || [];
        if (recentFiles.length > 0) {
            const lastUpdate = recentFiles[0]?.updated_at || '-';
            this.updateElement('superiorLastUpdate', lastUpdate.split(' ')[0]);
        }
    }
    
    // 更新图表
    updateCharts(data) {
        const sopStats = data.sop_stats || {};
        const standardStats = data.standard_stats || {};
        const auditStats = data.audit_stats || {};
        const growthTrend = data.growth_trend || {};
        
        // SOP部门分布
        if (this.charts.sopDepartment) {
            const deptData = sopStats.by_department || {};
            const labels = Object.keys(deptData);
            const values = Object.values(deptData);
            
            this.charts.sopDepartment.data.labels = labels;
            this.charts.sopDepartment.data.datasets[0].data = values;
            this.charts.sopDepartment.data.datasets[0].backgroundColor = this.getChartColors(labels.length);
            this.charts.sopDepartment.update();
        }
        
        // SOP级别分布
        if (this.charts.sopLevel) {
            const levelData = sopStats.by_level || {};
            this.charts.sopLevel.data.datasets[0].data = [
                levelData.一级 || 0,
                levelData.二级 || 0,
                levelData.三级 || 0
            ];
            this.charts.sopLevel.update();
        }
        
        // 标准状态分布
        if (this.charts.standardStatus) {
            const statusData = standardStats.by_status || {};
            this.charts.standardStatus.data.datasets[0].data = [
                statusData.有效 || 0,
                statusData.待更新 || 0,
                statusData.已过期 || 0
            ];
            this.charts.standardStatus.update();
        }
        
        // 审核状态分布
        if (this.charts.auditStatus) {
            const auditStatusData = auditStats.by_status || {};
            this.charts.auditStatus.data.datasets[0].data = [
                auditStatusData.待审核 || 0,
                auditStatusData.审核中 || 0,
                auditStatusData.已完成 || 0,
                auditStatusData.已驳回 || 0
            ];
            this.charts.auditStatus.update();
        }
        
        // SOP增长趋势
        if (this.charts.sopGrowth && growthTrend.sop_growth) {
            const growthData = growthTrend.sop_growth;
            this.charts.sopGrowth.data.labels = growthData.map(item => item.month);
            this.charts.sopGrowth.data.datasets[0].data = growthData.map(item => item.count);
            this.charts.sopGrowth.update();
        }
        
        // 审核完成趋势
        if (this.charts.auditTrend && auditStats.trend_last_30_days) {
            const trendData = auditStats.trend_last_30_days;
            this.charts.auditTrend.data.labels = trendData.labels || [];
            
            // 这里需要根据实际数据调整
            // 暂时使用示例数据
            this.charts.auditTrend.data.datasets[0].data = trendData.data || [];
            this.charts.auditTrend.data.datasets[1].data = trendData.data || [];
            this.charts.auditTrend.update();
        }
    }
    
    // 更新数据表格
    async updateDataTables(data) {
        // 部门详情表格
        const departmentDetails = data.department_details || [];
        this.updateDepartmentTable(departmentDetails);
        
        // 标准详情表格
        await this.updateStandardTable();
        
        // 待办事项表格
        await this.updateTodoTable();
    }
    
    // 更新部门表格
    updateDepartmentTable(departments) {
        const tbody = document.getElementById('departmentDetailBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (departments.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="loading">
                        <i class="fas fa-info-circle"></i><br>
                        暂无部门数据
                    </td>
                </tr>
            `;
            return;
        }
        
        departments.forEach(dept => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${dept.name}</td>
                <td>${dept.total}</td>
                <td>${dept.level1 || 0}</td>
                <td>${dept.level2 || 0}</td>
                <td>${dept.level3 || 0}</td>
                <td><span class="status-badge status-pending">${dept.pending || 0}</span></td>
                <td>${dept.reviewed || 0}</td>
                <td>${dept.pass_rate || 0}%</td>
                <td>${dept.mappings || 0}</td>
            `;
            tbody.appendChild(row);
        });
    }
    
    // 更新标准表格
    async updateStandardTable() {
        try {
            const params = new URLSearchParams({
                time_range: this.currentFilters.timeRange
            });
            
            const url = `${this.apiBaseUrl}/api/dashboard/standard-stats?${params}`;
            const response = await fetch(url);
            
            if (!response.ok) return;
            
            const result = await response.json();
            if (!result.success) return;
            
            const stats = result.data;
            const tbody = document.getElementById('standardDetailBody');
            
            if (!tbody) return;
            
            tbody.innerHTML = '';
            
            // 这里需要根据实际数据结构调整
            // 暂时使用示例数据
            const standardTypes = [
                { type: '国家标准', data: stats },
                { type: '行业标准', data: stats },
                { type: '企业标准', data: stats }
            ];
            
            standardTypes.forEach(item => {
                const statusData = stats.by_status || {};
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.type}</td>
                    <td>${Math.floor(stats.total / 3) || 0}</td>
                    <td><span class="status-badge status-approved">${statusData.有效 || 0}</span></td>
                    <td><span class="status-badge status-pending">${statusData.待更新 || 0}</span></td>
                    <td><span class="status-badge status-expired">${statusData.已过期 || 0}</span></td>
                    <td>2年</td>
                    <td>2026-03-15</td>
                    <td>2027-03-15</td>
                `;
                tbody.appendChild(row);
            });
            
        } catch (error) {
            console.error('更新标准表格失败:', error);
        }
    }
    
    // 更新待办事项表格
    async updateTodoTable() {
        try {
            const params = new URLSearchParams({
                time_range: this.currentFilters.timeRange
            });
            
            const url = `${this.apiBaseUrl}/api/dashboard/todo-items?${params}`;
            const response = await fetch(url);
            
            if (!response.ok) return;
            
            const result = await response.json();
            if (!result.success) return;
            
            const todos = result.data || [];
            const tbody = document.getElementById('todoBody');
            
            if (!tbody) return;
            
            tbody.innerHTML = '';
            
            if (todos.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6" class="loading">
                            <i class="fas fa-check-circle"></i><br>
                            暂无待办事项
                        </td>
                    </tr>
                `;
                return;
            }
            
            todos.forEach(todo => {
                const priorityClass = todo.priority === '高' ? 'status-badge status-pending' :
                                     todo.priority === '中' ? 'status-badge status-pending' : 
                                     'status-badge status-approved';
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${todo.type}</td>
                    <td>${todo.item}</td>
                    <td>${todo.count}</td>
                    <td><span class="${priorityClass}">${todo.priority}</span></td>
                    <td>${todo.due_date}</td>
                    <td><button class="btn btn-sm btn-primary" onclick="dashboard.handleTodoAction('${todo.action}')">${todo.action}</button></td>
                `;
                tbody.appendChild(row);
            });
            
        } catch (error) {
            console.error('更新待办事项表格失败:', error);
        }
    }
    
    // 更新待办事项列表（从汇总数据）
    async updateTodoList() {
        // 这个方法现在由updateTodoTable处理
    }
    
    // 处理待办事项操作
    handleTodoAction(action) {
        switch(action) {
            case '立即审核':
                window.location.href = 'sops.html?filter=pending';
                break;
            case '查看详情':
                window.location.href = 'standards.html?filter=expiring';
                break;
            case '批量归档':
                this.showMessage('info', '批量归档功能开发中...');
                break;
            case '检查关联':
                window.location.href = 'sops.html?filter=unmapped';
                break;
            case '立即处理':
                window.location.href = 'standards.html?filter=expiring';
                break;
            default:
                this.showMessage('info', `执行操作: ${action}`);
        }
    }
    
    // 导出仪表板数据
    async exportDashboardData() {
        try {
            const summary = await this.fetchDashboardSummary();
            
            const exportData = {
                export_time: new Date().toISOString(),
                filters: this.currentFilters,
                data: summary
            };
            
            const dataStr = JSON.stringify(exportData, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
            
            const exportFileName = `仪表板数据_${new Date().toISOString().split('T')[0]}.json`;
            
            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileName);
            linkElement.click();
            
            this.showMessage('success', '数据导出成功！');
            
        } catch (error) {
            console.error('导出数据失败:', error);
            this.showMessage('error', '导出数据失败，请稍后重试');
        }
    }
    
    // 设置自动刷新
    setupAutoRefresh() {
        // 每5分钟自动刷新一次
        setInterval(() => {
            this.loadDashboardData();
        }, 5 * 60 * 1000);
    }
    
    // 工具方法
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    getChartColors(count) {
        const colors = [
            '#3498db', '#2ecc71', '#9b59b6', '#e74c3c', '#f39c12', 
            '#1abc9c', '#34495e', '#7f8c8d', '#d35400', '#c0392b'
        ];
        return colors.slice(0, count);
    }
    
    showLoading() {
        const loadingElements = document.querySelectorAll('.loading');
        loadingElements.forEach(el => {
            el.style.display = 'block';
        });
        
        // 禁用筛选器
        const filters = document.querySelectorAll('.filter-select, button');
        filters.forEach(filter => {
            filter.disabled = true;
        });
    }
    
    hideLoading() {
        const loadingElements = document.querySelectorAll('.loading');
        loadingElements.forEach(el => {
            el.style.display = 'none';
        });
        
        // 启用筛选器
        const filters = document.querySelectorAll('.filter-select, button');
        filters.forEach(filter => {
            filter.disabled = false;
        });
    }
    
    showMessage(type, message) {
        // 这里可以集成更漂亮的消息提示组件
        // 暂时使用alert
        alert(`${type}: ${message}`);
    }
    
    showError(message) {
        this.showMessage('错误', message);
    }
}

// 导出DashboardManager类到全局作用域
window.DashboardManager = DashboardManager;

// 如果页面中没有其他代码初始化dashboard，则自动初始化
if (!window.dashboardAutoInitDisabled) {
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.dashboard) {
            window.dashboard = new DashboardManager();
            window.dashboard.init();
        }
    });
}