"""
统一LLM客户端 - 支持多个免费LLM提供商
支持: Groq, DashScope, 智谱AI, SiliconFlow, DeepSeek
"""
import os
import json
import requests
from typing import Optional, Dict, Any, Iterator

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  openai 库未安装，流式输出将使用模拟方式")


class LLMClient:
    """统一LLM客户端"""
    
    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        初始化LLM客户端
        
        Args:
            provider: LLM提供商 (groq/dashscope/zhipu/siliconflow/deepseek)
            api_key: API Key（如果为None，从环境变量读取）
            model: 模型名称（如果为None，使用默认模型）
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "groq")
        self.api_key = api_key or self._get_api_key()
        self.model = model or self._get_model()
        
        if not self.api_key:
            print(f"⚠️  LLM API Key 未配置（提供商: {self.provider}）")
            print(f"   将使用文本拼接方式生成答案")
            print(f"   请在 .env 文件中配置 {self.provider.upper()}_API_KEY")
        else:
            print(f"✅ LLM 已配置: {self.provider} - {self.model}")
    
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
    
    def chat(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> Optional[str]:
        """
        调用LLM生成回答
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            max_tokens: 最大token数
            
        Returns:
            生成的回答，失败返回None
        """
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
    
    def chat_stream(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> Iterator[str]:
        """
        流式调用LLM生成回答
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            max_tokens: 最大token数
            
        Yields:
            生成的文本片段
        """
        if not self.api_key:
            return
        
        try:
            if self.provider == "dashscope":
                yield from self._call_dashscope_stream(prompt, system_prompt, max_tokens)
            elif self.provider == "groq":
                yield from self._call_groq_stream(prompt, system_prompt, max_tokens)
            else:
                # 其他提供商暂不支持流式，降级到普通调用
                result = self.chat(prompt, system_prompt, max_tokens)
                if result:
                    yield result
        except Exception as e:
            print(f"[ERROR] LLM流式调用失败: {e}")
            return
    
    def _call_groq(self, prompt: str, system_prompt: str, max_tokens: int) -> Optional[str]:
        """调用Groq API（超快！）"""
        url = "https://api.groq.com/openai/v1/chat/completions"
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
    
    def _call_groq_stream(self, prompt: str, system_prompt: str, max_tokens: int) -> Iterator[str]:
        """调用Groq API（流式）"""
        if OPENAI_AVAILABLE:
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                stream=True
            )
            
            for chunk in completion:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
        else:
            # 降级到非流式
            result = self._call_groq(prompt, system_prompt, max_tokens)
            if result:
                yield result
    
    def _call_dashscope(self, prompt: str, system_prompt: str, max_tokens: int) -> Optional[str]:
        """调用阿里云通义千问API（非流式）- 使用OpenAI兼容模式"""
        if OPENAI_AVAILABLE:
            try:
                client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
                
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                completion = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                
                return completion.choices[0].message.content
            except Exception as e:
                print(f"[ERROR] OpenAI SDK调用失败: {e}")
                # 降级到原生API
                pass
        
        # 降级到DashScope原生API
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
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
            "input": {
                "messages": messages
            },
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["output"]["text"]
    
    def _call_dashscope_stream(self, prompt: str, system_prompt: str, max_tokens: int) -> Iterator[str]:
        """调用阿里云通义千问API（流式）- 使用OpenAI兼容模式"""
        if OPENAI_AVAILABLE:
            try:
                client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
                
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                completion = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7,
                    stream=True,
                    stream_options={"include_usage": True}
                )
                
                for chunk in completion:
                    if chunk.choices:
                        content = chunk.choices[0].delta.content or ""
                        if content:
                            yield content
                return
            except Exception as e:
                print(f"[ERROR] OpenAI SDK流式调用失败: {e}")
                # 降级到原生API
        
        # 降级到DashScope原生SSE流式API
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-DashScope-SSE": "enable"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "input": {"messages": messages},
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "incremental_output": True
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, stream=True, timeout=60)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data:'):
                        try:
                            json_str = line[5:].strip()
                            if json_str:
                                chunk_data = json.loads(json_str)
                                if 'output' in chunk_data and 'text' in chunk_data['output']:
                                    text = chunk_data['output']['text']
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"[ERROR] DashScope原生API流式调用失败: {e}")
            result = self._call_dashscope(prompt, system_prompt, max_tokens)
            if result:
                yield result
    
    def _call_zhipu(self, prompt: str, system_prompt: str, max_tokens: int) -> Optional[str]:
        """调用智谱AI API"""
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
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
    
    def _call_siliconflow(self, prompt: str, system_prompt: str, max_tokens: int) -> Optional[str]:
        """调用硅基流动API"""
        url = "https://api.siliconflow.cn/v1/chat/completions"
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
    
    def _call_deepseek(self, prompt: str, system_prompt: str, max_tokens: int) -> Optional[str]:
        """调用DeepSeek API（原始方案）"""
        url = "https://api.deepseek.com/v1/chat/completions"
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
