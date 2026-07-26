import logging

from langgraph.graph.state import RunnableConfig

from graph.state import AgentState
from ml_predictor.utils import predict_risk
from shared.run_policy import get_risk_threshold
from utils.log_format import log_tail
from shared.paths import extract_python_path
from utils.repo_files import read_repo_text

logger = logging.getLogger(__name__)


def wait_for_task(state: AgentState, config: RunnableConfig):
    repo_path = config["configurable"]["repo_path"]
    user_task = state.get("user_input")

    if not user_task or not str(user_task).strip():
        logger.warning("wait_for_task: user_input is missing or empty")
    else:
        logger.debug(
            "wait_for_task user_task preview: %s",
            log_tail(str(user_task), max_chars=300, max_lines=5),
        )

    target_file = extract_python_path(user_task or "")
    logger.debug("wait_for_task repo_path=%s target_file=%r", repo_path, target_file)

    code_content = read_repo_text(repo_path, target_file)
    logger.debug("wait_for_task code_len=%s", len(code_content or ""))

    risk, top_reasons = predict_risk(code_content)

    reasons_for_state = []
    for feat, data in top_reasons:
        reasons_for_state.append(
            {
                "feature": feat,
                "impact": float(data["importance"]),
                "value": float(data["value"]),
            }
        )

    threshold = get_risk_threshold()
    logger.info(
        "wait_for_task risk_score=%.4f target_file=%r (RISK_THRESHOLD=%.2f)",
        float(risk),
        target_file,
        threshold,
    )
    logger.debug("wait_for_task top_reasons=%s", reasons_for_state)

    return {
        "risk_score": float(risk),
        "risk_reasons": reasons_for_state,
    }
