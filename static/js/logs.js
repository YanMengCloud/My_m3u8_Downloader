// 日志管理
let logUpdateInterval;
let lastLogId = null;
let autoScroll = true;

// 在页面加载和标签切换时初始化日志
document.addEventListener('DOMContentLoaded', () => {
    const logLevel = document.getElementById('logLevel');
    if (logLevel) {
        logLevel.addEventListener('change', filterLogs);
    }
    
    // 初始化自动滚动按钮状态
    const autoScrollBtn = document.getElementById('autoScrollToggle');
    if (autoScrollBtn) {
        autoScrollBtn.classList.toggle('active', autoScroll);
    }
});

// 当切换到日志标签时开始更新
function startLogUpdates() {
    console.log('开始更新日志...');
    loadLogs();
    if (!logUpdateInterval) {
        logUpdateInterval = setInterval(updateLogs, 1000);
    }
}

// 当离开日志标签时停止更新
function stopLogUpdates() {
    console.log('停止更新日志...');
    if (logUpdateInterval) {
        clearInterval(logUpdateInterval);
        logUpdateInterval = null;
    }
}

// 加载所有日志
async function loadLogs() {
    try {
        const response = await fetch('/api/logs');
        if (!response.ok) throw new Error('获取日志失败');
        
        const logs = await response.json();
        const logContent = document.getElementById('logContent');
        if (!logContent) return;

        logContent.innerHTML = '';
        logs.forEach(log => {
            appendLog(log);
            if (log.id > lastLogId || lastLogId === null) {
                lastLogId = log.id;
            }
        });
        scrollToBottom();
    } catch (error) {
        console.error('加载日志失败:', error);
    }
}

// 更新日志（获取新日志）
async function updateLogs() {
    try {
        const response = await fetch(`/api/logs${lastLogId ? `?since=${lastLogId}` : ''}`);
        if (!response.ok) throw new Error('获取日志失败');
        
        const logs = await response.json();
        if (logs.length > 0) {
            logs.forEach(log => {
                appendLog(log);
                if (log.id > lastLogId || lastLogId === null) {
                    lastLogId = log.id;
                }
            });
            scrollToBottom();
        }
    } catch (error) {
        console.error('更新日志失败:', error);
    }
}

// 添加单条日志
function appendLog(log) {
    const logContent = document.getElementById('logContent');
    if (!logContent) return;

    const logElement = document.createElement('div');
    logElement.className = `log-entry ${log.level.toLowerCase()}`;
    logElement.dataset.level = log.level;
    
    const timestamp = new Date(log.timestamp).toLocaleString();
    logElement.innerHTML = `
        <span class="log-time">${timestamp}</span>
        <span class="log-level">${log.level}</span>
        <span class="log-message">${escapeHtml(log.message)}</span>
    `;
    
    logContent.appendChild(logElement);
}

// 过滤日志
function filterLogs() {
    const selectedLevel = document.getElementById('logLevel').value;
    const logEntries = document.querySelectorAll('.log-entry');
    
    logEntries.forEach(entry => {
        if (selectedLevel === 'ALL' || entry.dataset.level === selectedLevel) {
            entry.style.display = '';
        } else {
            entry.style.display = 'none';
        }
    });
}

// 清空日志
async function clearLogs() {
    if (!confirm('确定要清空所有日志吗？')) return;
    
    try {
        const response = await fetch('/api/logs/clear', { method: 'POST' });
        if (!response.ok) throw new Error('清空日志失败');
        
        const result = await response.json();
        if (result.status === 'success') {
            document.getElementById('logContent').innerHTML = '';
            lastLogId = null;
        }
    } catch (error) {
        console.error('清空日志失败:', error);
        alert('清空日志失败');
    }
}

// 导出日志
async function exportLogs() {
    try {
        const response = await fetch('/api/logs/export');
        if (!response.ok) throw new Error('导出日志失败');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `logs_${new Date().toISOString().slice(0,10)}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('导出日志失败:', error);
        alert('导出日志失败');
    }
}

// 滚动到底部
function scrollToBottom() {
    if (!autoScroll) return;
    const logContainer = document.getElementById('logContainer');
    if (logContainer) {
        logContainer.scrollTop = logContainer.scrollHeight;
    }
}

// 切换自动滚动
function toggleAutoScroll() {
    autoScroll = !autoScroll;
    const button = document.getElementById('autoScrollToggle');
    if (button) {
        button.classList.toggle('active', autoScroll);
    }
    if (autoScroll) {
        scrollToBottom();
    }
}

// HTML转义
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// 监听标签切换
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopLogUpdates();
    } else {
        const logsTab = document.getElementById('logsTab');
        if (logsTab && logsTab.style.display !== 'none') {
            startLogUpdates();
        }
    }
}); 