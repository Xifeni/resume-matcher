from sentence_transformers import SentenceTransformer, util

class ResumeRanker:
    def __init__(self, model_name='intfloat/e5-large-v2'):
        self.device = 'cpu'
        self.model = SentenceTransformer(model_name, device=self.device)
        print(f"Модель эмбеддингов загружена на: {self.device}")

    def get_embeddings(self, text_list):
        processed_texts = [f"passage: {t}" for t in text_list]
        return self.model.encode(processed_texts, convert_to_tensor=True)

    def calculate_similarity(self, vacancy_text, resume_embeddings):
        query_text = f"query: {vacancy_text}"
        query_embedding = self.model.encode(query_text, convert_to_tensor=True)

        cosine_scores = util.cos_sim(query_embedding, resume_embeddings)[0]
        return cosine_scores.tolist()