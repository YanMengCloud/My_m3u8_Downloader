// 处理下载表单提交
async function handleDownload(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    try {
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
        
        const data = await response.json();
        if (data.status === 'success') {
            form.reset();
            // 立即更新任务列表
            updateTasks();
        } else {
            alert(data.error || '下载失败');
        }
    } catch (error) {
        console.error('创建下载任务失败:', error);
        alert('创建下载任务失败');
    }
}

// 处理M3U文件加载
async function handleM3uLoad(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    try {
        const response = await fetch('/api/task/load_m3u', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            // 将频道列表添加到下载表单
            const urls = data.channels.map(channel => channel.url).join('\n');
            document.getElementById('m3u8_url').value = urls;
        } else {
            alert(data.error || '加载M3U文件失败');
        }
    } catch (error) {
        console.error('加载M3U文件失败:', error);
        alert('加载M3U文件失败');
    }
} 