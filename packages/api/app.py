import os
from typing import Any

from flasgger import Swagger
from flask import Flask, jsonify, request
from flask_cors import CORS

import db
from judge import llm_judge
from parser import (
    extract_text_from_file,
    extract_text_from_upload,
    extension_from_filename,
    save_upload_to_temp_path,
)
from ranker import ResumeRanker

app = Flask(__name__)
CORS(app)

ranker = ResumeRanker()


def run_match_pipeline(resume_text: str, vacancy_text: str) -> dict[str, Any]:
    resume_emb = ranker.get_embeddings([resume_text])
    semantic_score = ranker.calculate_similarity(vacancy_text, resume_emb)[0]
    semantic_score_100 = semantic_score * 100

    llm_result = llm_judge(vacancy_text, resume_text)
    llm_score = llm_result.get("score", 0)
    reasoning = llm_result.get("reasoning", "")

    final_score = (0.4 * semantic_score_100) + (0.6 * llm_score)

    return {
        "final_score": round(final_score, 2),
        "details": {
            "semantic_similarity": round(semantic_score_100, 2),
            "llm_judge_score": llm_score,
            "reasoning": reasoning,
        },
    }


def predict_and_persist(
    resume_text: str,
    vacancy_text: str,
    resume_id: int,
    vacancy_id: int,
) -> dict[str, Any]:
    out = run_match_pipeline(resume_text, vacancy_text)
    analysis_id = db.insert_analysis(
        resume_id,
        vacancy_id,
        out["final_score"],
        out["details"]["semantic_similarity"],
        out["details"]["llm_judge_score"],
        out["details"]["reasoning"] or "",
    )
    return {
        "final_score": out["final_score"],
        "details": out["details"],
        "analysis_id": analysis_id,
        "resume_id": resume_id,
        "vacancy_id": vacancy_id,
    }


@app.route("/resumes", methods=["POST"])
def create_resume():
    """
    Сохранить резюме в БД
    Извлекает текст из PDF, DOCX или DOC, сохраняет в SQLite, возвращает id для дальнейших /predict и /predict/batch.
    ---
    tags:
      - Резюме
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: Файл резюме (PDF, DOCX или DOC; для DOC в системе нужен antiword)
    responses:
      200:
        description: Запись создана
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
            original_filename:
              type: string
            created_at:
              type: string
      400:
        description: Нет файла, неподдерживаемый формат или ошибка извлечения текста
        schema:
          $ref: '#/definitions/Error'
    """
    if "file" not in request.files:
        return jsonify({"error": "Нужен файл в поле file (PDF, DOCX или DOC)"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Пустое имя файла"}), 400
    try:
        text = extract_text_from_upload(f)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    rid = db.insert_resume(f.filename, text)
    row = db.get_resume(rid)
    return jsonify(
        {
            "id": rid,
            "original_filename": row["original_filename"],
            "created_at": row["created_at"],
        }
    )


def _multipart_files_list() -> list:
    raw = request.files.getlist("files")
    if not raw:
        raw = request.files.getlist("files[]")
    return [f for f in raw if f is not None]


@app.route("/resumes/batch", methods=["POST"])
def create_resumes_batch():
    """
    Массовая загрузка резюме
    multipart/form-data: несколько файлов в поле **files** (HTML `input name="files" multiple`) или **files[]**.
    Порядок в **results** совпадает с порядком файлов в запросе. Форматы PDF, DOCX, DOC (как в POST /resumes).
    ---
    tags:
      - Резюме
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: files
        type: array
        items:
          type: file
        collectionFormat: multi
        required: true
        description: Несколько файлов резюме (повторяющееся поле files)
    responses:
      200:
        description: Итог по каждому файлу
        schema:
          type: object
          properties:
            total:
              type: integer
            saved:
              type: integer
              description: Число успешно сохранённых записей
            results:
              type: array
              items:
                type: object
                properties:
                  ok: {type: boolean}
                  id: {type: integer}
                  original_filename: {type: string}
                  created_at: {type: string}
                  error: {type: string}
      400:
        description: Ни одного файла не передано
        schema:
          $ref: '#/definitions/Error'
    """
    files = _multipart_files_list()
    if not files:
        return jsonify(
            {"error": "Нет файлов: передайте поле files с одним или несколькими файлами (multipart)"}
        ), 400

    results: list[dict[str, Any]] = []
    for f in files:
        if not f.filename:
            results.append(
                {
                    "ok": False,
                    "original_filename": None,
                    "error": "Пустое имя файла",
                }
            )
            continue
        try:
            text = extract_text_from_upload(f)
            rid = db.insert_resume(f.filename, text)
            row = db.get_resume(rid)
            results.append(
                {
                    "ok": True,
                    "id": rid,
                    "original_filename": row["original_filename"],
                    "created_at": row["created_at"],
                }
            )
        except ValueError as e:
            results.append(
                {"ok": False, "original_filename": f.filename, "error": str(e)}
            )
        except Exception as e:
            results.append(
                {"ok": False, "original_filename": f.filename, "error": str(e)}
            )

    saved = sum(1 for r in results if r.get("ok"))
    return jsonify({"results": results, "total": len(results), "saved": saved})


@app.route("/vacancies", methods=["POST"])
def create_vacancy():
    """
    Сохранить вакансию в БД
    Извлекает текст из PDF, DOCX или DOC, сохраняет в SQLite, возвращает id.
    ---
    tags:
      - Вакансии
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: Файл вакансии (PDF, DOCX или DOC)
    responses:
      200:
        description: Запись создана
        schema:
          type: object
          properties:
            id:
              type: integer
            original_filename:
              type: string
            created_at:
              type: string
      400:
        description: Ошибка валидации или извлечения текста
        schema:
          $ref: '#/definitions/Error'
    """
    if "file" not in request.files:
        return jsonify({"error": "Нужен файл в поле file (PDF, DOCX или DOC)"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Пустое имя файла"}), 400
    try:
        text = extract_text_from_upload(f)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    vid = db.insert_vacancy(f.filename, text)
    row = db.get_vacancy(vid)
    return jsonify(
        {
            "id": vid,
            "original_filename": row["original_filename"],
            "created_at": row["created_at"],
        }
    )


@app.route("/vacancies/batch", methods=["POST"])
def create_vacancies_batch():
    """
    Массовая загрузка вакансий
    Как POST /resumes/batch, но сохраняет в таблицу vacancies. Поле **files** (или **files[]**) — несколько файлов PDF/DOC/DOCX.
    ---
    tags:
      - Вакансии
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: files
        type: array
        items:
          type: file
        collectionFormat: multi
        required: true
        description: Несколько файлов вакансий
    responses:
      200:
        description: Итог по каждому файлу
        schema:
          type: object
          properties:
            total: {type: integer}
            saved: {type: integer}
            results:
              type: array
              items:
                type: object
                properties:
                  ok: {type: boolean}
                  id: {type: integer}
                  original_filename: {type: string}
                  created_at: {type: string}
                  error: {type: string}
      400:
        description: Нет файлов
        schema:
          $ref: '#/definitions/Error'
    """
    files = _multipart_files_list()
    if not files:
        return jsonify(
            {"error": "Нет файлов: передайте поле files с одним или несколькими файлами (multipart)"}
        ), 400

    results: list[dict[str, Any]] = []
    for f in files:
        if not f.filename:
            results.append(
                {
                    "ok": False,
                    "original_filename": None,
                    "error": "Пустое имя файла",
                }
            )
            continue
        try:
            text = extract_text_from_upload(f)
            vid = db.insert_vacancy(f.filename, text)
            row = db.get_vacancy(vid)
            results.append(
                {
                    "ok": True,
                    "id": vid,
                    "original_filename": row["original_filename"],
                    "created_at": row["created_at"],
                }
            )
        except ValueError as e:
            results.append(
                {"ok": False, "original_filename": f.filename, "error": str(e)}
            )
        except Exception as e:
            results.append(
                {"ok": False, "original_filename": f.filename, "error": str(e)}
            )

    saved = sum(1 for r in results if r.get("ok"))
    return jsonify({"results": results, "total": len(results), "saved": saved})


@app.route("/vacancies/<int:vacancy_id>/analyses", methods=["GET"])
def list_vacancy_analyses(vacancy_id: int):
    """
    Список анализов по вакансии
    Возвращает все сохранённые предикты для указанной вакансии (с именем файла резюме), от новых к старым.
    ---
    tags:
      - Анализы
    parameters:
      - in: path
        name: vacancy_id
        type: integer
        required: true
        description: Идентификатор вакансии в БД
    responses:
      200:
        description: Вакансия и массив анализов
        schema:
          type: object
          properties:
            vacancy_id:
              type: integer
            vacancy:
              type: object
              properties:
                id: {type: integer}
                original_filename: {type: string}
                created_at: {type: string}
            analyses:
              type: array
              items:
                type: object
                properties:
                  analysis_id: {type: integer}
                  resume_id: {type: integer}
                  resume_filename: {type: string}
                  final_score: {type: number}
                  details:
                    type: object
                    properties:
                      semantic_similarity: {type: number}
                      llm_judge_score: {type: number}
                      reasoning: {type: string}
                  created_at: {type: string}
      404:
        description: Вакансия не найдена
        schema:
          $ref: '#/definitions/Error'
    """
    v = db.get_vacancy(vacancy_id)
    if not v:
        return jsonify({"error": f"Вакансия id={vacancy_id} не найдена"}), 404

    rows = db.list_analyses_for_vacancy(vacancy_id)
    analyses = []
    for row in rows:
        analyses.append(
            {
                "analysis_id": row["analysis_id"],
                "resume_id": row["resume_id"],
                "resume_filename": row["resume_filename"],
                "final_score": row["final_score"],
                "details": {
                    "semantic_similarity": row["semantic_similarity"],
                    "llm_judge_score": row["llm_judge_score"],
                    "reasoning": row["reasoning"],
                },
                "created_at": row["created_at"],
            }
        )

    return jsonify(
        {
            "vacancy_id": vacancy_id,
            "vacancy": {
                "id": v["id"],
                "original_filename": v["original_filename"],
                "created_at": v["created_at"],
            },
            "analyses": analyses,
        }
    )


@app.route("/predict", methods=["POST"])
def predict():
    """
    Одиночный предикт (матч резюме ↔ вакансия)
    Два взаимоисключающих режима multipart/form-data:
      1) Поля **resume_id** и **vacancy_id** — тексты берутся из БД (заранее POST /resumes и POST /vacancies).
      2) Файлы **resume** и **vacancy** (PDF, DOCX или DOC каждый) — тексты извлекаются, в БД создаются новые записи резюме и вакансии, затем считается скор и пишется строка в analyses.
    Итог: семантика (e5) + LLM-судья, итоговый вес 0.4/0.6. Ответ всегда содержит analysis_id, resume_id, vacancy_id.
    ---
    tags:
      - Предикт
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: resume
        type: file
        required: false
        description: Резюме PDF/DOC/DOCX (режим загрузки файлов)
      - in: formData
        name: vacancy
        type: file
        required: false
        description: Вакансия PDF/DOC/DOCX (режим загрузки файлов)
      - in: formData
        name: resume_id
        type: integer
        required: false
        description: Id резюме в БД (режим по id)
      - in: formData
        name: vacancy_id
        type: integer
        required: false
        description: Id вакансии в БД (режим по id)
    responses:
      200:
        description: Успешный расчёт и сохранение анализа
        schema:
          type: object
          properties:
            final_score:
              type: number
              description: Сводный балл 0–100
            details:
              type: object
              properties:
                semantic_similarity: {type: number}
                llm_judge_score: {type: number}
                reasoning: {type: string}
            analysis_id: {type: integer}
            resume_id: {type: integer}
            vacancy_id: {type: integer}
      400:
        description: Не переданы ни файлы, ни пара id
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Резюме или вакансия по id не найдены
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Ошибка пайплайна (LLM, эмбеддинги и т.д.)
        schema:
          $ref: '#/definitions/Error'
    """
    resume_id = request.form.get("resume_id", type=int)
    vacancy_id = request.form.get("vacancy_id", type=int)

    resume_text: str | None = None
    vacancy_text: str | None = None
    rid: int | None = None
    vid: int | None = None

    if resume_id is not None and vacancy_id is not None:
        r = db.get_resume(resume_id)
        v = db.get_vacancy(vacancy_id)
        if not r:
            return jsonify({"error": f"Резюме id={resume_id} не найдено"}), 404
        if not v:
            return jsonify({"error": f"Вакансия id={vacancy_id} не найдена"}), 404
        resume_text = r["extracted_text"]
        vacancy_text = v["extracted_text"]
        rid, vid = resume_id, vacancy_id
    elif "resume" in request.files and "vacancy" in request.files:
        resume_file = request.files["resume"]
        vacancy_file = request.files["vacancy"]
        if not resume_file.filename or not vacancy_file.filename:
            return jsonify({"error": "Укажите оба файла (PDF, DOCX или DOC)"}), 400

        resume_path: str | None = None
        vacancy_path: str | None = None
        try:
            try:
                extension_from_filename(resume_file.filename)
                extension_from_filename(vacancy_file.filename)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
            resume_path = save_upload_to_temp_path(resume_file)
            vacancy_path = save_upload_to_temp_path(vacancy_file)
            resume_text = extract_text_from_file(resume_path)
            vacancy_text = extract_text_from_file(vacancy_path)
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        finally:
            for p in (resume_path, vacancy_path):
                if p and os.path.isfile(p):
                    os.remove(p)

        rid = db.insert_resume(resume_file.filename, resume_text)
        vid = db.insert_vacancy(vacancy_file.filename, vacancy_text)
    else:
        return jsonify(
            {
                "error": "Либо загрузите resume и vacancy (PDF/DOC/DOCX), либо передайте resume_id и vacancy_id"
            }
        ), 400

    assert resume_text is not None and vacancy_text is not None
    assert rid is not None and vid is not None

    try:
        body = predict_and_persist(resume_text, vacancy_text, rid, vid)
        return jsonify(body)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict/batch", methods=["POST"])
def predict_batch():
    """
    Массовый предикт для одной вакансии
    Принимает JSON: **vacancy_id** и массив **resume_ids**. Для каждого id резюме по очереди выполняется тот же пайплайн, что и в /predict, результат сохраняется в analyses. Отсутствующее резюме или ошибка по одному кандидату не останавливает обработку остальных — в results приходит ok true/false по каждому resume_id.
    ---
    tags:
      - Предикт
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - vacancy_id
            - resume_ids
          properties:
            vacancy_id:
              type: integer
              description: Id вакансии в БД
            resume_ids:
              type: array
              items:
                type: integer
              description: Список id резюме в порядке обработки
    responses:
      200:
        description: Итог по каждому резюме (успех с полями предикта или ошибка)
        schema:
          type: object
          properties:
            vacancy_id:
              type: integer
            results:
              type: array
              items:
                type: object
                properties:
                  resume_id: {type: integer}
                  ok: {type: boolean}
                  error: {type: string}
                  final_score: {type: number}
                  details: {type: object}
                  analysis_id: {type: integer}
                  vacancy_id: {type: integer}
      400:
        description: Невалидный JSON или поля
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Вакансия не найдена
        schema:
          $ref: '#/definitions/Error'
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Ожидается JSON с полями vacancy_id и resume_ids"}), 400

    vacancy_id = data.get("vacancy_id")
    resume_ids = data.get("resume_ids")

    if vacancy_id is None or resume_ids is None:
        return jsonify({"error": "Нужны поля vacancy_id и resume_ids (массив)"}), 400

    try:
        vacancy_id = int(vacancy_id)
    except (TypeError, ValueError):
        return jsonify({"error": "vacancy_id должен быть целым числом"}), 400

    if not isinstance(resume_ids, list) or len(resume_ids) == 0:
        return jsonify({"error": "resume_ids должен быть непустым массивом id резюме"}), 400

    parsed_resume_ids: list[int] = []
    for i, raw in enumerate(resume_ids):
        try:
            parsed_resume_ids.append(int(raw))
        except (TypeError, ValueError):
            return jsonify({"error": f"resume_ids[{i}] не целое число: {raw!r}"}), 400

    v = db.get_vacancy(vacancy_id)
    if not v:
        return jsonify({"error": f"Вакансия id={vacancy_id} не найдена"}), 404

    vacancy_text = v["extracted_text"]
    results: list[dict[str, Any]] = []

    for rid in parsed_resume_ids:
        r = db.get_resume(rid)
        if not r:
            results.append(
                {
                    "resume_id": rid,
                    "ok": False,
                    "error": f"Резюме id={rid} не найдено",
                }
            )
            continue
        try:
            body = predict_and_persist(
                r["extracted_text"], vacancy_text, rid, vacancy_id
            )
            results.append({"resume_id": rid, "ok": True, **body})
        except Exception as e:
            results.append({"resume_id": rid, "ok": False, "error": str(e)})

    return jsonify({"vacancy_id": vacancy_id, "results": results})


@app.route("/health", methods=["GET"])
def health():
    """
    Проверка живости сервиса
    ---
    tags:
      - Служебное
    responses:
      200:
        description: Сервис отвечает
        schema:
          type: object
          properties:
            status:
              type: string
              example: ok
    """
    return jsonify({"status": "ok"})

@app.route("/resumes/<int:resume_id>", methods=["DELETE"])
def delete_resume_endpoint(resume_id: int):
    """
    Удалить одно резюме по ID
    ---
    tags:
      - Резюме
    """
    try:
        db.delete_resume(resume_id)
        return jsonify({"ok": True, "message": "Резюме удалено"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/resumes", methods=["DELETE"])
def delete_all_resumes_endpoint():
    """
    Удалить все резюме
    ---
    tags:
      - Резюме
    """
    try:
        db.delete_all_resumes()
        return jsonify({"ok": True, "message": "Все резюме удалены"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/vacancies/<int:vacancy_id>", methods=["DELETE"])
def delete_vacancy_endpoint(vacancy_id: int):
    """
    Удалить одну вакансию по ID
    ---
    tags:
      - Вакансии
    """
    try:
        db.delete_vacancy(vacancy_id)
        return jsonify({"ok": True, "message": "Вакансия удалена"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/vacancies", methods=["DELETE"])
def delete_all_vacancies_endpoint():
    """
    Удалить все вакансии
    ---
    tags:
      - Вакансии
    """
    try:
        db.delete_all_vacancies()
        return jsonify({"ok": True, "message": "Все вакансии удалены"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Resume Matcher API",
        "description": (
            "API сопоставления резюме с вакансией: извлечение текста из PDF, DOCX (python-docx) "
            "и DOC (утилита antiword в образе), семантика (sentence-transformers e5), "
            "оценка LLM (vLLM), сохранение в SQLite. Документация: /apidocs/, спецификация: /apispec.json"
        ),
        "version": "1.0.0",
    },
    "basePath": "/",
    "schemes": ["http", "https"],
    "definitions": {
        "Error": {
            "type": "object",
            "properties": {"error": {"type": "string"}},
        }
    },
    "tags": [
        {
            "name": "Резюме",
            "description": "Одиночная и массовая загрузка резюме (PDF, DOCX, DOC)",
        },
        {
            "name": "Вакансии",
            "description": "Одиночная и массовая загрузка вакансий (PDF, DOCX, DOC)",
        },
        {"name": "Предикт", "description": "Одиночный и пакетный матчинг"},
        {"name": "Анализы", "description": "Чтение сохранённых результатов"},
        {"name": "Служебное", "description": "Health и документация"},
    ],
}

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}

Swagger(app, template=SWAGGER_TEMPLATE, config=SWAGGER_CONFIG)

db.init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
