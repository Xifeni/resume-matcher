# Resume Matcher

Пояснительная записка в `Пояснительная записка.md`

Монорепозиторий: **Vue 3** (фронт) и **Flask** (API) для оценки соответствия резюме вакансии. Скоринг комбинирует семантическое сходство (**sentence-transformers**, e5) и оценку **LLM** (OpenAI-совместимый endpoint, например vLLM). Результаты и загруженные тексты можно хранить в **SQLite**.

## Документация API (Swagger)

После запуска бэкенда откройте в браузере:

- **Swagger UI:** [http://localhost:8080/apidocs/](http://localhost:8080/apidocs/) — описание всех методов, схемы запросов/ответов, «Try it out».
- **OpenAPI (JSON):** [http://localhost:5001/apispec.json](http://localhost:5001/apispec.json) — сырая спецификация Swagger 2.0.

В Docker при пробросе порта `5001` используйте тот же хост и порт, что и для API.

## Структура проекта

| Путь | Назначение |
|------|------------|
| `packages/api` | Flask-приложение: парсинг PDF/DOC/DOCX, эмбеддинги, вызов LLM, SQLite, Flasgger |
| `packages/web` | SPA на Vue 3 + Vite + Element Plus |
| `docker-compose.yml` | GPU: vLLM + API + фронт (nginx) |
| `docker-compose.mac.yml` | API + фронт; LLM задаётся через `VLLM_URL` |

## Требования

- **Python 3.10+** (для API), **Node.js 20+** (для фронта).
- Для **`.doc`** на машине с API нужна утилита **antiword** (в Docker-образах API она уже ставится). **`.docx`** обрабатывается через `python-docx`.
- Полный стек с локальным LLM: **NVIDIA GPU** и образ с CUDA (см. `docker-compose.yml`).

## Переменные окружения (API)

| Переменная | Описание |
|------------|----------|
| `VLLM_URL` | Базовый URL OpenAI-совместимого API, без завершающего слэша (пример: `http://localhost:8000/v1`). В Docker для сервиса `app` обычно `http://vllm:8000/v1`. |
| `SQLITE_PATH` | Путь к файлу SQLite (по умолчанию `packages/api/data/resume_matcher.db`). В Docker: `/app/data/resume_matcher.db` + том для персистентности. |

## Запуск в Docker

**Linux с GPU** (vLLM + API + фронт):

```bash
docker compose up --build
```

- API: порт **5001**
- vLLM: **8000**
- Фронт: **8080** → nginx, API в браузере настраивается через `VITE_API_URL` (в compose: `http://localhost:5001`)

**macOS / без GPU** (только API и фронт; LLM снаружи):

```bash
export VLLM_URL=http://127.0.0.1:8000/v1  
docker compose -f docker-compose.mac.yml up --build
```

## Локальная разработка

**API** (из каталога `packages/api`):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export VLLM_URL=http://127.0.0.1:8000/v1 
python app.py
```

API слушает **5001**. Swagger: **http://localhost:5001/apidocs/**.

**Фронт** (из корня репозитория):

```bash
npm install
npm run dev:web
```

Либо `cd packages/web && npm run dev`. Укажите `VITE_API_URL` в `.env` фронта, если API не на том же origin.

## Кратко об API

- `POST /resumes`, `POST /resumes/batch` — сохранение резюме (файлы PDF / DOC / DOCX).
- `POST /vacancies`, `POST /vacancies/batch` — сохранение вакансий.
- `POST /predict` — одиночный матч (файлы или `resume_id` + `vacancy_id` из БД).
- `POST /predict/batch` — массовый предикт по списку `resume_ids` и одной `vacancy_id` (JSON).
- `GET /vacancies/<id>/analyses` — сохранённые анализы по вакансии.
- `GET /health` — проверка живости.

Подробности, коды ответов и примеры — в **Swagger UI** по ссылке выше.

#### Лицензия

См. файл `LICENSE` в корне репозитория.
