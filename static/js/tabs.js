// 标签页管理
document.addEventListener('DOMContentLoaded', () => {
    // 获取所有标签按钮和内容面板
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // 停止所有更新函数
    function stopAllUpdates() {
        if (typeof stopTaskUpdates === 'function') stopTaskUpdates();
        if (typeof stopLogUpdates === 'function') stopLogUpdates();
    }

    // 标签切换函数
    function switchTab(tabId) {
        // 停止所有更新
        stopAllUpdates();

        // 更新按钮状态
        tabButtons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.tab === tabId) {
                btn.classList.add('active');
            }
        });

        // 更新内容面板显示
        tabContents.forEach(content => {
            content.style.display = 'none';
            if (content.id === tabId) {
                content.style.display = 'block';
            }
        });

        // 根据标签页启动相应的更新
        if (tabId === 'downloadTab') {
            if (typeof startTaskUpdates === 'function') startTaskUpdates();
        } else if (tabId === 'logsTab') {
            if (typeof startLogUpdates === 'function') startLogUpdates();
        } else if (tabId === 'video-library') {
            if (typeof updateVideoLibrary === 'function') updateVideoLibrary();
        }
    }

    // 为每个标签按钮添加点击事件
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.dataset.tab;
            switchTab(tabId);
        });
    });

    // 初始化显示第一个标签页
    const firstTab = tabButtons[0];
    if (firstTab) {
        switchTab(firstTab.dataset.tab);
    }
}); 