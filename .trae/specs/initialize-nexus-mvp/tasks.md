# Tasks

## 阶段一：项目初始化与基础架构

- [x] Task 1: 初始化 Tauri v2 项目结构
  - [x] SubTask 1.1: 创建 Tauri v2 项目基础结构
  - [x] SubTask 1.2: 配置 Vue3 + TypeScript + Tailwind CSS 前端
  - [x] SubTask 1.3: 配置 Python FastAPI 后端服务
  - [x] SubTask 1.4: 设置项目目录结构和配置文件

- [x] Task 2: 设计数据模型与数据库架构
  - [x] SubTask 2.1: 设计 SQLite 数据库表结构（用户配置、对话历史、文档索引）
  - [x] SubTask 2.2: 集成 SQLite-vec 向量数据库扩展
  - [x] SubTask 2.3: 实现数据库初始化和迁移脚本

## 阶段二：统一AI模型接入层

- [x] Task 3: 实现模型适配器接口
  - [x] SubTask 3.1: 设计统一的 AI 模型接口抽象类
  - [x] SubTask 3.2: 实现 Ollama 本地模型适配器
  - [x] SubTask 3.3: 实现 OpenAI API 适配器
  - [x] SubTask 3.4: 实现 DeepSeek API 适配器
  - [x] SubTask 3.5: 集成 LiteLLM 统一接口层

- [x] Task 4: 开发模型管理功能
  - [x] SubTask 4.1: 实现模型配置存储（API Key加密存储）
  - [x] SubTask 4.2: 实现模型状态检测和监控
  - [x] SubTask 4.3: 实现模型快速配置界面（前端）
  - [x] SubTask 4.4: 实现模型切换下拉组件（前端）

## 阶段三：本地知识库系统

- [x] Task 5: 实现文档处理管道
  - [x] SubTask 5.1: 实现文档上传接口（支持拖拽）
  - [x] SubTask 5.2: 实现 PDF 文本提取功能
  - [x] SubTask 5.3: 实现 Markdown/TXT 文档解析
  - [x] SubTask 5.4: 实现自适应文本分块算法

- [x] Task 6: 构建向量检索系统
  - [x] SubTask 6.1: 实现文本向量化（调用嵌入模型）
  - [x] SubTask 6.2: 实现向量存储到 SQLite-vec
  - [x] SubTask 6.3: 实现基于相似度的向量检索
  - [x] SubTask 6.4: 实现混合检索策略（关键词+向量）

- [x] Task 7: 开发文档管理界面
  - [x] SubTask 7.1: 实现文档列表展示组件
  - [x] SubTask 7.2: 实现文档删除和重命名功能
  - [x] SubTask 7.3: 实现文档上传进度显示

## 阶段四：本地动作执行引擎

- [x] Task 8: 实现安全沙箱机制
  - [x] SubTask 8.1: 设计命令执行权限模型
  - [x] SubTask 8.2: 实现命令预览和用户确认对话框
  - [x] SubTask 8.3: 实现命令执行隔离环境
  - [x] SubTask 8.4: 实现执行结果反馈机制

- [x] Task 9: 开发预定义动作库
  - [x] SubTask 9.1: 实现文件操作动作（整理、移动、重命名）
  - [x] SubTask 9.2: 实现笔记创建动作
  - [x] SubTask 9.3: 实现系统信息查询动作
  - [x] SubTask 9.4: 实现自定义 Python 脚本执行器

- [x] Task 10: 开发动作管理界面
  - [x] SubTask 10.1: 实现动作选择面板
  - [x] SubTask 10.2: 实现命令历史记录展示
  - [x] SubTask 10.3: 实现权限管理设置

## 阶段五：三层记忆架构

- [x] Task 11: 实现瞬时记忆
  - [x] SubTask 11.1: 实现滑动窗口上下文管理
  - [x] SubTask 11.2: 实现上下文压缩和摘要
  - [x] SubTask 11.3: 实现对话历史本地存储

- [x] Task 12: 实现工作记忆
  - [x] SubTask 12.1: 设计知识图谱数据结构
  - [x] SubTask 12.2: 实现重要信息自动提取
  - [x] SubTask 12.3: 实现向量数据库存储工作记忆
  - [x] SubTask 12.4: 实现分钟级记忆更新机制

- [x] Task 13: 实现长期记忆
  - [x] SubTask 13.1: 实现跨会话记忆索引
  - [x] SubTask 13.2: 实现记忆重要性评分算法
  - [x] SubTask 13.3: 实现长期记忆检索接口

- [x] Task 14: 开发记忆管理界面
  - [x] SubTask 14.1: 实现记忆片段列表展示
  - [x] SubTask 14.2: 实现记忆编辑和删除功能
  - [x] SubTask 14.3: 实现记忆搜索功能

## 阶段六：用户界面完善

- [x] Task 15: 开发主界面布局
  - [x] SubTask 15.1: 实现左侧面板（模型选择/文档管理）
  - [x] SubTask 15.2: 实现右侧对话区域
  - [x] SubTask 15.3: 实现响应式布局适配

- [x] Task 16: 开发对话界面
  - [x] SubTask 16.1: 实现消息列表组件
  - [x] SubTask 16.2: 实现流式响应显示
  - [x] SubTask 16.3: 实现 Markdown 渲染和代码高亮
  - [x] SubTask 16.4: 实现输入框和发送功能

- [x] Task 17: 实现主题和交互
  - [x] SubTask 17.1: 实现深色/浅色主题切换
  - [x] SubTask 17.2: 实现自定义颜色配置
  - [x] SubTask 17.3: 实现快捷键支持
  - [x] SubTask 17.4: 实现中英文语言切换

## 阶段七：测试与优化

- [x] Task 18: 功能测试
  - [x] SubTask 18.1: 编写模型接入层单元测试
  - [x] SubTask 18.2: 编写知识库功能测试
  - [x] SubTask 18.3: 编写动作执行引擎测试
  - [x] SubTask 18.4: 编写记忆系统测试

- [x] Task 19: 性能优化
  - [x] SubTask 19.1: 优化启动时间
  - [x] SubTask 19.2: 优化内存占用
  - [x] SubTask 19.3: 优化响应速度
  - [x] SubTask 19.4: 进行压力测试

- [x] Task 20: 打包与部署
  - [x] SubTask 20.1: 配置 GitHub Actions CI/CD
  - [x] SubTask 20.2: 实现 Windows 安装包打包
  - [x] SubTask 20.3: 实现 macOS 安装包打包
  - [x] SubTask 20.4: 实现 Linux 安装包打包

---

# Task Dependencies

- Task 2 依赖 Task 1（需要项目结构）
- Task 3-4 依赖 Task 2（需要数据库支持配置存储）
- Task 5-7 依赖 Task 2（需要数据库支持文档存储）
- Task 8-10 依赖 Task 1（需要基础架构）
- Task 11-14 依赖 Task 2（需要数据库支持记忆存储）
- Task 15-17 依赖 Task 1（需要前端框架）
- Task 18-19 依赖 Task 3-17（需要所有功能完成）
- Task 20 依赖 Task 18-19（需要测试通过）

# Parallelizable Work

以下任务可并行执行：
- Task 3-4（模型接入层）与 Task 5-7（知识库系统）
- Task 8-10（动作引擎）与 Task 11-14（记忆系统）
- Task 15-17（用户界面）可与后端任务并行开发
