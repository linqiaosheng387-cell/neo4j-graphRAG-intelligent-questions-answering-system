# 🚀 GraphRAG LLM 模型更换完全指南（小白版）

> 本文档教你如何在 GraphRAG 系统中更换大语言模型（LLM）。无论你是想换成其他云厂商的模型，还是用本地模型，都能按照这个指南一步步来。

---

## 📋 目录

1. [基础概念](#基础概念)
2. [快速方案：换已有的 5 个 LLM](#快速方案换已有的-5-个-llm)
3. [进阶方案：添加新的 LLM](#进阶方案添加新的-llm)
4. [常见场景示例](#常见场景示例)
5. [故障排查](#故障排查)

---

## 基础概念

### 什么是 LLM Provider（提供商）？

LLM Provider 就是提供大语言模型服务的公司或服务。你的系统目前支持 5 个：

| 提供商 | 说明 | 特点 |
|--------|------|------|
| **Groq** | 美国公司，提供免费 API | 速度超快，适合实时应用 |
| **DashScope（通义千问）** | 阿里云，国内 | 中文支持好，有免费额度 |
| **智谱 AI** | 国内，GLM 系列模型 | 中文理解能力强 |
| **SiliconFlow** | 国内，模型聚合平台 | 支持多种开源模型 |
| **DeepSeek** | 国内，深度求索 | 推理能力强，性价比高 |

### 系统怎么选择用哪个 LLM？

你的系统通过一个叫 **`.env` 文件**的配置文件来决定用哪个 LLM。

- `.env` 文件在你的服务器上，路径是：`/www/wwwroot/output/backend/.env`
- 里面有一行：`LLM_PROVIDER=groq`（或其他值）
- 系统启动时会读这个值，然后自动调用对应的 LLM

### 代码在哪里？

所有 LLM 相关的代码都在一个文件里：

```
/www/wwwroot/output/backend/llm_client.py
```

这个文件包含了 5 个 LLM 的实现，但运行时只会用其中一个（由 `.env` 决定）。

---

## 快速方案：换已有的 5 个 LLM

### 场景：我想从 Groq 换成 DeepSeek

**步骤 1：获取 API Key**

1. 访问 [DeepSeek 官网](https://platform.deepseek.com)
2. 注册账号，登录
3. 在"API 密钥"页面，点击"创建新密钥"
4. 复制这个密钥（类似：`sk-xxxxxxxxxxxxxxxx`）

**步骤 2：修改 `.env` 文件**

在宝塔面板上：

1. 打开"文件"→ 找到 `/www/wwwroot/output/backend/.env`
2. 用文本编辑器打开
3. 找到这几行：

```env
LLM_PROVIDER=groq
GROQ_API_KEY=xxx
GROQ_MODEL=llama-3.1-70b-versatile
```

改成：

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-你复制的密钥
DEEPSEEK_MODEL=deepseek-chat
```

4. 保存文件

**步骤 3：重启后端服务**

在宝塔面板上：

1. 找到你的 Python 项目（vue_backend）
2. 点"重启"按钮
3. 等待 10 秒左右

**步骤 4：验证是否成功**

1. 打开后台管理系统
2. 进入"问答管理"，提个问题
3. 如果能正常回答，说明切换成功了

---

## 进阶方案：添加新的 LLM

### 场景：我想用本地 vLLM、或者某个不在列表里的模型

这需要改代码。别怕，我会一步步教你。

### 第一步：确认你的 LLM 服务信息

首先你需要知道：

1. **API 地址**：你的 LLM 服务的 URL，比如：
   - 本地 vLLM：`http://127.0.0.1:8000/v1/chat/completions`
   - 自建网关：`https://your-server.com/api/chat`
   - 其他云厂商：他们会告诉你

2. **API Key**：用来认证的密钥（如果有的话）

3. **模型名称**：比如 `qwen2.5-7b`、`llama2` 等

### 第二步：打开代码文件

在宝塔面板或你的 IDE 里打开：

```
/www/wwwroot/output/backend/llm_client.py
```

### 第三步：找到这三个地方，逐个改

#### 改动 1：在 `_get_api_key()` 方法里加一行

**找到这段代码**（大约在第 41-51 行）：

```python
def _get_api_key(self) -> Optional[str]:
    """从环境变量获取API Key"""
    key_mapping = {
        "groq": "GROQ_API_KEY",
        "dashscope": "DASHSCOPE_API_KEY",
        "zhipu": "ZHIPU_API_KEY",
        "siliconflow": "SILICONFLOW_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY"
    }
    env_key = key_mapping.get(self.provider)
    return os.getenv(env_key) if env_key else None
```

**改成这样**（在 `"deepseek"` 后面加一行）：

```python
def _get_api_key(self) -> Optional[str]:
    """从环境变量获取API Key"""
    key_mapping = {
        "groq": "GROQ_API_KEY",
        "dashscope": "DASHSCOPE_API_KEY",
        "zhipu": "ZHIPU_API_KEY",
        "siliconflow": "SILICONFLOW_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "custom": "CUSTOM_API_KEY"  # ← 新增这一行
    }
    env_key = key_mapping.get(self.provider)
    return os.getenv(env_key) if env_key else None
```

#### 改动 2：在 `_get_model()` 方法里加一行

**找到这段代码**（大约在第 53-62 行）：

```python
def _get_model(self) -> str:
    """获取模型名称"""
    model_mapping = {
        "groq": os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
        "dashscope": os.getenv("DASHSCOPE_MODEL", "qwen-plus"),
        "zhipu": os.getenv("ZHIPU_MODEL", "glm-4-flash"),
        "siliconflow": os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
        "deepseek": os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    }
    return model_mapping.get(self.provider, "default")
```

**改成这样**（在 `"deepseek"` 后面加一行）：

```python
def _get_model(self) -> str:
    """获取模型名称"""
    model_mapping = {
        "groq": os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
        "dashscope": os.getenv("DASHSCOPE_MODEL", "qwen-plus"),
        "zhipu": os.getenv("ZHIPU_MODEL", "glm-4-flash"),
        "siliconflow": os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
        "deepseek": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "custom": os.getenv("CUSTOM_MODEL", "your-model-name")  # ← 新增这一行
    }
    return model_mapping.get(self.provider, "default")
```

#### 改动 3：在 `chat()` 方法里加一个分支

**找到这段代码**（大约在第 64-95 行）：

```python
def chat(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> Optional[str]:
    if not self.api_key:
        return None
    
    try:
        if self.provider == "groq":
            return self._call_groq(prompt, system_prompt, max_tokens)
        elif self.provider == "dashscope":
            return self._call_dashscope(prompt, system_prompt, max_tokens)
        elif self.provider == "zhipu":
            return self._call_zhipu(prompt, system_prompt, max_tokens)
        elif self.provider == "siliconflow":
            return self._call_siliconflow(prompt, system_prompt, max_tokens)
        elif self.provider == "deepseek":
            return self._call_deepseek(prompt, system_prompt, max_tokens)
        else:
            print(f"[ERROR] 不支持的LLM提供商: {self.provider}")
            return None
    except Exception as e:
        print(f"[ERROR] LLM调用失败: {e}")
        return None
```

**改成这样**（在 `deepseek` 后面加一个 `elif`）：

```python
def chat(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> Optional[str]:
    if not self.api_key:
        return None
    
    try:
        if self.provider == "groq":
            return self._call_groq(prompt, system_prompt, max_tokens)
        elif self.provider == "dashscope":
            return self._call_dashscope(prompt, system_prompt, max_tokens)
        elif self.provider == "zhipu":
            return self._call_zhipu(prompt, system_prompt, max_tokens)
        elif self.provider == "siliconflow":
            return self._call_siliconflow(prompt, system_prompt, max_tokens)
        elif self.provider == "deepseek":
            return self._call_deepseek(prompt, system_prompt, max_tokens)
        elif self.provider == "custom":  # ← 新增这个分支
            return self._call_custom(prompt, system_prompt, max_tokens)
        else:
            print(f"[ERROR] 不支持的LLM提供商: {self.provider}")
            return None
    except Exception as e:
        print(f"[ERROR] LLM调用失败: {e}")
        return None
```

#### 改动 4：在文件末尾加一个新方法

**在文件最后（第 392 行之后）加上这段代码**：

```python
    def _call_custom(self, prompt: str, system_prompt: str, max_tokens: int) -> Optional[str]:
        """调用自定义LLM API"""
        url = os.getenv("CUSTOM_API_URL", "http://localhost:8000/v1/chat/completions")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
```

### 第四步：修改 `.env` 文件

打开 `/www/wwwroot/output/backend/.env`，加上这几行：

```env
LLM_PROVIDER=custom
CUSTOM_API_URL=http://你的模型服务地址/v1/chat/completions
CUSTOM_API_KEY=你的 API Key（如果没有就写 none）
CUSTOM_MODEL=你的模型名称
```

### 第五步：重启后端服务

在宝塔面板上重启 Python 项目。

---

## 常见场景示例

### 场景 1：用本地 vLLM

你在本地或服务器上用 vLLM 启动了一个模型服务。

**第一步**：确保 vLLM 已启动

```bash
python -m vllm.entrypoints.openai.api_server --model qwen2.5-7b
```

**第二步**：修改 `.env`

```env
LLM_PROVIDER=custom
CUSTOM_API_URL=http://127.0.0.1:8000/v1/chat/completions
CUSTOM_API_KEY=none
CUSTOM_MODEL=qwen2.5-7b
```

**第三步**：重启后端

完事。

---

### 场景 2：用自建 OpenAI 兼容网关

你有一个自己搭建的 OpenAI 兼容网关（比如用 FastAPI 写的）。

**修改 `.env`**

```env
LLM_PROVIDER=custom
CUSTOM_API_URL=https://your-gateway.example.com/v1/chat/completions
CUSTOM_API_KEY=sk-your-secret-key
CUSTOM_MODEL=your-model-name
```

---

### 场景 3：用 Claude（Anthropic）

Claude 的 API 格式和 OpenAI 不一样，需要特殊处理。

**第一步**：获取 API Key

访问 [Anthropic 官网](https://console.anthropic.com)，获取 API Key。

**第二步**：修改 `llm_client.py`

把 `_call_custom()` 方法改成：

```python
def _call_custom(self, prompt: str, system_prompt: str, max_tokens: int) -> Optional[str]:
    """调用 Claude API"""
    import anthropic
    
    client = anthropic.Anthropic(api_key=self.api_key)
    
    message = client.messages.create(
        model=self.model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text
```

**第三步**：修改 `.env`

```env
LLM_PROVIDER=custom
CUSTOM_API_KEY=sk-ant-你的-key
CUSTOM_MODEL=claude-3-5-sonnet-20241022
```

**第四步**：安装 anthropic 库

在服务器上运行：

```bash
pip install anthropic
```

---

### 场景 4：用国内云厂商（比如讯飞星火）

讯飞星火也有 OpenAI 兼容的 API。

**修改 `.env`**

```env
LLM_PROVIDER=custom
CUSTOM_API_URL=https://api.xf-yun.com/v1/chat/completions
CUSTOM_API_KEY=你的-key
CUSTOM_MODEL=spark-3.5-max
```

---

## 故障排查

### 问题 1：改完后，后台显示"加载失败"或"请求超时"

**原因**：通常是 API Key 错了，或者 API 地址不对。

**排查步骤**：

1. 在服务器上查看后端日志：
   ```bash
   tail -f /www/wwwlogs/vue_backend.log
   ```
   看有没有错误信息。

2. 手动测试 API 是否可用：
   ```bash
   curl -X POST http://你的API地址 \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer 你的key" \
     -d '{"model":"你的模型","messages":[{"role":"user","content":"hello"}]}'
   ```

3. 确认 `.env` 里的 `CUSTOM_API_URL` 和 `CUSTOM_API_KEY` 是否正确。

### 问题 2：改完后，后端启动时打印"LLM API Key 未配置"

**原因**：`.env` 里没有对应的 API Key 环境变量。

**解决**：

1. 检查 `.env` 里是否有 `CUSTOM_API_KEY=` 这一行。
2. 如果没有，加上去。
3. 重启后端。

### 问题 3：改完代码后，后端启动报错

**原因**：代码有语法错误，或者缩进不对。

**解决**：

1. 检查你加的代码是否有拼写错误。
2. 检查缩进是否正确（Python 对缩进很敏感）。
3. 如果还是不行，把改动撤销，重新来一遍。

### 问题 4：API 调用成功，但回答质量很差

**原因**：可能是模型本身的问题，或者参数设置不对。

**可以尝试**：

1. 在 `_call_custom()` 里调整 `temperature` 参数（0-1，越小越稳定，越大越创意）。
2. 调整 `max_tokens` 参数（越大回答越长）。
3. 换一个更强的模型。

---

## 📞 快速参考表

| 想要做什么 | 需要改什么 |
|-----------|----------|
| 换成已有的 5 个 LLM 之一 | 只改 `.env` 文件 |
| 用本地 vLLM | 改 `llm_client.py` 的 4 个地方 + `.env` |
| 用自建网关 | 改 `llm_client.py` 的 4 个地方 + `.env` |
| 用 Claude / Gemini 等 | 改 `llm_client.py` 的 4 个地方 + 可能需要改 `_call_custom()` 的实现 + `.env` |

---

## 🎯 总结

- **简单情况**（换已有的 LLM）：只改 `.env`
- **复杂情况**（新 LLM）：改代码 + 改 `.env` + 重启
- **遇到问题**：查看日志，检查 API 是否可用，确认 Key 是否正确

祝你使用愉快！有问题随时问。

