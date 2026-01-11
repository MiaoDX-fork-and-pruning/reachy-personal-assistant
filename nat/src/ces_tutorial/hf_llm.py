"""HuggingFace LLM backend for NAT using InferenceClient.

This module provides a HuggingFace Inference API integration for the
NeMo Agent Toolkit, allowing use of Qwen and other HF models instead
of NVIDIA NIM models.
"""

import os
from typing import Any, Iterator, List, Optional

from pydantic import Field
from huggingface_hub import InferenceClient
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from nat.data_models.llm import LLMBaseConfig
from nat.builder.register_llm import register_llm
from nat.builder.framework_enum import LLMFrameworkEnum


class HuggingFaceLLMConfig(LLMBaseConfig, name="huggingface"):
    """Configuration for HuggingFace Inference API."""

    model_name: str = Field(description="HuggingFace model ID (e.g., Qwen/Qwen2.5-7B-Instruct)")
    temperature: float = Field(default=0.0, description="Sampling temperature (0=deterministic)")
    max_tokens: int = Field(default=1024, description="Maximum tokens to generate")
    top_p: float = Field(default=1.0, description="Nucleus sampling threshold")


class HuggingFaceChatModel(BaseChatModel):
    """LangChain-compatible wrapper for HuggingFace InferenceClient.

    This class wraps the HuggingFace InferenceClient to provide a
    LangChain-compatible interface for use with NAT's routing system.
    """

    client: Any  # InferenceClient
    model_name: str
    temperature: float = 0.0
    max_tokens: int = 1024
    top_p: float = 1.0

    class Config:
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return "huggingface"

    @property
    def _identifying_params(self) -> dict:
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def _convert_messages_to_openai_format(self, messages: List[BaseMessage]) -> List[dict]:
        """Convert LangChain messages to OpenAI-compatible format."""
        openai_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                openai_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                # Handle multimodal content (text + images)
                content = msg.content
                if isinstance(content, list):
                    # Already in multimodal format
                    openai_messages.append({"role": "user", "content": content})
                else:
                    openai_messages.append({"role": "user", "content": content})
            elif isinstance(msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": msg.content})
            else:
                # Fallback for other message types
                openai_messages.append({"role": "user", "content": str(msg.content)})
        return openai_messages

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a chat completion using HuggingFace Inference API."""
        openai_messages = self._convert_messages_to_openai_format(messages)

        # Build request parameters
        params = {
            "model": self.model_name,
            "messages": openai_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

        if stop:
            params["stop"] = stop

        # Merge any additional kwargs
        params.update(kwargs)

        # Call HuggingFace Inference API
        response = self.client.chat.completions.create(**params)

        # Extract response content
        content = response.choices[0].message.content
        message = AIMessage(content=content)

        # Build generation with usage info if available
        generation_info = {}
        if hasattr(response, "usage") and response.usage:
            generation_info["usage"] = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return ChatResult(
            generations=[ChatGeneration(message=message, generation_info=generation_info)]
        )

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async version of generate - currently uses sync implementation."""
        # HuggingFace InferenceClient doesn't have native async for chat completions
        # so we use the sync version. For true async, consider AsyncInferenceClient.
        return self._generate(messages, stop, run_manager, **kwargs)


@register_llm(config_type=HuggingFaceLLMConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def huggingface_llm_fn(config: HuggingFaceLLMConfig):
    """Create and yield a HuggingFace LLM instance.

    This function is registered with NAT and creates a LangChain-compatible
    LLM that uses HuggingFace Inference API for completions.
    """
    # Get API key from environment
    api_key = os.getenv("HF_API_KEY")
    if not api_key:
        raise ValueError("HF_API_KEY environment variable is required for HuggingFace LLM")

    # Create InferenceClient
    client = InferenceClient(token=api_key)

    # Create LangChain-compatible chat model
    llm = HuggingFaceChatModel(
        client=client,
        model_name=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        top_p=config.top_p,
    )

    yield llm
