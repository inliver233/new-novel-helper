# LoreMaster - 小说辅助工具

一个专为小说创作设计的辅助工具，支持人物档案管理、世界观构建、剧情规划等功能，具有直观的图形界面和强大的拖拽排序功能。

## ✨ 主要功能

### 📁 分类管理
- **层级分类系统**：支持无限层级的分类嵌套，类似文件夹结构
- **智能拖拽排序**：
  - 🔄 同级分类顺序调整（拖拽到边缘显示插入线）
  - 📂 跨层级移动（拖拽到中心区域高亮目标分类）
  - 🎯 实时视觉反馈，清晰指示操作类型
- **右键菜单**：新建、重命名、删除分类
- **展开/折叠**：清晰的层级结构显示

### 📝 条目管理
- **富文本编辑**：支持标题、标签、内容编辑
- **拖拽排序**：条目在同一分类内可自由调整顺序
- **实时保存**：自动保存编辑内容
- **统计信息**：字数统计、创建时间、更新时间

### 🔍 搜索功能
- **全文搜索**：支持标题和内容搜索
- **快速导航**：搜索结果直接跳转到对应条目

### 🎨 用户界面
- **现代化设计**：深色主题，圆角设计，类似 VS Code 风格
- **三栏布局**：分类树 + 条目列表 + 内容编辑器
- **调整模式**：一键开启/关闭拖拽排序功能
- **状态反馈**：实时显示当前路径和操作状态
- **智能通知**：状态栏实时反馈操作结果，避免静默失败

### 🔧 系统稳定性
- **健壮的异常处理**：细化的异常类型，精确的错误定位
- **完整的日志系统**：自动记录操作日志，便于问题追踪
- **用户友好的错误提示**：清晰的错误信息和解决建议

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行程序
```bash
python main.py
```

## 📖 使用指南

### 基本操作
1. **创建分类**：右键分类树空白处或现有分类
2. **创建条目**：选择分类后点击"新建条目"按钮
3. **编辑内容**：在右侧编辑器中输入标题、标签和内容

### 拖拽排序
1. **开启调整模式**：点击工具栏的"调整"按钮
2. **分类排序**：
   - 拖拽到分类边缘 → 显示蓝色插入线 → 调整顺序
   - 拖拽到分类中心 → 蓝色高亮 → 移动到该分类内
3. **条目排序**：拖拽条目到目标位置，显示插入线指示

### 搜索功能
- 使用 `Ctrl+F` 或点击搜索按钮
- 输入关键词搜索标题和内容
- 点击搜索结果直接跳转

## 🏗️ 项目结构

```
loremaster/
├── src/                    # 源代码
│   ├── core/              # 核心业务逻辑
│   │   ├── business_manager.py    # 业务管理器
│   │   └── search_service.py      # 搜索服务
│   ├── data_access/       # 数据访问层
│   │   └── file_system_manager.py # 文件系统管理
│   ├── models/            # 数据模型
│   │   └── entry.py       # 条目模型
│   ├── ui/                # 用户界面
│   │   ├── main_window.py         # 主窗口
│   │   ├── enhanced_category_tree.py  # 增强分类树
│   │   ├── draggable_entry_list.py    # 可拖拽条目列表
│   │   ├── search_dialog.py       # 搜索对话框
│   │   ├── context_menu_helper.py # 上下文菜单辅助类
│   │   ├── ui_components.py       # UI组件工厂
│   │   └── ui_styles.py          # 统一样式管理
│   └── utils/             # 工具模块
│       ├── logger.py      # 日志配置和辅助函数
│       └── file_utils.py  # 文件操作工具函数
├── data/                  # 数据存储目录
├── logs/                  # 日志文件目录
├── main.py               # 程序入口
└── requirements.txt      # 依赖列表
```

## 💾 数据存储

- **分类**：以文件夹形式存储，支持嵌套结构
- **条目**：以 JSON 文件存储，包含完整的元数据
- **排序**：通过 `.order.json` 文件保存自定义排序
- **向后兼容**：无排序文件时自动使用字母排序

## 🔧 技术特性

- **框架**：PyQt6 - 现代化的 Python GUI 框架
- **架构**：分层架构，业务逻辑与界面分离
- **拖拽系统**：基于 Qt 拖拽框架的自定义实现
- **数据持久化**：JSON 格式，易于备份和迁移
- **模块化设计**：高内聚低耦合，易于扩展
- **日志系统**：完整的日志记录和错误追踪
- **异常处理**：细化的异常类型，提升调试体验
- **用户反馈**：实时状态通知，避免静默失败

## 📋 系统要求

- **Python**：3.9+ (推荐 3.11+)
- **操作系统**：Windows 10+, macOS 10.14+, Linux
- **内存**：最低 512MB，推荐 1GB+
- **存储**：50MB+ 可用空间

## 🎯 适用场景

- **小说创作**：人物设定、世界观构建、剧情规划
- **游戏设计**：角色档案、技能系统、剧情设计
- **学术研究**：资料整理、笔记管理、知识体系构建
- **项目管理**：文档整理、进度跟踪、资源管理

## 📈 最近更新

### v2.1.0 - 代码质量优化 (2025-06-21)
- ✅ **UI样式系统重构**：统一样式管理，消除代码冗余
- ✅ **异常处理细化**：精确的异常类型，提升调试体验
- ✅ **用户反馈机制**：状态栏通知，避免静默失败
- ✅ **代码重构优化**：提取通用工具，改善代码结构
- ✅ **日志系统完善**：完整的操作日志和错误追踪

## 🔮 未来规划

- [ ] 导入/导出功能（Markdown、Word、PDF）
- [ ] 模板系统（人物模板、世界观模板）
- [ ] 关系图谱（人物关系、事件时间线）
- [ ] 多主题支持（浅色主题、自定义主题）
- [ ] 插件系统（自定义功能扩展）
- [ ] 云同步支持（多设备协作）

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**LoreMaster** - 让创作更有序，让灵感更清晰 ✨
