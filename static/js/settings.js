// 加载设置
async function loadSettings() {
    try {
        const response = await fetch('/api/config');
        const settings = await response.json();
        
        const maxConcurrent = document.getElementById('max-concurrent');
        const speedLimit = document.getElementById('speed-limit');
        const cleanupDays = document.getElementById('cleanup-days');
        const verifySSL = document.getElementById('verify-ssl');
        
        // 只在设置页面时更新值
        if (maxConcurrent && speedLimit && cleanupDays && verifySSL) {
            maxConcurrent.value = settings.max_concurrent;
            speedLimit.value = settings.speed_limit;
            cleanupDays.value = settings.cleanup_days;
            verifySSL.checked = settings.verify_ssl;
        }
    } catch (error) {
        console.error('加载设置失败:', error);
    }
}

// 保存设置
async function saveSettings() {
    const settings = {
        max_concurrent: parseInt(document.getElementById('max-concurrent').value),
        speed_limit: parseFloat(document.getElementById('speed-limit').value),
        cleanup_days: parseInt(document.getElementById('cleanup-days').value),
        verify_ssl: document.getElementById('verify-ssl').checked
    };
    
    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        if (response.ok) {
            alert('设置已保存');
        } else {
            throw new Error('保存设置失败');
        }
    } catch (error) {
        console.error('保存设置失败:', error);
        alert('保存设置失败');
    }
}

// 更新系统资源信息
async function updateSystemResources() {
    try {
        const response = await fetch('/api/system_resources');
        const data = await response.json();
        
        updateResourceCircle('cpu', data.cpu_percent);
        updateResourceCircle('memory', data.memory_percent);
        updateResourceCircle('disk', data.disk_usage);
    } catch (error) {
        console.error('更新系统资源信息失败:', error);
    }
}

// 更新资源圆环
function updateResourceCircle(type, value) {
    const circle = document.getElementById(`${type}-circle`);
    if (!circle) return;
    
    const valueElement = circle.querySelector('.resource-value');
    const progressCircle = circle.querySelector('.progress');
    
    // 更新数值
    valueElement.textContent = value.toFixed(1) + '%';
    
    // 更新进度圈
    const circumference = 2 * Math.PI * 48;
    const offset = circumference - (value / 100) * circumference;
    progressCircle.style.strokeDashoffset = offset;
    
    // 移除所有现有的状态类
    circle.classList.remove('warning', 'danger');
    
    // 根据使用率添加对应的状态类
    if (value >= 90) {
        circle.classList.add('danger');
    } else if (value >= 70) {
        circle.classList.add('warning');
    }
}

// 在页面加载时加载设置和开始更新系统资源信息
document.addEventListener('DOMContentLoaded', () => {
    // 只在设置页面时加载设置
    if (document.getElementById('settingsTab')) {
        loadSettings();
        // 开始定期更新系统资源信息
        updateSystemResources();
        const updateInterval = setInterval(updateSystemResources, 2000);
        
        // 页面卸载时清除定时器
        window.addEventListener('unload', () => {
            clearInterval(updateInterval);
        });
    }
}); 