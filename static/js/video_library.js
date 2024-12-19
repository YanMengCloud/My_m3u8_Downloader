// 在文件开头添加变量存储所有视频
let allVideos = [];

// 添加加载状态变量
let isLoading = false;

// 更新视频库列表
async function updateVideoLibrary() {
    try {
        isLoading = true;
        renderVideoGrid([]); // 显示加载状态

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
    } finally {
        isLoading = false;
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

    if (isLoading) {
        grid.innerHTML = `
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <div class="loading-text">正在加载视频库...</div>
            </div>
        `;
        return;
    }

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
    const thumbnailIndex = video.thumbnail_index || 0;  // 使用保存的索引
    thumbnail.src = `/static/${video.preview_path}/preview_${thumbnailIndex}.jpg`;
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
                    showToast('标题修改成功');
                } else {
                    title.textContent = originalTitle;
                    showToast(data.error || '更新失败', 'error');
                }
            } catch (error) {
                console.error('更新标题失败:', error);
                title.textContent = originalTitle;
                showToast('更新标题失败', 'error');
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
    const infoBtn = card.querySelector('.info-btn');
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

    infoBtn.onclick = () => showVideoInfo(video);
    deleteBtn.onclick = () => deleteVideo(video.id);

    const editThumbnailBtn = card.querySelector('.edit-thumbnail-btn');
    editThumbnailBtn.onclick = (e) => {
        e.stopPropagation(); // 防止触发卡片的点击事件
        showThumbnailSelector(video, thumbnail);
    };

    return card;
}

// 添加封面选择器函数
function showThumbnailSelector(video, thumbnailImg) {
    const modalTemplate = document.getElementById('thumbnailSelectorModalTemplate');
    if (!modalTemplate) return;

    const modalContent = modalTemplate.content.cloneNode(true);
    document.body.appendChild(modalContent);

    const modal = document.querySelector('.modal-overlay');
    const closeButton = modal.querySelector('.modal-close');
    const thumbnailGrid = modal.querySelector('.thumbnail-grid');

    // 获取预览图列表
    const previewPaths = video.video_info?.preview_path || {};
    
    // 添加预览图选项
    Object.entries(previewPaths).forEach(([index, data]) => {
        const option = document.createElement('div');
        option.className = 'thumbnail-option';
        
        const imgSrc = `/static/video_library/${video.task_id}/preview/${data.path.split('/').pop()}`;
        
        option.innerHTML = `
            <img src="${imgSrc}" alt="预览图">
            <div class="timestamp">${formatDuration(data.timestamp)}</div>
        `;

        // 如果是当前封面，添加选中状态
        if (thumbnailImg.src === imgSrc) {
            option.classList.add('selected');
        }

        // 点击选择新封面
        option.onclick = async () => {
            try {
                const response = await fetch(`/api/video-library/${video.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        thumbnail_index: index 
                    })
                });

                const data = await response.json();
                if (data.status === 'success') {
                    // 更新卡片中的封面图
                    thumbnailImg.src = imgSrc;
                    // 更新视频对象中的封面索引
                    video.thumbnail_index = parseInt(index);
                    modal.remove();
                    showToast('封面更新成功');
                } else {
                    throw new Error(data.error || '更新封面失败');
                }
            } catch (error) {
                console.error('更新封面失败:', error);
                showToast(error.message, 'error');
            }
        };

        thumbnailGrid.appendChild(option);
    });

    // 关闭功能
    const closeModal = () => modal.remove();
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
    const previewList = modal.querySelector('.preview-list');
    const videoPlayer = modal.querySelector('#libraryVideo');

    console.log('Video player element:', videoPlayer); // 添加调试日志

    // 初始化 Plyr
    const player = new Plyr(videoPlayer, {
        controls: [
            'play-large', // 大播放按钮
            'play', // 播放/暂停
            'progress', // 进度条
            'current-time', // 当前时间
            'duration', // 总时长
            'mute', // 静音
            'volume', // 音量
            'settings', // 设置
            'fullscreen' // 全屏
        ],
        settings: ['quality', 'speed'], // 设置菜单项
        speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] }, // 播放速度选项
        keyboard: { focused: true, global: false }, // 键盘控制
        tooltips: { controls: true, seek: true }, // 显示提示
        i18n: {
            speed: '播放速度',
            normal: '正常',
            quality: '视频质量',
            play: '播放',
            pause: '暂停',
            mute: '静音',
            unmute: '取消静音',
            enterFullscreen: '全屏',
            exitFullscreen: '退出全屏',
            settings: '设置'
        }
    });

    // 设置视频源
    if (videoPlayer && video.file_path) {
        const source = videoPlayer.querySelector('source');
        if (source) {
            source.src = `/static/${video.file_path}`;
            videoPlayer.load();
            player.source = {
                type: 'video',
                sources: [{
                    src: `/static/${video.file_path}`,
                    type: 'video/mp4',
                }]
            };
        }
    }

    // 加载预览图
    const previewPaths = video.video_info?.preview_path || {};
    
    if (previewList) {
        // 如果没有预览图数据，显示提示信息
        if (Object.keys(previewPaths).length === 0) {
            const noPreviewMsg = document.createElement('div');
            noPreviewMsg.className = 'no-preview-message';
            noPreviewMsg.innerHTML = `
                <i class="mdi mdi-image-off"></i>
                <p>暂无预览图</p>
            `;
            previewList.appendChild(noPreviewMsg);
        } else {
            // 使用预览路径数据创建预览网格
            Object.entries(previewPaths).forEach(([index, data]) => {
                const previewItem = document.createElement('div');
                previewItem.className = 'preview-item';
                
                if (!data.path) {
                    console.error('Preview path is undefined:', data);
                    return;
                }

                const imgSrc = `/static/video_library/${video.task_id}/preview/${data.path.split('/').pop()}`;
                
                previewItem.innerHTML = `
                    <img src="${imgSrc}" alt="预览图" 
                         onerror="this.onerror=null;this.src='/static/images/no-preview.png';">
                    <div class="preview-timestamp">${formatDuration(data.timestamp)}</div>
                `;

                // 点击预览图时跳转到对应时间点
                previewItem.onclick = () => {
                    const allPreviews = previewList.querySelectorAll('.preview-item');
                    allPreviews.forEach(item => item.classList.remove('active'));
                    previewItem.classList.add('active');
                    
                    if (player) {
                        player.currentTime = data.timestamp;
                        player.play();
                    }
                };

                previewList.appendChild(previewItem);
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
        if (player) {
            player.destroy();
        }
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
    const downloadVideoBtn = modal.querySelector('.library-video-download-btn');

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

    if (downloadVideoBtn) {
        downloadVideoBtn.onclick = async () => {
            try {
                const response = await fetch(`/api/video-library/${video.id}/download_video`);
                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || '下载视频失败');
                }
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = video.original_filename || `video_${video.task_id}.mp4`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } catch (error) {
                console.error('下载视频失败:', error);
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

// 显示视频信息模态框
function showVideoInfo(video) {
    const modalTemplate = document.getElementById('videoInfoModalTemplate');
    if (!modalTemplate) return;

    console.log('Video info:', video.video_info); // 添加调试日志

    const modalContent = modalTemplate.content.cloneNode(true);
    document.body.appendChild(modalContent);

    const modal = document.querySelector('.modal-overlay');
    const closeButton = modal.querySelector('.modal-close');

    // 填充基本信息
    modal.querySelector('#videoTitle').textContent = video.title || '未知';
    modal.querySelector('#originalFilename').textContent = video.original_filename || '未知';
    modal.querySelector('#createdTime').textContent = video.created_at ? 
        new Date(video.created_at).toLocaleString() : '未知';
    modal.querySelector('#updatedTime').textContent = video.updated_at ? 
        new Date(video.updated_at).toLocaleString() : '未知';

    // 填充技术参数
    const format = video.video_info?.format || {};
    const streams = video.video_info?.streams || [];
    const metadata = video.video_info?.metadata || {};
    
    // 查找视频流和音频流
    const videoStream = streams.find(s => s.codec_type === 'video');
    const audioStream = streams.find(s => s.codec_type === 'audio');

    // 视频编码信息
    modal.querySelector('#videoCodec').textContent = videoStream ? 
        `${videoStream.codec_name.toUpperCase()} / ${videoStream.codec_long_name} (${videoStream.profile})` : '未知';

    // 音频编码信息
    modal.querySelector('#audioCodec').textContent = audioStream ? 
        `${audioStream.codec_name.toUpperCase()} / ${audioStream.codec_long_name} (${audioStream.profile})` : '未知';

    // 分辨率
    const resolution = videoStream ? 
        `${videoStream.width}x${videoStream.height} (DAR: ${videoStream.display_aspect_ratio})` : 
        format.resolution || '未知';
    modal.querySelector('#resolution').textContent = resolution;

    // 时长
    modal.querySelector('#duration').textContent = format.duration ? 
        formatDuration(parseFloat(format.duration)) : '未知';

    // 总比特率
    modal.querySelector('#bitrate').textContent = format.bit_rate ? 
        `${Math.round(format.bit_rate / 1000)} Kbps (视频: ${Math.round(videoStream.bit_rate / 1000)} Kbps, 音频: ${Math.round(audioStream.bit_rate / 1000)} Kbps)` : '未知';

    // 文件大小
    modal.querySelector('#fileSize').textContent = format.size ? 
        formatBytes(parseInt(format.size)) : '未知';

    // 帧率
    const fps = videoStream?.r_frame_rate ? 
        eval(videoStream.r_frame_rate) : // 计算实际帧率
        (format.fps || '未知');
    modal.querySelector('#fps').textContent = typeof fps === 'number' ? fps.toFixed(2) + ' fps' : fps;

    // 添加更多技术信息
    const infoGrid = modal.querySelector('.info-grid');
    
    // 视频详细信息
    if (videoStream) {
        appendInfoItem(infoGrid, '编码器', videoStream.codec_long_name);
        appendInfoItem(infoGrid, '像素格式', videoStream.pix_fmt);
        appendInfoItem(infoGrid, '色彩范围', videoStream.color_range);
        appendInfoItem(infoGrid, '色彩空间', videoStream.color_space);
        appendInfoItem(infoGrid, '色彩转换', videoStream.color_transfer);
        appendInfoItem(infoGrid, '色彩原色', videoStream.color_primaries);
        appendInfoItem(infoGrid, '总帧数', videoStream.nb_frames);
        appendInfoItem(infoGrid, '编码宽度', `${videoStream.coded_width}x${videoStream.coded_height}`);
    }

    // 音频详细信息
    if (audioStream) {
        appendInfoItem(infoGrid, '音频采样率', `${audioStream.sample_rate} Hz`);
        appendInfoItem(infoGrid, '音频通道数', audioStream.channels);
        appendInfoItem(infoGrid, '声道布局', audioStream.channel_layout);
        appendInfoItem(infoGrid, '音频帧数', audioStream.nb_frames);
        appendInfoItem(infoGrid, '音频格式', audioStream.sample_fmt);
    }

    // 格式信息
    appendInfoItem(infoGrid, '容器格式', format.format_long_name);
    appendInfoItem(infoGrid, '流数量', format.nb_streams);

    // 元数据信息
    if (metadata) {
        appendInfoItem(infoGrid, '主要品牌', metadata.major_brand);
        appendInfoItem(infoGrid, '兼容品牌', metadata.compatible_brands);
        appendInfoItem(infoGrid, '编码器', metadata.encoder);
    }

    // 关闭功能
    const closeModal = () => modal.remove();
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
}

// 辅助函数：添加信息项
function appendInfoItem(container, label, value) {
    const item = document.createElement('div');
    item.className = 'info-item';
    item.innerHTML = `
        <span class="info-label">${label}</span>
        <span class="info-value">${value}</span>
    `;
    container.appendChild(item);
}

// 添加一个通用的提示函数
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="mdi mdi-${type === 'success' ? 'check-circle' : 'alert-circle'}"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);
    
    // 添加显示类
    requestAnimationFrame(() => toast.classList.add('show'));
    
    // 3秒后移除
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
} 