// 处理下载表单提交
async function handleDownload(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    // 打印表单数据
    console.log('提交的表单数据:');
    for (let [key, value] of formData.entries()) {
        console.log(`${key}: ${value}`);
    }
    
    try {
        console.log('发送下载请求...');
        const response = await fetch('/api/task/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: formData.get('m3u8_url'),
                filename: formData.get('filename'),
                format: formData.get('format_type')
            })
        });
        
        console.log('收到响应:', response.status);
        const data = await response.json();
        console.log('响应数据:', data);
        
        if (data.error) {
            alert(data.error);
        } else if (data.status === 'success') {
            form.reset();
            // 立即更新任务列表
            updateTasks();
        }
    } catch (error) {
        console.error('创建下载任务失败:', error);
        alert('创建下载任务失败');
    }
}

// 更新任务列表
function updateTaskList(tasks) {
    const taskList = document.getElementById('taskList');
    if (!taskList) {
        console.error('找不到任务列表容器');
        return;
    }

    taskList.innerHTML = '';
    
    if (!tasks || tasks.length === 0) {
        taskList.innerHTML = `
            <div class="no-tasks">
                <i class="mdi mdi-playlist-remove" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <p>暂无下载任务</p>
            </div>
        `;
        return;
    }

    tasks.forEach(task => {
        if (!task) return;
        console.log('渲染任务:', task); // 添加日志
        const taskElement = createTaskElement(task);
        if (taskElement) {
            taskList.appendChild(taskElement);
        }
    });
}

// 创建任务元素
function createTaskElement(task) {
    const template = document.getElementById('taskItemTemplate');
    if (!template) {
        console.error('找不到任务模板');
        return null;
    }

    const taskElement = template.content.cloneNode(true).children[0];

    try {
        // 设置任务标题
        const titleElement = taskElement.querySelector('.task-title');
        titleElement.textContent = task.filename || (task.url ? task.url.split('/').pop() : '未命名任务');

        // 设置M3U8 URL
        const urlElement = taskElement.querySelector('.task-url');
        urlElement.textContent = task.url || '无URL信息';

        // 设置状态
        const statusElement = taskElement.querySelector('.task-status');
        statusElement.textContent = getStatusText(task.status);
        statusElement.className = `task-status ${task.status || 'unknown'}`;

        // 设置进度条
        const progressFill = taskElement.querySelector('.progress-fill');
        progressFill.style.width = `${task.progress || 0}%`;

        // 更新进度信息
        const progressText = taskElement.querySelector('.progress-text');
        const speedText = taskElement.querySelector('.speed-text');
        const timeText = taskElement.querySelector('.time-text');

        if (task.segments && typeof task.segments === 'object') {
            progressText.textContent = `${task.segments.downloaded || 0}/${task.segments.total || 0} 片段`;
        } else {
            progressText.textContent = '0/0 片段';
        }

        if (task.download_speed) {
            speedText.textContent = formatSpeed(task.download_speed);
        }

        if (task.estimated_time) {
            timeText.textContent = formatTime(task.estimated_time);
        }

        // 设置按钮状态
        const pauseBtn = taskElement.querySelector('.pause-btn');
        const resumeBtn = taskElement.querySelector('.resume-btn');
        const cancelBtn = taskElement.querySelector('.cancel-btn');
        const deleteBtn = taskElement.querySelector('.delete-btn');
        const previewBtn = taskElement.querySelector('.preview-btn');
        const infoBtn = taskElement.querySelector('.info-btn');
        const downloadBtn = taskElement.querySelector('.download-btn');

        // 隐藏所有按钮
        [pauseBtn, resumeBtn, cancelBtn, deleteBtn, previewBtn, infoBtn, downloadBtn].forEach(btn => {
            if (btn) btn.style.display = 'none';
        });

        // 根据任务状态显示相应按钮
        switch (task.status) {
            case 'pending':
                cancelBtn.style.display = '';
                deleteBtn.style.display = '';
                break;
            case 'downloading':
                pauseBtn.style.display = '';
                cancelBtn.style.display = '';
                break;
            case 'paused':
                resumeBtn.style.display = '';
                cancelBtn.style.display = '';
                deleteBtn.style.display = '';
                break;
            case 'completed':
                previewBtn.style.display = '';
                infoBtn.style.display = '';
                downloadBtn.style.display = '';
                deleteBtn.style.display = '';
                break;
            case 'failed':
            case 'cancelled':
                deleteBtn.style.display = '';
                break;
        }

        // 添加按钮事件监听
        if (pauseBtn) pauseBtn.onclick = () => pauseTask(task.task_id);
        if (resumeBtn) resumeBtn.onclick = () => resumeTask(task.task_id);
        if (cancelBtn) cancelBtn.onclick = () => cancelTask(task.task_id);
        if (deleteBtn) deleteBtn.onclick = () => deleteTask(task.task_id);
        if (previewBtn) previewBtn.onclick = () => showPreview(task);
        if (infoBtn) infoBtn.onclick = () => showInfo(task);
        if (downloadBtn) downloadBtn.onclick = () => downloadFile(task);

        return taskElement;
    } catch (error) {
        console.error('创建任务元素失败:', error, '任务数据:', task);
        return null;
    }
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'pending': '等待中',
        'downloading': '下载中',
        'paused': '已暂停',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消'
    };
    return statusMap[status] || status;
}

// 格式化下载速度
function formatSpeed(speed) {
    if (!speed) return '';
    const units = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
    let size = speed;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

// 格式化剩余时间
function formatTime(seconds) {
    if (!seconds) return '';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}时${minutes}分剩余`;
    } else if (minutes > 0) {
        return `${minutes}分${secs}秒剩余`;
    } else {
        return `${secs}秒剩余`;
    }
}

// 格式化时间
function formatDuration(seconds) {
    if (!seconds) return '未知';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}时${minutes}分${secs}秒`;
    } else if (minutes > 0) {
        return `${minutes}分${secs}秒`;
    } else {
        return `${secs}秒`;
    }
}

// 任务操作函数
async function pauseTask(taskId) {
    try {
        const response = await fetch(`/api/task/${taskId}/pause`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || '暂停任务失败');
        if (data.status === 'success') {
            // 立即更新任务列表
            updateTasks();
        }
    } catch (error) {
        console.error('暂停任务失败:', error);
        alert(error.message);
    }
}

async function resumeTask(taskId) {
    try {
        const response = await fetch(`/api/task/${taskId}/resume`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || '恢复任务失败');
        if (data.status === 'success') {
            // 立即更新任务列表
            updateTasks();
        }
    } catch (error) {
        console.error('恢复任务失败:', error);
        alert(error.message);
    }
}

async function cancelTask(taskId) {
    if (!confirm('确定要取消此任务吗？')) return;
    try {
        const response = await fetch(`/api/task/${taskId}/cancel`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || '取消任务失败');
        if (data.status === 'success') {
            // 立即更新任务列表
            updateTasks();
        }
    } catch (error) {
        console.error('取消任务失败:', error);
        alert(error.message);
    }
}

async function deleteTask(taskId) {
    if (!confirm('确定要删除此任务吗？')) return;
    try {
        const response = await fetch(`/api/task/${taskId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || '删除任务失败');
        if (data.status === 'success') {
            // 立即更新任务列表
            updateTasks();
        }
    } catch (error) {
        console.error('删除任务失败:', error);
        alert(error.message);
    }
}

// 定期更新任务列表
let updateInterval;

function startTaskUpdates() {
    // 立即更新一次
    updateTasks();
    // 每3秒更新一次
    updateInterval = setInterval(updateTasks, 3000);
}

function stopTaskUpdates() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

async function updateTasks() {
    try {
        const response = await fetch('/api/task/list');
        if (!response.ok) throw new Error('获取任务列表失败');
        const data = await response.json();
        if (data.status === 'success' && data.tasks) {
            // 将对象转换为数组
            const taskArray = Object.values(data.tasks);
            updateTaskList(taskArray);
        } else {
            console.error('任务表数据格式不正确:', data);
        }
    } catch (error) {
        console.error('更新任务列表失败:', error);
    }
}

// 页面加载时开始更新
document.addEventListener('DOMContentLoaded', startTaskUpdates);

// 页面隐藏时停止更新
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopTaskUpdates();
    } else {
        startTaskUpdates();
    }
});

// 显示模态框
function showModal(title, content) {
    // 创建模态框
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <style>
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 1rem;
                z-index: 1000;
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            
            .modal-overlay.active {
                opacity: 1;
            }
            
            .modal-container {
                background: var(--card-background);
                border-radius: 0.75rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                width: 100%;
                max-width: 800px;
                max-height: 90vh;
                overflow-y: auto;
                transform: translateY(20px);
                transition: transform 0.3s ease;
            }
            
            .modal-overlay.active .modal-container {
                transform: translateY(0);
            }
            
            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1.25rem 1.5rem;
                border-bottom: 1px solid var(--border-color);
            }
            
            .modal-title {
                font-size: 1.25rem;
                font-weight: 600;
                color: var(--text-primary);
                margin: 0;
            }
            
            .modal-close {
                background: none;
                border: none;
                font-size: 1.5rem;
                color: var(--text-secondary);
                cursor: pointer;
                padding: 0.5rem;
                margin: -0.5rem;
                border-radius: 0.375rem;
                transition: all 0.2s ease;
            }
            
            .modal-close:hover {
                color: var(--text-primary);
                background: var(--background-color);
            }
            
            .modal-body {
                padding: 1.5rem;
            }
            
            @media (max-width: 768px) {
                .modal-container {
                    max-width: 100%;
                    margin: 1rem;
                    max-height: calc(100vh - 2rem);
                }
                
                .modal-header {
                    padding: 1rem;
                }
                
                .modal-body {
                    padding: 1rem;
                }
            }
            
            /* 滚动条样式 */
            .modal-container::-webkit-scrollbar {
                width: 8px;
            }
            
            .modal-container::-webkit-scrollbar-track {
                background: var(--background-color);
                border-radius: 4px;
            }
            
            .modal-container::-webkit-scrollbar-thumb {
                background: var(--border-color);
                border-radius: 4px;
            }
            
            .modal-container::-webkit-scrollbar-thumb:hover {
                background: var(--text-secondary);
            }
        </style>
        <div class="modal-container">
            <div class="modal-header">
                <h3 class="modal-title">${title}</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                ${content}
            </div>
        </div>
    `;

    // 添加关闭功能
    const closeBtn = modal.querySelector('.modal-close');
    const closeModal = () => {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 300);
    };
    closeBtn.onclick = closeModal;
    modal.onclick = (e) => {
        if (e.target === modal) closeModal();
    };

    // 添加ESC键关闭功能
    const handleEsc = (e) => {
        if (e.key === 'Escape') {
            closeModal();
            document.removeEventListener('keydown', handleEsc);
        }
    };
    document.addEventListener('keydown', handleEsc);

    // 添加到页面并显示
    document.body.appendChild(modal);
    requestAnimationFrame(() => modal.classList.add('active'));
}

// 添加formatValue辅助函数
function formatValue(value, unit = '') {
    return value ? `${value}${unit}` : '未知';
}

// 显示视频预览
function showPreview(task) {
    if (!task.task_id) {
        alert('无效的任务ID');
        return;
    }

    // 获取预览图列表
    fetch(`/api/task/${task.task_id}/previews`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            const previews = data.previews || [];
            if (previews.length === 0) {
                alert('暂无预览图');
                return;
            }

            // 创建预览图HTML
            const previewsHtml = previews.map(preview => `
                <div class="preview-item">
                    <img src="${preview.url}" alt="视频预览" class="preview-image" 
                         onerror="this.onerror=null;this.src='/static/images/no-preview.png';"
                         onclick="showFullImage(this.src)">
                    <div class="preview-timestamp">${formatDuration(preview.timestamp)}</div>
                </div>
            `).join('');

            const content = `
                <div class="preview-grid">
                    ${previewsHtml}
                </div>
                <div class="preview-info">
                    <p class="filename">${task.filename || '未命名视频'}</p>
                    <div class="preview-actions">
                        <button onclick="downloadPreviews('${task.task_id}')" class="preview-download-btn">
                            <i class="mdi mdi-image-multiple"></i> 下载所有预览图
                        </button>
                        <button onclick="downloadVideoInfo('${task.task_id}')" class="preview-info-btn">
                            <i class="mdi mdi-information"></i> 下载视频信息
                        </button>
                    </div>
                </div>
                <style>
                    .preview-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 1rem;
                        margin-bottom: 1rem;
                    }
                    .preview-item {
                        position: relative;
                        border-radius: 0.5rem;
                        overflow: hidden;
                        cursor: pointer;
                    }
                    .preview-image {
                        width: 100%;
                        height: 200px;
                        object-fit: cover;
                        border-radius: 0.5rem;
                        transition: transform 0.2s;
                    }
                    .preview-image:hover {
                        transform: scale(1.05);
                    }
                    .preview-timestamp {
                        position: absolute;
                        bottom: 0.5rem;
                        right: 0.5rem;
                        background: rgba(0, 0, 0, 0.7);
                        color: white;
                        padding: 0.25rem 0.5rem;
                        border-radius: 0.25rem;
                        font-size: 0.875rem;
                    }
                    .preview-actions {
                        display: flex;
                        gap: 1rem;
                        margin-top: 1rem;
                        justify-content: center;
                    }
                    .preview-download-btn,
                    .preview-info-btn {
                        display: inline-flex;
                        align-items: center;
                        gap: 0.5rem;
                        padding: 0.5rem 1rem;
                        border-radius: 0.5rem;
                        border: none;
                        cursor: pointer;
                        font-size: 0.875rem;
                        transition: all 0.2s;
                    }
                    .preview-download-btn {
                        background-color: var(--primary-color);
                        color: white;
                    }
                    .preview-info-btn {
                        background-color: var(--background-color);
                        color: var(--text-primary);
                        border: 1px solid var(--border-color);
                    }
                    .preview-download-btn:hover {
                        background-color: var(--primary-hover);
                    }
                    .preview-info-btn:hover {
                        background-color: var(--border-color);
                    }
                    
                    /* 图片放大查看样式 */
                    .fullscreen-image-overlay {
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background: rgba(0, 0, 0, 0.9);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        z-index: 2000;
                        opacity: 0;
                        transition: opacity 0.3s ease;
                    }
                    .fullscreen-image-overlay.active {
                        opacity: 1;
                    }
                    .fullscreen-image {
                        max-width: 90%;
                        max-height: 90vh;
                        object-fit: contain;
                        border-radius: 0.5rem;
                        box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
                        transform: scale(0.9);
                        transition: transform 0.3s ease;
                    }
                    .fullscreen-image-overlay.active .fullscreen-image {
                        transform: scale(1);
                    }
                    .fullscreen-close {
                        position: absolute;
                        top: 1rem;
                        right: 1rem;
                        color: white;
                        font-size: 2rem;
                        cursor: pointer;
                        width: 40px;
                        height: 40px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background: rgba(0, 0, 0, 0.5);
                        border-radius: 50%;
                        transition: background-color 0.2s;
                    }
                    .fullscreen-close:hover {
                        background: rgba(255, 255, 255, 0.2);
                    }
                </style>
            `;

            showModal('视频预览', content);
        })
        .catch(error => {
            console.error('获取预览图失败:', error);
            alert(error.message);
        });
}

// 下载预览图
async function downloadPreviews(taskId) {
    try {
        const response = await fetch(`/api/task/${taskId}/download_previews`);
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || '下载预览图失败');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `previews_${taskId}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('下载预览图失败:', error);
        alert(error.message);
    }
}

// 下载视频信息
async function downloadVideoInfo(taskId) {
    try {
        const response = await fetch(`/api/task/${taskId}/download_info`);
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || '下载视频信息失败');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `video_info_${taskId}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('下载视频信息失败:', error);
        alert(error.message);
    }
}

// 显示视频信息
function showInfo(task) {
    const metadata = task.video_metadata || {};
    const technical_info = metadata.technical_info || {};
    
    // 使用technical_info.size作为文件大小
    const fileSize = technical_info.size ? formatBytes(technical_info.size) : '未知';
    
    const content = `
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">文件名</div>
                <div class="info-value">${task.filename || '未命名'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">分辨率</div>
                <div class="info-value">${formatValue(technical_info.resolution)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">时长</div>
                <div class="info-value">${technical_info.duration ? formatDuration(technical_info.duration) : '未知'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">编码</div>
                <div class="info-value">${formatValue(technical_info.codec)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">比特率</div>
                <div class="info-value">${technical_info.bitrate ? formatBytes(technical_info.bitrate) + '/s' : '未知'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">帧率</div>
                <div class="info-value">${technical_info.fps ? technical_info.fps + ' fps' : '未知'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">文件大小</div>
                <div class="info-value">${fileSize}</div>
            </div>
            <div class="info-item">
                <div class="info-label">下载状态</div>
                <div class="info-value">${getStatusText(task.status)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">开始时间</div>
                <div class="info-value">${task.start_time ? new Date(task.start_time).toLocaleString() : '未知'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">完成时间</div>
                <div class="info-value">${task.end_time ? new Date(task.end_time).toLocaleString() : '-'}</div>
            </div>
        </div>
    `;

    showModal('视频信息', content);
}

// 下载文件到本地
async function downloadFile(task) {
    if (!task.task_id) {
        alert('无效的任务ID');
        return;
    }

    try {
        const response = await fetch(`/api/task/${task.task_id}/download`);
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || '下载失败');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = task.filename || 'video.mp4';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('下载失败:', error);
        alert(error.message);
    }
}

// 添加图片放大查看函数
function showFullImage(imageSrc) {
    const overlay = document.createElement('div');
    overlay.className = 'fullscreen-image-overlay';
    overlay.innerHTML = `
        <img src="${imageSrc}" class="fullscreen-image" alt="预览图">
        <div class="fullscreen-close">&times;</div>
    `;
    
    document.body.appendChild(overlay);
    
    // 添加关闭功能
    const closeOverlay = () => {
        overlay.classList.remove('active');
        setTimeout(() => overlay.remove(), 300);
    };
    
    overlay.querySelector('.fullscreen-close').onclick = closeOverlay;
    overlay.onclick = (e) => {
        if (e.target === overlay) closeOverlay();
    };
    
    // 添加ESC键关闭功能
    const handleEsc = (e) => {
        if (e.key === 'Escape') {
            closeOverlay();
            document.removeEventListener('keydown', handleEsc);
        }
    };
    document.addEventListener('keydown', handleEsc);
    
    // 显示动画
    requestAnimationFrame(() => overlay.classList.add('active'));
}
 