# Resume Matcher

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
export VLLM_URL=http://127.0.0.1:8000/v1   # ваш запущенный vLLM или другой совместимый сервис
docker compose -f docker-compose.mac.yml up --build
```

## Локальная разработка

**API** (из каталога `packages/api`):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export VLLM_URL=http://127.0.0.1:8000/v1   # при необходимости
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


## Финальная оценка кандидата (калибратор на основе датасета ручной разметки)

Изначальная простая линейная комбинация семантического сходства и LLM-оценки:
final_score = 0.4 × COS_score + 0.6 × LLM_score
приводила к систематическому завышению итоговых оценок, особенно в граничных случаях, когда один из признаков был высоким, а другой — низким.

Решение:

Для устранения перекоса была обучена ML-модель-калибратор на пространстве признаков [COS_score, LLM_score] с использованием ручной разметки (150+ пар "резюме-вакансия").


Введён дополнительный признак llm_cos_interaction=(COS_score*LLM_score) создающий не линейную связь, умнешает стандартное отклонение метрики на кроссвалидации.



**Статистически данные датасета**
```
        list_score_llm	list_score_cos	list_score_manual	llm_cos_interaction
count	150.000000	    150.000000	    150.000000	        150.000000
mean	72.726667	    0.840847	    48.520000	        61.289187
std	    15.710851	    0.024402	    29.589296	        13.915949
min	    20.000000	    0.796700	    0.000000	        16.100000
max	    95.000000	    0.902400	    100.000000	        85.386000

Модель калибратора 

Опробованы 10 вариантов, различных алгоритмов 

СРАВНЕНИЕ ВСЕХ МОДЕЛЕЙ (10 вариантов) по результатам кросс валидации :



LinearRegression     | R² = 0.5872
Ridge                | R² = 0.5873
Lasso                | R² = 0.5872
ElasticNet           | R² = 0.5871
BayesianRidge        | R² = 0.5869
HuberRegressor       | R² = 0.5844
SGDRegressor         | R² = 0.6454
RandomForest         | R² = 0.6181
SVR                  | R² = 0.5773
LinearSVR            | R² = 0.5880


 РЕЙТИНГ МОДЕЛЕЙ ПО КАЧЕСТВУ:

1. SGDRegressor         | R² = 0.6454
2. RandomForest         | R² = 0.6181
3. LinearSVR            | R² = 0.5880
4. Ridge                | R² = 0.5873
5. Lasso                | R² = 0.5872
6. LinearRegression     | R² = 0.5872
7. ElasticNet           | R² = 0.5871
8. BayesianRidge        | R² = 0.5869
9. HuberRegressor       | R² = 0.5844
10. SVR                 | R² = 0.5773


```

В качестве калибратора выбран SGDRegressor. 1. SGDRegressor   R² = 0.6454

- `Resumematcher.ipynb` файл содержит пайплайн обучения модели, основные метрики вывод, данные ручной разметки, создания бинарного файла модели калибратора.

- `packages/api/custom_transformers.py` специализированный  класс для расширения признакового пространства данных. Необходим для работы бинарного предстваления модели SGDregressor.
 
- `packages/api/model_best_resume_matcher.pkl` бинарник  обученный pipline для калибровки finalscore . Включает в себя изменение признакового пространства, масштабирование и саму модель SGDRegressor.




**Дальнейшие улучшения:**
- Накопление большего объёма размеченных данных (цель: 1000+ пар)
- Эксперименты с нелинейными моделями 
- Расширение признакового пространства
- Внедрение онлайн-дообучения по мере поступления новых экспертных оценок





## Лицензия

См. файл `LICENSE` в корне репозитория.
