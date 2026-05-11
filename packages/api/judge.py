import json
import logging
import os
import re
from typing import Any

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _extract_json_object(text: str) -> dict[str, Any]:
    """Разбирает JSON из ответа модели: чистая строка, markdown ```json ... ``` или текст с объектом внутри."""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("пустой content от модели")

    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
    if fenced:
        raw = fenced.group(1).strip()

    try:
        out = json.loads(raw)
        if isinstance(out, dict):
            return out
    except json.JSONDecodeError:
        pass

    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end > start:
        return json.loads(raw[start : end + 1])

    raise ValueError(f"не удалось извлечь JSON из ответа: {raw[:400]!r}")


def llm_judge(vacancy_description: str, resume_text: str) -> dict[str, Any]:
    prompt = f"""
    Оцени соответствие кандидата вакансии по шкале от 0 до 100.
    Вакансия: {vacancy_description[:1000]}
    Резюме: {resume_text[:2000]}

    Ответь строго одним JSON-объектом без пояснений до и после: {{"score": число, "reasoning": "краткое обоснование"}}
    """

    payload = {
        "model": "qwen2.5",
        "messages": [
            {"role": "system", "content": "You are a professional HR recruiter."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 512,
    }

    try:
        base_url = os.getenv("VLLM_URL", "http://localhost:8000/v1").rstrip("/")
        model_url = f"{base_url}/chat/completions"

        logger.info("Запрос к LLM: %s", model_url)

        response = requests.post(model_url, json=payload, timeout=120)
        response.raise_for_status()

        try:
            result = response.json()
        except json.JSONDecodeError:
            logger.error("Тело ответа не JSON: %r", response.text[:800])
            raise

        choices = result.get("choices") or []
        if not choices:
            logger.error("Нет choices в ответе: %s", result)
            raise ValueError("пустой choices")

        message = choices[0].get("message") or {}
        content = message.get("content")

        if content is None and message.get("tool_calls"):
            logger.error("Модель вернула tool_calls вместо текста: %s", message)
            raise ValueError("unexpected tool_calls")

        if isinstance(content, list):
            # multimodal: [{"type": "text", "text": "..."}]
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text") or "")
            content = "".join(parts)

        if not (isinstance(content, str) and content.strip()):
            logger.error(
                "Пустой или нестроковый content. message=%s finish_reason=%s",
                message,
                choices[0].get("finish_reason"),
            )
            raise ValueError("пустой content от модели")

        parsed = _extract_json_object(content)
        score = parsed.get("score", 0)
        reasoning = parsed.get("reasoning", "")
        return {"score": score, "reasoning": reasoning}

    except Exception as e:
        logger.exception("Ошибка при обращении к LLM-судье: %s", e)
        return {"score": 0, "reasoning": f"Ошибка обработки: {e}"}
