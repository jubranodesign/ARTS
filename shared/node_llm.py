import logging

from shared.llm_factory import get_model

logger = logging.getLogger(__name__)


def setup_node_llm(config, tools=None):
    """מחלץ provider מה-config, מאתחל LLM ומצמיד כלים אם יש."""
    configurable = config.get("configurable", {})
    provider = configurable.get("model_provider", "groq")
    logger.debug("setup_node_llm provider: %s", provider)

    llm = get_model(provider)

    if tools:
        return llm.bind_tools(tools)

    return llm
