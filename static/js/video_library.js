// 在文件开头添加变量存储所有视频
let allVideos = [];

// 更新视频库列表
async function updateVideoLibrary() {
    try {
        const response = await fetch('/api/video-library/list');
        const data = await response.json();
        
        if (data.status === 'success') {
            allVideos = data.videos; // 保存所有视频
            renderVideoGrid(allVideos); // 渲染所有视频
        } else {
            console.error('获取视频库列表失败:', data.error);
        }
    } catch (error) {
        console.error('更新视频库失败:', error);
    }
}

// 添加搜索功能
function initializeSearch() {
    const searchInput = document.getElementById('videoSearch');
    const searchClear = document.getElementById('searchClear');
    
    if (!searchInput || !searchClear) return;

    let searchTimeout;

    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const searchTerm = e.target.value.trim();
        
        // 控制清除按钮的显示
        searchClear.style.display = searchTerm ? 'block' : 'none';
        
        searchTimeout = setTimeout(() => {
            const searchTermLower = searchTerm.toLowerCase();
            const filteredVideos = searchTermLower ? 
                allVideos.filter(video => 
                    (video.title || '').toLowerCase().includes(searchTermLower) ||
                    (video.original_filename || '').toLowerCase().includes(searchTermLower)
                ) : allVideos;
            
            renderVideoGrid(filteredVideos, searchTerm);
        }, 300);
    });

    searchClear.addEventListener('click', () => {
        searchInput.value = '';
        searchClear.style.display = 'none';
        renderVideoGrid(allVideos);
        searchInput.focus();
    });

    // 添加搜索框快捷键
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchInput.value = '';
            searchClear.style.display = 'none';
            renderVideoGrid(allVideos);
            searchInput.blur();
        }
    });
}

// 渲染视频网格
function renderVideoGrid(videos, searchTerm = '') {
    const grid = document.getElementById('videoGrid');
    if (!grid) return;

    grid.innerHTML = '';

    if (!videos || videos.length === 0) {
        grid.innerHTML = `
            <div class="no-videos">
                <i class="mdi mdi-${searchTerm ? 'file-search-outline' : 'video-off'}"></i>
                <p>${
                    searchTerm 
                    ? `没有找到包含 "<span class="search-term">${searchTerm}</span>" 的视频`
                    : '视频库暂无视频'
                }</p>
                ${
                    searchTerm 
                    ? '<p style="font-size: 0.875rem; opacity: 0.7;">试试其他关键词？</p>'
                    : ''
                }
            </div>
        `;
        return;
    }

    videos.forEach(video => {
        const card = createVideoCard(video);
        if (card) {
            grid.appendChild(card);
        }
    });
}

// 创建视频卡片
function createVideoCard(video) {
    const template = document.getElementById('videoCardTemplate');
    if (!template) return null;

    const card = template.content.cloneNode(true).children[0];
    const videoInfo = video.video_info || {};
    const technicalInfo = videoInfo.technical_info || {};

    // 设置缩略图
    const thumbnail = card.querySelector('.video-thumbnail img');
    thumbnail.src = `/static/${video.preview_path}/preview_0.jpg`;
    thumbnail.onerror = () => {
        thumbnail.src = '/static/images/no-preview.png';
    };

    // 设置标题和编辑功能
    const title = card.querySelector('.video-title');
    title.textContent = video.title || video.original_filename;
    
    // 添加标题编辑功能
    let originalTitle = title.textContent;
    
    title.addEventListener('dblclick', () => {
        title.classList.add('editing');
        title.focus();
    });

    title.addEventListener('blur', async () => {
        title.classList.remove('editing');
        const newTitle = title.textContent.trim();
        
        if (newTitle && newTitle !== originalTitle) {
            try {
                const response = await fetch(`/api/video-library/${video.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ title: newTitle })
                });

                const data = await response.json();
                if (data.status === 'success') {
                    originalTitle = newTitle;
                } else {
                    title.textContent = originalTitle;
                    alert(data.error || '更新失败');
                }
            } catch (error) {
                console.error('更新标题失败:', error);
                title.textContent = originalTitle;
                alert('更新标题失败');
            }
        } else {
            title.textContent = originalTitle;
        }
    });

    title.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            title.blur();
        }
        if (e.key === 'Escape') {
            title.textContent = originalTitle;
            title.blur();
        }
    });

    // 设置元数据
    const resolution = card.querySelector('.resolution');
    const duration = card.querySelector('.duration');
    const fileSize = card.querySelector('.file-size');
    const createdAt = card.querySelector('.created-at');

    resolution.textContent = technicalInfo.resolution || '未知分辨率';
    duration.textContent = technicalInfo.duration ? formatDuration(technicalInfo.duration) : '未知时长';
    fileSize.textContent = technicalInfo.size ? formatBytes(technicalInfo.size) : '未知大小';
    createdAt.textContent = video.created_at ? new Date(video.created_at).toLocaleDateString() : '未知时间';

    // 添加按钮事件
    const previewBtn = card.querySelector('.preview-btn');
    const deleteBtn = card.querySelector('.delete-btn');

    previewBtn.onclick = () => {
        try {
            if (!video.video_info) {
                video.video_info = video.video_metadata || {};
            }
            showLibraryPreview(video);
        } catch (error) {
            console.error('显示预览失败:', error);
            alert('显示预览失败');
        }
    };
    deleteBtn.onclick = () => deleteVideo(video.id);

    return card;
}

// 显示编辑标题模态框
function showEditTitleModal(video) {
    // 先移除可能存在的旧模态框
    const existingModal = document.querySelector('.modal-overlay');
    if (existingModal) {
        existingModal.remove();
    }

    const modalHtml = `
        <div class="modal-overlay">
            <div class="edit-title-modal">
                <h3>编辑视频标题</h3>
                <input type="text" id="newTitle" value="${video.title || ''}" placeholder="输入新标题">
                <div class="modal-actions">
                    <button class="cancel-btn">取消</button>
                    <button class="save-btn">保存</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);

    const modal = document.querySelector('.modal-overlay');
    const input = document.getElementById('newTitle');
    const cancelBtn = modal.querySelector('.cancel-btn');
    const saveBtn = modal.querySelector('.save-btn');

    // 设置初始焦点
    setTimeout(() => input.focus(), 100);

    const closeModal = () => {
        modal.classList.add('fade-out');
        setTimeout(() => modal.remove(), 200);
    };

    cancelBtn.onclick = closeModal;
    modal.onclick = (e) => {
        if (e.target === modal) closeModal();
    };

    saveBtn.onclick = async () => {
        const newTitle = input.value.trim();
        if (!newTitle) {
            alert('标题不能为空');
            return;
        }

        try {
            const response = await fetch(`/api/video-library/${video.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title: newTitle })
            });

            const data = await response.json();
            if (data.status === 'success') {
                closeModal();
                updateVideoLibrary();
            } else {
                alert(data.error || '更新失败');
            }
        } catch (error) {
            console.error('更新标题失败:', error);
            alert('更新标题失败');
        }
    };

    // 添加ESC键关闭功能
    const handleEsc = (e) => {
        if (e.key === 'Escape') {
            closeModal();
            document.removeEventListener('keydown', handleEsc);
        }
    };
    document.addEventListener('keydown', handleEsc);
}

// 删除视频
async function deleteVideo(videoId) {
    if (!confirm('确定要删除这个视频吗？此操作不可恢复。')) {
        return;
    }

    try {
        const response = await fetch(`/api/video-library/${videoId}`, {
            method: 'DELETE'
        });

        const data = await response.json();
        if (data.status === 'success') {
            updateVideoLibrary();
        } else {
            alert(data.error || '删除失败');
        }
    } catch (error) {
        console.error('删除视频失败:', error);
        alert('删除视频失败');
    }
}

// 显示视频库预览
function showLibraryPreview(video) {
    console.log('Library Video object:', video);
    
    const modalTemplate = document.getElementById('videoLibraryPreviewModalTemplate');
    if (!modalTemplate) {
        console.error('找不到预览模态框模板');
        return;
    }

    // 先移除可能存在的旧模态框
    const existingModal = document.querySelector('.modal-overlay');
    if (existingModal) {
        existingModal.remove();
    }

    const modalContent = modalTemplate.content.cloneNode(true);
    document.body.appendChild(modalContent);

    const modal = document.querySelector('.modal-overlay');
    const closeButton = modal.querySelector('.modal-close');
    const previewGrid = modal.querySelector('.preview-grid');
    const videoPlayer = document.getElementById('libraryVideo');

    // 清空预览网格内容
    if (previewGrid) {
        previewGrid.innerHTML = '';
    }

    // 设置视频源
    if (videoPlayer) {
        const source = videoPlayer.querySelector('source');
        if (source && video.file_path) {
            source.src = `/static/${video.file_path}`;
            source.type = 'video/mp4';
            videoPlayer.load();
        }
    }

    // 加载预览图
    const previewPaths = video.video_info?.preview_path || {};
    
    if (previewGrid) {
        // 如果没有预览图数据，显示提示信息
        if (Object.keys(previewPaths).length === 0) {
            const noPreviewMsg = document.createElement('div');
            noPreviewMsg.className = 'no-preview-message';
            noPreviewMsg.innerHTML = `
                <i class="mdi mdi-image-off" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <p>暂无预览图</p>
            `;
            previewGrid.appendChild(noPreviewMsg);
        } else {
            // 使用预览路径数据创建预览网格
            Object.entries(previewPaths).forEach(([index, data]) => {
                const previewItem = document.createElement('div');
                previewItem.className = 'preview-item';
                
                // 检查路径是否存在
                if (!data.path) {
                    console.error('Preview path is undefined:', data);
                    return;
                }

                // 构建预览图路径
                const imgSrc = `/static/video_library/${video.task_id}/preview/${data.path.split('/').pop()}`;
                
                previewItem.innerHTML = `
                    <img src="${imgSrc}" alt="视频预览" class="preview-image" 
                         onerror="this.onerror=null;this.src='/static/images/no-preview.png';"
                         onclick="showFullImage('${imgSrc}')">
                    <div class="preview-timestamp">${formatDuration(data.timestamp)}</div>
                `;
                previewGrid.appendChild(previewItem);
            });
        }
    }

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

    // 添加下载按钮事件处理
    const downloadPreviewsBtn = modal.querySelector('.library-preview-download-btn');
    const downloadInfoBtn = modal.querySelector('.library-preview-info-btn');

    if (downloadPreviewsBtn) {
        downloadPreviewsBtn.onclick = async () => {
            try {
                const response = await fetch(`/api/video-library/${video.id}/download_previews`);
                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || '下载预览图失败');
                }
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `previews_${video.task_id}.zip`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } catch (error) {
                console.error('下载预览图失败:', error);
                alert(error.message);
            }
        };
    }

    if (downloadInfoBtn) {
        downloadInfoBtn.onclick = async () => {
            try {
                const response = await fetch(`/api/video-library/${video.id}/download_info`);
                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || '下载视频信息失败');
                }
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `video_info_${video.task_id}.json`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } catch (error) {
                console.error('下载视频信息失败:', error);
                alert(error.message);
            }
        };
    }

    // 显示模态框
    requestAnimationFrame(() => modal.classList.add('active'));
}

// 格式化时长
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

// 格式化文件大小
function formatBytes(bytes) {
    if (!bytes) return '未知';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    updateVideoLibrary();
    initializeSearch();
}); 