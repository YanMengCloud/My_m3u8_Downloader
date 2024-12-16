# 贡献指南

感谢您考虑为 My_m3u8_Downloader 项目做出贡献！

## 开发环境设置

1. Fork 并克隆项目
```bash
git clone https://github.com/YourUsername/My_m3u8_Downloader.git
cd My_m3u8_Downloader
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

## 代码风格

- 遵循 PEP 8 规范
- 使用 4 个空格缩进
- 最大行长度为 88 字符
- 使用有意义的变量名和函数名
- 添加适当的注释和文档字符串

## 提交规范

提交信息应该遵循以下格式：
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型（type）：
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 构建过程或辅助工具的变动

示例：
```
feat(download): 添加断点续传功能

- 实现文件分片下载
- 添加进度保存
- 优化重试机制

Closes #123
```

## 分支管理

- main: 主分支，保持稳定
- develop: 开发分支
- feature/*: 新功能分支
- fix/*: 修复分支
- release/*: 发布分支

## Pull Request 流程

1. 从最新的 develop 分支创建功能分支
2. 在功能分支上进行开发
3. 提交代码前：
   - 运行测试确保全部通过
   - 更新文档（如需要）
   - 遵循代码规范
4. 创建 Pull Request 到 develop 分支
5. 等待代码审查
6. 根据反馈进行修改
7. 合并到 develop 分支

## 测试

- 添加单元测试
- 确保测试覆盖率
- 运行所有测试：
```bash
python -m pytest
```

## 文档

- 更新 README.md
- 添加/更新 API 文档
- 更新 FAQ（如需要）
- 添加示例代码

## 报告问题

创建 Issue 时请包含：
- 问题描述
- 复现步骤
- 期望行为
- 实际行为
- 环境信息
- 相关日志
- 截图（如有）

## 联系方式

如有任何问题，请通过以下方式联系：
- 提交 Issue
- 发送邮件至：3405523@qq.com

## 行为准则

请参阅 [行为准则](CODE_OF_CONDUCT.md)。

## 许可证

通过提交 Pull Request，您同意您的贡献将采用与项目相同的 [MIT 许可证](LICENSE)。 