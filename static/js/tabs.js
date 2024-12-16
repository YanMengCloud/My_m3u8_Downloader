// 标签页管理
document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = tab.dataset.target;
            
            // 更新标签页状态
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // 更新内容区域
            tabContents.forEach(content => {
                if (content.id === targetId) {
                    content.classList.add('active');
                    // 如果是日志标签，启动日志更新
                    if (targetId === 'logsTab') {
                        startLogUpdates();
                    }
                } else {
                    content.classList.remove('active');
                    // 如果离开日志标签，停止日志更新
                    if (content.id === 'logsTab') {
                        stopLogUpdates();
                    }
                }
            });
        });
    });
    
    // 默认激活第一个标签
    const firstTab = tabs[0];
    if (firstTab) {
        firstTab.click();
    }
}); 