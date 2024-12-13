# 🎥 My_m3u8_Downloader

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![GitHub License](https://img.shields.io/github/license/YanMengCloud/My_m3u8_Downloader)](https://github.com/YanMengCloud/My_m3u8_Downloader/blob/main/LICENSE)
[![Docker](https://img.shields.io/badge/docker-%E2%9C%93-blue)](https://www.docker.com/)
[![GitHub Stars](https://img.shields.io/github/stars/YanMengCloud/My_m3u8_Downloader?style=social)](https://github.com/YanMengCloud/My_m3u8_Downloader/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/YanMengCloud/My_m3u8_Downloader)](https://github.com/YanMengCloud/My_m3u8_Downloader/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/YanMengCloud/My_m3u8_Downloader)](https://github.com/YanMengCloud/My_m3u8_Downloader/pulls)
[![Last Commit](https://img.shields.io/github/last-commit/YanMengCloud/My_m3u8_Downloader)](https://github.com/YanMengCloud/My_m3u8_Downloader/commits/main)

</div>

<p align="center">
    <strong>一个简单易用的 M3U8 视频下载工具</strong>
</p>

<p align="center">
    <a href="#功能特点">功能特点</a> •
    <a href="#安装说明">安装说明</a> •
    <a href="#使用指南">使用指南</a> •
    <a href="#未来计划">未来计划</a>
</p>


## ✨ 功能特点

- 🚀 支持批量下载 M3U8 视频
- 🔒 支持 AES-128 加密视频的下载和解密
- ⏸️ 支持暂停/继续下载功能
- 📊 实时显示下载进度和速度
- 🎮 简洁直观的用户界面
- 🛠️ 可配置的系统设置
- 📈 系统资源监控
- 🗑️ 自动清理临时文件
- 📁 支持文件批量导入链接
- 🔄 支持断点续传
- 🎯 精确的进度显示

## 🚀 安装说明

### 使用 Docker（推荐）

```bash
# 克隆仓库
git clone https://github.com/YanMengCloud/My_m3u8_Downloader.git

# 进入项目目录
cd My_m3u8_Downloader

# 构建并启动服务
docker-compose up -d
```

### 手动安装

```bash
# 克隆仓库
git clone https://github.com/YanMengCloud/My_m3u8_Downloader.git

# 进入项目目录
cd My_m3u8_Downloader

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py
```

## 📖 使用指南

### 基本使用

1. 访问 `http://localhost:7101` 打开Web界面
2. 在输入框中粘贴 M3U8 链接（支持多行批量输入）
3. 设置下载选项（可选）：
   - 选择输出格式（MP4/TS）
   - 设置自定义文件名
   - 配置加密相关参数（如需要）
4. 点击"开始下载"按钮


### 高级功能

#### 加密视频下载
- 支持输入密钥URL
- 支持手动输入IV值
- 自动识别加密方式

#### 批量导入
- 支持从文本文件导入链接
- 支持从 M3U/M3U8 播放列表导入

#### 系统设置
- 可配置最大并发下载数
- 可设置下载速度限制
- 可调整临时文件保留时间
- 可开关 SSL 证书验证

<p align="center">
    <img src="docs/images/settings.png" alt="Settings" width="800">
</p>

## 🔮 未来计划

### 核心功能增强
- [ ] 支持更多加密方式（如 AES-192/256）
- [ ] 添加视频格式转换功能
- [ ] 支持自定义视频合并参数
- [ ] 添加下载队列优先级管理
- [ ] 优化断点续传功能

### 用户体验改进
- [ ] 添加深色模式支持
- [ ] 支持拖拽排序下载任务
- [ ] 添加下载完成通知（桌面/邮件）
- [ ] 支持自定义主题
- [ ] 优化移动端适配
- [ ] 添加多语言支持

### 高级功能
- [ ] 集成在线视频预览
- [ ] 添加用户系统和权限管理
- [ ] 支持远程下载管理（API/WebSocket）
- [ ] 添加 RESTful API 接口
- [ ] 支持自动识别视频信息
- [ ] 集成视频元数据编辑
- [ ] 添加智能任务调度

### 其他功能
- [ ] JSON/CSV 格式导出下载历史
- [ ] 添加定时下载功能
- [ ] 集成多种代理支持（HTTP/SOCKS）
- [ ] 智能速度限制
- [ ] WebDAV 存储支持
- [ ] 自动更新检查

## 🛠️ 技术栈

- 后端：Python + Flask
- 前端：HTML + CSS + JavaScript
- 容器化：Docker + Docker Compose

## 📸 项目截图

### 主界面
<p align="center">
    <img src="docs/images/main.png" alt="Main UI" width="800">
</p>
<p align="center">
    <img src="docs/images/main2.png" alt="Main UI" width="800">
</p>

### 上传文件下载
<p align="center">
    <img src="docs/images/file.png" alt="Main UI" width="800">
</p>

### 系统监控
<p align="center">
    <img src="docs/images/settings.png" alt="System Monitor" width="800">
</p>

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详细信息

## 🤝 贡献指南

1. Fork 本仓库
2. 创建新的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 🐛 问题反馈

如果您在使用过程中遇到任何问题，请：

1. 查看 [常见问题](docs/FAQ.md)
2. 搜索现有 [Issues](https://github.com/YanMengCloud/My_m3u8_Downloader/issues)
3. 创建新的 Issue

## 📧 联系方式

- 作者：张宇豪
- 邮箱：3405523@qq.com

## 🌟 致谢

- [FFmpeg](https://ffmpeg.org/)
- [m3u8](https://github.com/globocom/m3u8)
- [requests](https://github.com/psf/requests)
- [pycryptodome](https://github.com/Legrandin/pycryptodome)

---

<p align="center">
    如果这个项目对您有帮助，请给个 Star ⭐️
</p>
