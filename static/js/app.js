// 标签页切换功能
function showTab(tabId) {
    // 隐藏所有标签页
    document.querySelectorAll('.tab-content').forEach(tab => {
        if (tab) {
            tab.style.display = 'none';
        }
    });
    
    // 显示选中的标签页
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.style.display = 'block';
    }
    
    // 更新按钮激活状态
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
        if (button.getAttribute('onclick').includes(tabId)) {
            button.classList.add('active');
        }
    });
}

// 通用的API调用函数
async function fetchApi(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API调用失败:', error);
        throw error;
    }
}

// 页面加载时显示下载标签页
document.addEventListener('DOMContentLoaded', () => {
    showTab('downloadTab');
}); 