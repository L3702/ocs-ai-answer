# OCS 本地 AI 答题服务

用大模型给 OCS 自动答题功能提供"虚拟题库接口"，把 OCS 的 `AnswererWrapper` 请求转发到你配置的大模型 API。

## 文件

| 文件 | 作用 |
|------|------|
| `server.py` | Flask 服务端，接收 OCS 的答题请求 |
| `config.json` | 模型/端口/API Key 配置 |
| `ocs_config.json` | 复制粘贴到 OCS 的题库配置 JSON |
| `启动.bat` | 双击启动（Windows） |

## 使用步骤

1. **编辑 `config.json`**
   - 把 `apiKey` 填成你的模型 API Key（默认模板是 DeepSeek，也可改成 OpenAI / 通义 / 智谱等兼容 OpenAI 协议的任意服务）
   - 按需修改 `model`、`apiBase`、`port` 等

2. **启动服务**
   - 双击 `启动.bat`，或在命令行 `cd` 到本目录后 `python server.py`

3. **导入 OCS**
   - 打开 OCS → 脚本设置 → 题库配置
   - 导入 `ocs_config.json` 的内容
   - 保存后即可在答题时使用

## 协议说明

OCS 用 `AnswererWrapper` 定义的 HTTP 约定：

- **请求**：POST 到 `/api/answer`，携带 `${type}` `${title}` `${options}` 三个占位符对应的字段
- **响应**：JSON `{ code: 1, question, answer }`
- **Handler**：`res.code === 1 ? [undefined, res.answer] : undefined`

服务兼容 JSON body 和 form-urlencoded 两种编码，以及任意兼容 OpenAI Chat Completions 的 API。

## 支持的模型

任何兼容 `POST {base}/chat/completions` 的服务都可以：

- DeepSeek：`apiBase = https://api.deepseek.com/v1`
- OpenAI：`apiBase = https://api.openai.com/v1`
- 通义千问：`apiBase = https://dashscope.aliyuncs.com/compatible-mode/v1`
- 智谱 GLM：`apiBase = https://open.bigmodel.cn/api/paas/v4`
- 本地 Ollama：`apiBase = http://localhost:11434/v1`
