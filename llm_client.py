import os
import json
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
        )
        self.model_pro = "deepseek-v4-pro"
        self.model_flash = "deepseek-v4-flash"
        self.total_tokens = 0

    async def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, model: str = None) -> str:
        response = await self.client.chat.completions.create(
            model=model or self.model_flash,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        self.total_tokens += response.usage.total_tokens
        return response.choices[0].message.content

    async def chat_json(self, system_prompt: str, user_prompt: str, model: str = None) -> dict:
        last_error = None
        for attempt in range(3):
            raw = await self.chat(system_prompt, user_prompt, temperature=0.3, model=model)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError as e:
                last_error = e
                if attempt < 2:
                    await asyncio.sleep(1)
                    system_prompt += "\n注意：上次返回的不是合法JSON，请严格只返回JSON格式数据，不要包含任何其他文字。"
        raise last_error

    async def chat_stream(self, system_prompt: str, user_prompt: str, on_chunk, temperature: float = 0.7, model: str = None):
        stream = await self.client.chat.completions.create(
            model=model or self.model_flash,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            stream=True,
        )
        full_text = ""
        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                full_text += delta
                if on_chunk:
                    await on_chunk(delta)
        return full_text

    async def chat_json_stream(self, system_prompt: str, user_prompt: str, on_chunk=None, model: str = None) -> dict:
        last_error = None
        for attempt in range(3):
            raw = await self.chat_stream(system_prompt, user_prompt, on_chunk, temperature=0.3, model=model)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError as e:
                last_error = e
                if attempt < 2:
                    await asyncio.sleep(1)
                    system_prompt += "\n注意：上次返回的不是合法JSON，请严格只返回JSON格式数据，不要包含任何其他文字。"
        raise last_error

    def get_token_count(self) -> int:
        return self.total_tokens

    def reset_tokens(self):
        self.total_tokens = 0
