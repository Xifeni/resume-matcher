from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from parser import extract_text_from_pdf
from ranker import ResumeRanker
from judge import llm_judge

app = Flask(__name__)
CORS(app)

ranker = ResumeRanker()

@app.route('/predict', methods=['POST'])
def predict():
    if 'resume' not in request.files or 'vacancy' not in request.files:
        return jsonify({"error": "Необходимо загрузить оба файла: resume и vacancy (PDF)"}), 400

    resume_file = request.files['resume']
    vacancy_file = request.files['vacancy']

    resume_path = "temp_resume.pdf"
    vacancy_path = "temp_vacancy.pdf"
    resume_file.save(resume_path)
    vacancy_file.save(vacancy_path)

    try:
        resume_text = extract_text_from_pdf(resume_path)
        vacancy_text = extract_text_from_pdf(vacancy_path)

        resume_emb = ranker.get_embeddings([resume_text])
        semantic_score = ranker.calculate_similarity(vacancy_text, resume_emb)[0]
        semantic_score_100 = semantic_score * 100

        llm_result = llm_judge(vacancy_text, resume_text)
        llm_score = llm_result.get('score', 0)

        final_score = (0.4 * semantic_score_100) + (0.6 * llm_score)

        return jsonify({
            "final_score": round(final_score, 2),
            "details": {
                "semantic_similarity": round(semantic_score_100, 2),
                "llm_judge_score": llm_score,
                "reasoning": llm_result.get('reasoning', "")
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(resume_path): os.remove(resume_path)
        if os.path.exists(vacancy_path): os.remove(vacancy_path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)