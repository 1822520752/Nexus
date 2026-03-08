# 贡献指南

感谢您有兴趣为 Nexus 做出贡献！本文档将帮助您了解如何参与项目开发。

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发指南](#开发指南)
- [提交规范](#提交规范)
- [代码风格](#代码风格)
- [测试要求](#测试要求)
- [文档贡献](#文档贡献)

## 行为准则

### 我们的承诺

为了营造一个开放和友好的环境，我们承诺：

- 使用包容性语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

### 不可接受的行为

- 使用性化的语言或图像
- 侮辱性或贬损性评论
- 公开或私下的骚扰
- 未经许可发布他人的私人信息
- 其他在专业环境中可能被合理认为不适当的行为

## 如何贡献

### 报告 Bug

如果您发现了 Bug，请通过 [GitHub Issues](https://github.com/your-username/nexus/issues) 提交报告。

**Bug 报告应包含：**

1. **标题** - 简洁描述问题
2. **描述** - 详细说明发生了什么
3. **复现步骤** - 如何重现问题
4. **预期行为** - 您期望发生什么
5. **实际行为** - 实际发生了什么
6. **环境信息**：
   - 操作系统（Windows/macOS/Linux 及版本）
   - Nexus 版本
   - Node.js 版本
   - Python 版本
7. **截图** - 如果适用
8. **日志** - 相关的错误日志

### 建议新功能

我们欢迎新功能建议！请通过 [GitHub Issues](https://github.com/your-username/nexus/issues) 提交。

**功能建议应包含：**

1. **标题** - 简洁描述功能
2. **动机** - 为什么需要这个功能
3. **详细描述** - 功能应该如何工作
4. **替代方案** - 您考虑过的其他解决方案
5. **附加信息** - 截图、草图等

### 提交代码

1. **Fork 仓库**

```bash
# 在 GitHub 上 Fork 仓库
# 然后克隆到本地
git clone https://github.com/your-username/nexus.git
cd nexus
```

2. **创建分支**

```bash
# 创建并切换到新分支
git checkout -b feature/your-feature-name

# 或修复 Bug
git checkout -b fix/your-bug-fix
```

3. **进行更改**

- 编写代码
- 添加测试
- 更新文档

4. **提交更改**

```bash
git add .
git commit -m "feat: 添加新功能描述"
```

5. **推送到 GitHub**

```bash
git push origin feature/your-feature-name
```

6. **创建 Pull Request**

- 在 GitHub 上创建 Pull Request
- 填写 PR 模板
- 等待审核

## 开发指南

### 环境设置

```bash
# 安装前端依赖
npm install

# 安装后端依赖
cd backend
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 启动开发服务器
cd ..
npm run tauri dev
```

### 项目结构

```
nexus/
├── src/                    # 前端源码 (Vue 3)
│   ├── components/         # UI 组件
│   ├── stores/             # 状态管理 (Pinia)
│   ├── composables/        # 组合式函数
│   └── types/              # TypeScript 类型
├── backend/                # 后端源码 (FastAPI)
│   ├── app/
│   │   ├── api/            # API 端点
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── schemas/        # Pydantic 模式
│   └── tests/              # 测试文件
└── src-tauri/              # Tauri Rust 后端
```

### 分支命名规范

- `feature/xxx` - 新功能
- `fix/xxx` - Bug 修复
- `docs/xxx` - 文档更新
- `refactor/xxx` - 代码重构
- `test/xxx` - 测试相关
- `chore/xxx` - 其他杂项

## 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

### 提交消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| 类型       | 说明                   |
| ---------- | ---------------------- |
| `feat`     | 新功能                 |
| `fix`      | Bug 修复               |
| `docs`     | 文档更新               |
| `style`    | 代码格式（不影响功能） |
| `refactor` | 代码重构               |
| `perf`     | 性能优化               |
| `test`     | 添加测试               |
| `chore`    | 构建过程或辅助工具变动 |
| `revert`   | 回滚提交               |

### 示例

```bash
# 新功能
git commit -m "feat(chat): 添加消息撤回功能"

# Bug 修复
git commit -m "fix(memory): 修复记忆检索时的内存泄漏问题"

# 文档更新
git commit -m "docs: 更新安装指南"

# 代码重构
git commit -m "refactor(llm): 重构模型适配器接口"
```

## 代码风格

### 前端 (TypeScript/Vue)

- 使用 ESLint + Prettier 进行代码格式化
- 遵循 Vue 3 Composition API 风格
- 使用 TypeScript 类型注解
- 所有注释使用中文

```typescript
/**
 * 发送消息到 AI 模型
 * @param content 消息内容
 * @param conversationId 会话 ID
 * @returns AI 响应内容
 */
async function sendMessage(
  content: string,
  conversationId: string
): Promise<string> {
  // 实现...
}
```

### 后端 (Python)

- 遵循 PEP 8 规范
- 使用 Black 格式化代码
- 使用 isort 排序导入
- 所有注释使用中文

```python
async def send_message(content: str, conversation_id: str) -> str:
    """
    发送消息到 AI 模型

    Args:
        content: 消息内容
        conversation_id: 会话 ID

    Returns:
        AI 响应内容
    """
    # 实现...
```

### Rust

- 使用 rustfmt 格式化代码
- 使用 clippy 进行代码检查
- 所有注释使用中文

## 测试要求

### 运行测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
npm run test

# 测试覆盖率
pytest --cov=app tests/
```

### 测试规范

- 所有新功能必须包含单元测试
- Bug 修复应包含回归测试
- 测试覆盖率应保持在 80% 以上
- 使用描述性的测试名称

```python
# 测试命名示例
def test_send_message_with_valid_content_should_return_response():
    """测试发送有效消息应返回响应"""
    pass

def test_send_message_with_empty_content_should_raise_error():
    """测试发送空消息应抛出错误"""
    pass
```

## 文档贡献

### 文档类型

- **README.md** - 项目介绍和快速开始
- **docs/** - 详细文档
- **代码注释** - 函数和类说明
- **API 文档** - API 端点说明

### 文档规范

- 使用 Markdown 格式
- 中英文双语支持
- 包含代码示例
- 保持简洁明了

## 获取帮助

如果您有任何问题，可以：

1. 查看 [文档](docs/)
2. 搜索 [Issues](https://github.com/your-username/nexus/issues)
3. 创建新的 [Issue](https://github.com/your-username/nexus/issues/new)
4. 加入我们的社区讨论

## 许可证

通过贡献代码，您同意您的贡献将根据 [MIT License](LICENSE) 进行许可。

---

再次感谢您的贡献！🎉
