import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI
from langchain_ollama import ChatOllama
from langchain_openai.chat_models.base import ChatOpenAI


def get_model(provider: str | None = None, temperature: float = 0):
    if provider is None:
        from shared.run_policy import get_default_model_provider

        provider = get_default_model_provider()
    """Factory function להחזרת מודל LLM לפי ספק."""
    if provider == "groq":
        return ChatGroq(
            model_name="openai/gpt-oss-120b",
            temperature=temperature,
            max_tokens=4096,
        )

    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=temperature,
        )

    if provider == "deepseek":
        return ChatOpenAI(
            model="deepseek-chat",
            openai_api_base="https://api.deepseek.com/v1",
            openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
            max_tokens=2048,
            temperature=temperature,
            tiktoken_model_name="gpt-4o",
        )

    if provider == "ollama":
        return ChatOllama(
            model="llama3.2:3b",
            temperature=temperature,
            num_ctx=8192,
        )

    if provider == "mistral":
        return ChatMistralAI(
            model="codestral-latest",
            temperature=0,
        )

    if provider == "open_router":
        return ChatOpenAI(
            model="google/gemini-3-flash-preview",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0,
            tiktoken_model_name="gpt-4o",
        )

    if provider == "github":
        return ChatOpenAI(
            base_url="https://models.inference.ai.azure.com",
            model="gpt-4o",
        )

    raise ValueError(f"Provider {provider} is not supported.")
