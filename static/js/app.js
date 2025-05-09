// 全局状态管理
const state = {
    currentRequestId: 0,
    stats: {
        total: 0,
        success: 0,
        failed: 0,
        timeout: 0,
        statusCodes: {}
    }
};

// 更新IP信息显示
async function checkLocalIp() {
    const ipInfo = document.getElementById('ipInfo');
    ipInfo.innerHTML = '正在获取IP信息...';
    ipInfo.className = 'text-gray-600 animate-pulse';

    const maxRetries = 3;
    let retryCount = 0;

    while (retryCount < maxRetries) {
        try {
            // 使用ip-api.com获取位置信息
            const geoResponse = await fetch(`http://ip-api.com/json`);
            const geoData = await geoResponse.json();
            var ip = geoData.query
            let locationInfo = `IP: ${ip}`;
            if (geoData.status === 'success') {
                locationInfo += `\n位置: ${geoData.country} ${geoData.regionName} ${geoData.city}`;
                if (geoData.countryCode === 'CN') {
                    locationInfo += '\n\n⚠️ 当前IP为中国大陆IP，可能无法正常使用代理服务';
                    ipInfo.className = 'text-red-500';
                } else {
                    locationInfo += '\n\n✅ 当前IP为海外IP，可以正常使用代理服务';
                    ipInfo.className = 'text-green-500';
                }
            }
            ipInfo.innerHTML = locationInfo.replace(/\n/g, '<br>');
            return;
        } catch (error) {
            retryCount++;
            const retryDelay = Math.min(1000 * Math.pow(2, retryCount - 1), 5000);
            const errorMessage = error.message === 'Failed to fetch' 
                ? '网络连接失败，请检查网络设置或代理配置' 
                : error.message;
            
            if (retryCount === maxRetries) {
                ipInfo.innerHTML = `获取IP信息失败: ${errorMessage}<br>已达到最大重试次数 (${maxRetries}次)`;
                ipInfo.className = 'text-red-500';
            } else {
                ipInfo.innerHTML = `获取IP信息失败: ${errorMessage}<br>将在${retryDelay/1000}秒后进行第${retryCount + 1}次重试...`;
                ipInfo.className = 'text-yellow-500';
            }
            
            await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
    }
}

// 更新统计信息显示
function updateStatsDisplay() {
    const statsInfo = document.getElementById('statsInfo');
    if (state.stats.total > 0) {
        const successRate = ((state.stats.success / state.stats.total) * 100);
        const failedRate = ((state.stats.failed / state.stats.total) * 100);
        const timeoutRate = ((state.stats.timeout / state.stats.total) * 100);
        
        let statsText = `测试总数: ${state.stats.total}\n`;
        statsText += `成功次数: ${state.stats.success} (${successRate.toFixed(2)}%)\n`;
        statsText += `失败次数: ${state.stats.failed} (${failedRate.toFixed(2)}%)\n`;
        statsText += `超时次数: ${state.stats.timeout} (${timeoutRate.toFixed(2)}%)\n\n`;
        statsText += '状态码分布:\n';
        
        for (const [code, count] of Object.entries(state.stats.statusCodes)) {
            const percentage = (count / state.stats.total) * 100;
            statsText += `${code}: ${count} 次 (${percentage.toFixed(2)}%)\n`;
        }
        
        statsInfo.textContent = statsText;
    } else {
        statsInfo.textContent = '暂无测试数据';
    }
}

// 更新详细信息显示
function updateDetailsDisplay(details) {
    const detailsInfo = document.getElementById('detailsInfo');
    detailsInfo.textContent = details;
}

// 添加测试结果到表格
function addResultToTable(requestId, status, responseTime, statusInfo, details) {
    const resultsList = document.getElementById('resultsList');
    const row = document.createElement('tr');
    row.innerHTML = `
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${requestId}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm ${status === '成功' ? 'text-green-600' : 'text-red-600'}">${status}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${responseTime}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${statusInfo}</td>
    `;
    row.addEventListener('click', () => updateDetailsDisplay(details));
    row.classList.add('hover:bg-gray-50', 'cursor-pointer');
    resultsList.insertBefore(row, resultsList.firstChild);
}

// 清除测试结果
function clearResults() {
    const resultsList = document.getElementById('resultsList');
    resultsList.innerHTML = '';
    state.stats = {
        total: 0,
        success: 0,
        failed: 0,
        timeout: 0,
        statusCodes: {}
    };
    updateStatsDisplay();
    updateDetailsDisplay('');
}

// 执行单次测试
async function runSingleTest(targetUrl, proxyUrl) {
    const requestId = ++state.currentRequestId;
    
    try {
        const response = await fetch('/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                targetUrl,
                proxyUrl,
                requestId
            })
        });
        
        const result = await response.json();
        
        // 使用原子操作更新统计信息
        const updateStats = () => {
            state.stats.total++;
            
            if (result.success) {
                state.stats.success++;
                state.stats.statusCodes[result.statusCode] = (state.stats.statusCodes[result.statusCode] || 0) + 1;
                addResultToTable(
                    requestId,
                    '成功',
                    result.responseTime.toFixed(2),
                    result.statusCode,
                    result.details
                );
            } else {
                if (result.error === 'timeout') {
                    state.stats.timeout++;
                } else {
                    state.stats.failed++;
                }
                state.stats.statusCodes[result.error] = (state.stats.statusCodes[result.error] || 0) + 1;
                addResultToTable(
                    requestId,
                    result.error === 'timeout' ? '超时' : '失败',
                    result.responseTime ? result.responseTime.toFixed(2) : 'N/A',
                    result.error,
                    result.details
                );
            }
            
            updateStatsDisplay();
        };
        
        // 确保统计信息的原子性更新
        setTimeout(updateStats, 0);
        
    } catch (error) {
        const updateErrorStats = () => {
            state.stats.total++;
            state.stats.failed++;
            addResultToTable(
                requestId,
                '失败',
                'N/A',
                '执行错误',
                error.message
            );
            updateStatsDisplay();
        };
        
        setTimeout(updateErrorStats, 0);
    }
}

// 开始测试
async function startTest() {
    const targetUrl = document.getElementById('targetUrl').value;
    const proxyUrl = document.getElementById('proxyUrl').value;
    const testCount = parseInt(document.getElementById('testCount').value);
    const concurrency = parseInt(document.getElementById('concurrency').value);
    
    if (testCount <= 0 || concurrency <= 0) {
        alert('请输入大于0的测试次数和并发数量');
        return;
    }
    
    const startButton = document.getElementById('startTest');
    startButton.disabled = true;
    startButton.textContent = '测试中...';
    
    try {
        clearResults();
        
        // 创建所有测试任务
        const tasks = Array.from({ length: testCount }, (_, index) => {
            return async () => {
                await runSingleTest(targetUrl, proxyUrl);
            };
        });
        
        // 并发执行任务
        const executeTasks = async (tasks, concurrency) => {
            const results = [];
            const running = new Set();
            
            for (const task of tasks) {
                if (running.size >= concurrency) {
                    await Promise.race(running);
                }
                
                const promise = task().then(() => {
                    running.delete(promise);
                });
                
                running.add(promise);
                results.push(promise);
            }
            
            return Promise.all(results);
        };
        
        await executeTasks(tasks, concurrency);
    } catch (error) {
        console.error('测试执行错误:', error);
        alert('测试执行过程中发生错误: ' + error.message);
    } finally {
        startButton.disabled = false;
        startButton.textContent = '开始测试';
    }
}

// 初始化事件监听
document.addEventListener('DOMContentLoaded', () => {
    checkLocalIp();
    
    document.getElementById('refreshIp').addEventListener('click', checkLocalIp);
    document.getElementById('startTest').addEventListener('click', startTest);
    document.getElementById('clearResults').addEventListener('click', clearResults);
});

// 请求队列管理
class RequestQueue {
    constructor(concurrency = 5) {
        this.concurrency = concurrency;
        this.queue = [];
        this.running = 0;
    }

    async add(task) {
        this.queue.push(task);
        return this.process();
    }

    async process() {
        if (this.running >= this.concurrency) {
            return;
        }

        if (this.queue.length === 0) {
            return;
        }

        this.running++;
        const task = this.queue.shift();

        try {
            await task();
        } catch (error) {
            console.error('Task error:', error);
        }

        this.running--;
        return this.process();
    }
}

// 创建测试请求
async function createTestRequest(requestId, targetUrl, proxyUrl, maxRetries = 2) {
    let retryCount = 0;

    while (retryCount <= maxRetries) {
        try {
            const response = await fetch('/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    targetUrl,
                    proxyUrl,
                    requestId
                })
            });

            const data = await response.json();

            // 更新状态和UI
            if (data.success) {
                state.stats.success++;
                state.stats.statusCodes[data.statusCode] = (state.stats.statusCodes[data.statusCode] || 0) + 1;
                addResultToTable(requestId, '成功', data.responseTime.toFixed(2), data.statusCode, data.details);
            } else if (data.error === 'timeout') {
                state.stats.timeout++;
                addResultToTable(requestId, '超时', data.responseTime ? data.responseTime.toFixed(2) : 'N/A', '超时', data.details);
            } else {
                state.stats.failed++;
                addResultToTable(requestId, '失败', data.responseTime ? data.responseTime.toFixed(2) : 'N/A', data.error, data.details);
            }

            updateStatsDisplay();
            return;
        } catch (error) {
            retryCount++;
            if (retryCount <= maxRetries) {
                await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
                continue;
            }
            state.stats.failed++;
            addResultToTable(requestId, '失败', 'N/A', '请求异常', error.message);
            updateStatsDisplay();
        }
    }
}

// 开始测试按钮事件处理
document.getElementById('startTest').addEventListener('click', async () => {
    const startButton = document.getElementById('startTest');
    startButton.disabled = true;
    startButton.textContent = '测试中...';

    // 重置统计信息
    state.stats = {
        total: 0,
        success: 0,
        failed: 0,
        timeout: 0,
        statusCodes: {}
    };

    // 获取测试参数
    const targetUrl = document.getElementById('targetUrl').value;
    const proxyUrl = document.getElementById('proxyUrl').value;
    const testCount = parseInt(document.getElementById('testCount').value);
    const concurrency = parseInt(document.getElementById('concurrency').value);

    // 创建请求队列
    const queue = new RequestQueue(concurrency);
    state.stats.total = testCount;

    // 生成所有测试请求
    const requests = Array.from({ length: testCount }, (_, i) => {
        return () => createTestRequest(i + 1, targetUrl, proxyUrl);
    });

    // 并发执行请求
    try {
        await Promise.all(requests.map(request => queue.add(request)));
    } catch (error) {
        console.error('Test execution error:', error);
    }

    startButton.disabled = false;
    startButton.textContent = '开始测试';
});

// 初始化事件监听
document.addEventListener('DOMContentLoaded', () => {
    checkLocalIp();
    
    document.getElementById('refreshIp').addEventListener('click', checkLocalIp);
    document.getElementById('startTest').addEventListener('click', startTest);
    document.getElementById('clearResults').addEventListener('click', clearResults);
});