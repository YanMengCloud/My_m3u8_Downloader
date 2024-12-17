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
        // console.log('渲染任务:', task); // 注释掉或删除这行
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
        const addToLibraryBtn = taskElement.querySelector('.add-to-library-btn');

        // 隐藏所有按钮
        [pauseBtn, resumeBtn, cancelBtn, deleteBtn, previewBtn, infoBtn, downloadBtn, addToLibraryBtn].forEach(btn => {
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
                addToLibraryBtn.style.display = '';
                addToLibraryBtn.disabled = false;
                deleteBtn.style.display = '';
                break;
            case 'failed':
            case 'cancelled':
                deleteBtn.style.display = '';
                break;
        }

        // 默认禁用添加至视频库按钮
        if (addToLibraryBtn && task.status !== 'completed') {
            addToLibraryBtn.disabled = true;
            addToLibraryBtn.style.opacity = '0.5';
            addToLibraryBtn.style.cursor = 'not-allowed';
        }

        // 添加按钮事件监听
        if (pauseBtn) pauseBtn.onclick = () => pauseTask(task.task_id);
        if (resumeBtn) resumeBtn.onclick = () => resumeTask(task.task_id);
        if (cancelBtn) cancelBtn.onclick = () => cancelTask(task.task_id);
        if (deleteBtn) deleteBtn.onclick = () => deleteTask(task.task_id);
        if (previewBtn) previewBtn.onclick = () => showPreview(task);
        if (infoBtn) infoBtn.onclick = () => showInfo(task);
        if (downloadBtn) downloadBtn.onclick = () => downloadFile(task);
        if (addToLibraryBtn) addToLibraryBtn.onclick = () => addToLibrary(task.task_id);

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

// 页面加载��开始更新
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

    // 使用预览模态框模板
    const modalTemplate = document.getElementById('previewModalTemplate');
    const modalContent = modalTemplate.content.cloneNode(true);
    document.body.appendChild(modalContent);

    const modal = document.querySelector('.modal-overlay');
    const closeButton = modal.querySelector('.modal-close');
    const previewGrid = modal.querySelector('.preview-grid');
    const videoPlayer = document.getElementById('taskVideo');

    // 清空预览网格内容
    previewGrid.innerHTML = '';

    // 修改视频源设置逻辑
    if (videoPlayer && task.video_metadata?.format?.filename) {
        const source = videoPlayer.querySelector('source');
        if (source) {
            source.src = `/temp/${task.task_id}/output.mp4`;
            source.type = 'video/mp4';
            videoPlayer.load();
        }
    }

    // 加载预览图
    const previewPaths = task.video_metadata?.preview_path || {};

    // 如果没有预览图数据，显示提示信息
    if (Object.keys(previewPaths).length === 0) {
        const noPreviewMsg = document.createElement('div');
        noPreviewMsg.className = 'no-preview-message';
        noPreviewMsg.innerHTML = `
            <i class="mdi mdi-image-off" style="font-size: 3rem; margin-bottom: 1rem;"></i>
            <p>暂无预览图</p>
        `;
        previewGrid.appendChild(noPreviewMsg);
        return;
    }

    // 使用预览路径数据创建预览网格
    Object.entries(previewPaths).forEach(([index, data]) => {
        const previewItem = document.createElement('div');
        previewItem.className = 'preview-item';
        
        // 检查路径是否存在
        if (!data.path) {
            console.error('Preview path is undefined:', data);
            return;
        }

        // 构建预览图路径 - 使用 /temp 作为基础路径
        const imgSrc = `/temp/${data.path}`;
        
        previewItem.innerHTML = `
            <img src="${imgSrc}" alt="视频预览" class="preview-image" 
                 onerror="this.onerror=null;this.src='/static/images/no-preview.png';"
                 onclick="showFullImage('${imgSrc}')">
            <div class="preview-timestamp">${formatDuration(data.timestamp)}</div>
        `;
        previewGrid.appendChild(previewItem);
    });

    // 标签切换功能
    const tabs = modal.querySelectorAll('.preview-tab');
    const contents = modal.querySelectorAll('.preview-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = tab.dataset.tab;
            
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            contents.forEach(content => {
                content.classList.remove('active');
                if (content.id === targetId) {
                    content.classList.add('active');
                }
            });
        });
    });

    // 关闭功能
    const closeModal = () => {
        if (videoPlayer) videoPlayer.pause();
        modal.remove();
    };

    closeButton.onclick = closeModal;
    modal.onclick = (e) => {
        if (e.target === modal) closeModal();
    };

    // ESC键关闭
    const handleEsc = (e) => {
        if (e.key === 'Escape') {
            closeModal();
            document.removeEventListener('keydown', handleEsc);
        }
    };
    document.addEventListener('keydown', handleEsc);

    // 显示模态框
    requestAnimationFrame(() => modal.classList.add('active'));

    // 添加下载按钮事件
    const downloadPreviewsBtn = modal.querySelector('.preview-download-btn');
    const downloadInfoBtn = modal.querySelector('.preview-info-btn');

    if (downloadPreviewsBtn) {
        downloadPreviewsBtn.onclick = () => downloadPreviews(task.task_id);
    }

    if (downloadInfoBtn) {
        downloadInfoBtn.onclick = () => downloadVideoInfo(task.task_id);
    }
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
        <button class="fullscreen-close-btn">&times;</button>
        <div class="fullscreen-image-container">
            <img src="${imageSrc}" class="fullscreen-image" alt="预览图">
        </div>
        <div class="zoom-controls">
            <button onclick="zoomImage('out')">
                <i class="mdi mdi-minus"></i>
            </button>
            <span class="zoom-text">100%</span>
            <button onclick="zoomImage('in')">
                <i class="mdi mdi-plus"></i>
            </button>
            <button onclick="zoomImage('reset')">
                <i class="mdi mdi-refresh"></i>
            </button>
        </div>
    `;
    
    // 将overlay添加到modal-container内部
    const modalContainer = document.querySelector('.modal-container');
    modalContainer.appendChild(overlay);
    
    // 图片拖动功能
    const container = overlay.querySelector('.fullscreen-image-container');
    const image = overlay.querySelector('.fullscreen-image');
    let isDragging = false;
    let startX, startY, translateX = 0, translateY = 0;
    let currentScale = 1;
    
    // 更新缩放文本
    const updateZoomText = () => {
        const zoomText = overlay.querySelector('.zoom-text');
        zoomText.textContent = `${Math.round(currentScale * 100)}%`;
    };
    
    // 缩放功能
    window.zoomImage = (action) => {
        const minScale = 0.5;
        const maxScale = 3;
        const step = 0.2;
        
        switch(action) {
            case 'in':
                if (currentScale < maxScale) {
                    currentScale = Math.min(currentScale + step, maxScale);
                }
                break;
            case 'out':
                if (currentScale > minScale) {
                    currentScale = Math.max(currentScale - step, minScale);
                }
                break;
            case 'reset':
                currentScale = 1;
                translateX = 0;
                translateY = 0;
                break;
        }
        
        image.style.transform = `translate(${translateX}px, ${translateY}px) scale(${currentScale})`;
        updateZoomText();
    };
    
    // 鼠标滚轮缩放
    container.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY;
        if (delta < 0) {
            zoomImage('in');
        } else {
            zoomImage('out');
        }
    });
    
    // 拖动开始
    container.addEventListener('mousedown', (e) => {
        if (e.button !== 0) return; // 只响应左键
        isDragging = true;
        startX = e.clientX - translateX;
        startY = e.clientY - translateY;
        image.classList.add('dragging');
    });
    
    // 拖动中
    container.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        translateX = e.clientX - startX;
        translateY = e.clientY - startY;
        image.style.transform = `translate(${translateX}px, ${translateY}px) scale(${currentScale})`;
    });
    
    // 拖动结束
    const endDrag = () => {
        isDragging = false;
        image.classList.remove('dragging');
    };
    container.addEventListener('mouseup', endDrag);
    container.addEventListener('mouseleave', endDrag);
    
    // 双击重置
    container.addEventListener('dblclick', () => {
        zoomImage('reset');
    });
    
    // 阻止事件冒泡
    overlay.addEventListener('click', (e) => {
        e.stopPropagation();
    });
    
    // 添加关闭按钮功能
    const closeBtn = overlay.querySelector('.fullscreen-close-btn');
    const closeOverlay = () => {
        overlay.classList.remove('active');
        setTimeout(() => {
            overlay.remove();
            delete window.zoomImage;
        }, 300);
    };
    
    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        closeOverlay();
    });
    
    // 点击图片容器外的区域关闭
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeOverlay();
        }
    });
    
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

// 视频播放相关功能
function initVideoPlayer(videoPath) {
    const video = document.getElementById('taskVideo');
    if (!video) return;
    
    const source = video.querySelector('source');
    if (!source) return;
    
    source.src = videoPath;
    source.type = 'video/mp4';
    
    // 重新加载视频
    video.load();
    
    // 添加错误处理
    video.onerror = function() {
        console.error('视频加载失败:', video.error);
        const errorMessages = {
            1: '视频加载被中止',
            2: '网络错误',
            3: '视频解码错误',
            4: '视频格式不支持'
        };
        alert(`视频加载失败: ${errorMessages[video.error.code] || '未知错误'}`);
    };
    
    // 添加加载状态处理
    video.onloadstart = function() {
        console.log('开始加载视频...');
    };
    
    video.oncanplay = function() {
        console.log('视频可以开始播放');
    };
}

function togglePlayPause() {
    const video = document.getElementById('taskVideo');
    if (video.paused) {
        video.play();
    } else {
        video.pause();
    }
}

function toggleMute() {
    const video = document.getElementById('taskVideo');
    video.muted = !video.muted;
    const muteButton = document.querySelector('.video-controls button:nth-child(2) i');
    muteButton.className = video.muted ? 'mdi mdi-volume-off' : 'mdi mdi-volume-high';
}

function toggleFullscreen() {
    const videoContainer = document.querySelector('.video-player');
    if (!document.fullscreenElement) {
        if (videoContainer.requestFullscreen) {
            videoContainer.requestFullscreen();
        } else if (videoContainer.webkitRequestFullscreen) {
            videoContainer.webkitRequestFullscreen();
        } else if (videoContainer.msRequestFullscreen) {
            videoContainer.msRequestFullscreen();
        }
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
    }
}

// 修改预览模态框的显示逻辑
function showPreviewModal(task) {
    const modalTemplate = document.getElementById('previewModalTemplate');
    const modalContent = modalTemplate.content.cloneNode(true);
    document.body.appendChild(modalContent);

    const modal = document.querySelector('.modal-overlay');
    const closeButton = modal.querySelector('.modal-close');
    const previewGrid = modal.querySelector('.preview-grid');
    const filename = modal.querySelector('.filename');

    // 设置文件名
    filename.textContent = task.filename;

    // 加载预览图
    const previewPaths = task.video_metadata?.preview_path || {};

    // 如果没有预览图数据，显示提示信息
    if (Object.keys(previewPaths).length === 0) {
        const noPreviewMsg = document.createElement('div');
        noPreviewMsg.className = 'no-preview-message';
        noPreviewMsg.innerHTML = `
            <i class="mdi mdi-image-off" style="font-size: 3rem; margin-bottom: 1rem;"></i>
            <p>暂无预览图</p>
        `;
        previewGrid.appendChild(noPreviewMsg);
        return;
    }

    // 使用预览路径数据创建预览网格
    Object.entries(previewPaths).forEach(([index, data]) => {
        const previewItem = document.createElement('div');
        previewItem.className = 'preview-item';
        const imgSrc = `/temp/${data.path}`;
        
        previewItem.innerHTML = `
            <img src="${imgSrc}" alt="视频预览" class="preview-image" 
                 onerror="this.onerror=null;this.src='/static/images/no-preview.png';"
                 onclick="showFullImage('${imgSrc}')">
            <div class="preview-timestamp">${formatDuration(data.timestamp)}</div>
        `;
        previewGrid.appendChild(previewItem);
    });

    // 初始化视频播放器
    if (task.status === 'completed') {
        initVideoPlayer(`/static/downloads/${task.task_id}/${task.filename}`);
    }

    // 标签切换功能
    const tabs = modal.querySelectorAll('.preview-tab');
    const contents = modal.querySelectorAll('.preview-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = tab.dataset.tab;
            
            // 更新标签状态
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // 更新内容显示
            contents.forEach(content => {
                content.classList.remove('active');
                if (content.id === targetId) {
                    content.classList.add('active');
                }
            });
        });
    });

    // 关闭模态框
    closeButton.onclick = () => {
        const video = document.getElementById('taskVideo');
        if (video) {
            video.pause();
        }
        document.body.removeChild(modal);
    };

    modal.onclick = (e) => {
        if (e.target === modal) {
            const video = document.getElementById('taskVideo');
            if (video) {
                video.pause();
            }
            document.body.removeChild(modal);
        }
    };
}

// 添加到视频库
async function addToLibrary(taskId) {
    try {
        const response = await fetch(`/api/video-library/add/${taskId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            alert('已成功添加到视频库');
            // 如果视频库标签页存在，更新其内容
            if (typeof updateVideoLibrary === 'function') {
                updateVideoLibrary();
            }
        } else {
            alert(data.error || '添加到视频库失败');
        }
    } catch (error) {
        console.error('添加到视频库失败:', error);
        alert('添加到视频库失败');
    }
}
 