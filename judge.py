import requests
import json
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def llm_judge(vacancy_description, resume_text):
    prompt = f"""
    Оцени соответствие кандидата вакансии по шкале от 0 до 100.
    Вакансия: {vacancy_description[:1000]}
    Резюме: {resume_text[:2000]}

    Ответь строго в формате JSON: {{"score": число, "reasoning": "краткое обоснование"}}
    """

    payload = {
        "model": "llama-2-7b",
        "messages": [
            {"role": "system", "content": "You are a professional HR recruiter."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 256
    }

    try:
        base_url = os.getenv("VLLM_URL", "http://localhost:8000/v1")
        model_url = f"{base_url}/chat/completions"

        logger.info(f"Получен запрос на анализ. ссылка: {model_url}, payload:{payload}")

        response = requests.post(model_url, json=payload, timeout=60)
        result = response.json()

        content = result['choices'][0]['message']['content']
        return json.loads(content)
    except Exception as e:
        logger.error(f"Ошибка при обращении к LLM-судье: {e}")
        return {"score": 0, "reasoning": f"Ошибка обработки {e}"}