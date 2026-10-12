import json
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.config import settings

def bounded(value, low, high):
    return max(low, min(high, float(value)))

def baseline_evaluation(answer, reference, rubric, max_marks):
    answer = answer.strip()
    if not answer:
        return {"method":"baseline_heuristic", "similarity":0.0, "recommended_marks":0.0,
                "summary":"No answer text was available.", "criteria":[], "evidence":[],
                "limitations":["Heuristic scoring is not validated; teacher review is mandatory."]}
    try:
        matrix = TfidfVectorizer(stop_words="english").fit_transform([answer, reference])
        similarity = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    except ValueError:
        similarity = 0.0
    results, earned_total, rubric_total = [], 0.0, 0.0
    lower = answer.lower()
    for item in rubric or []:
        keys = [str(k).lower().strip() for k in item.get("keywords", []) if str(k).strip()]
        marks = float(item.get("marks", 0))
        hits = [k for k in keys if k in lower]
        coverage = len(hits) / len(keys) if keys else similarity
        earned = marks * coverage
        earned_total += earned
        rubric_total += marks
        results.append({"criterion":item.get("criterion","Rubric criterion"), "max_marks":marks,
                        "suggested_marks":round(earned,2), "matched_keywords":hits,
                        "missing_keywords":[k for k in keys if k not in hits],
                        "evidence":"Matched terms: " + (", ".join(hits) if hits else "No rubric keywords matched.")})
    if rubric_total:
        score = 0.8 * (earned_total / rubric_total) * max_marks + 0.2 * similarity * max_marks
    else:
        score = similarity * max_marks
    evidence = [{"type":"rubric_keyword_match","criterion":r["criterion"],"text":", ".join(r["matched_keywords"])}
                for r in results if r["matched_keywords"]]
    if not evidence:
        evidence = [{"type":"notice","text":"No rubric keyword matches; manually inspect this answer."}]
    return {"method":"baseline_heuristic", "similarity":round(similarity,4),
            "recommended_marks":round(bounded(score,0,max_marks),2),
            "summary":"Draft recommendation from lexical similarity and rubric keyword coverage.",
            "criteria":results, "evidence":evidence,
            "limitations":["TF-IDF is lexical overlap, not a full understanding measure.",
                           "Keyword scoring can miss correct paraphrases.",
                           "This heuristic is not validated; teacher verification is mandatory."]}

def ollama_evaluation(answer, question_text, reference, rubric, max_marks):
    if not settings.ollama_enabled:
        return None
    prompt = (
        "You are assisting a teacher. Evaluate conservatively against the question, reference answer, and rubric. "
        "Return JSON only with keys recommended_marks, summary, criteria, evidence, limitations. "
        "Do not invent evidence. Quote only exact short phrases from the student answer. "
        f"Marks must be between 0 and {max_marks}. Teacher must finalize marks.\n"
        f"Question: {question_text}\nReference: {reference}\nMaximum marks: {max_marks}\n"
        f"Rubric: {json.dumps(rubric, ensure_ascii=False)}\nStudent answer: {answer}"
    )
    try:
        response = requests.post(settings.ollama_base_url.rstrip("/") + "/api/generate",
            json={"model":settings.ollama_model,"prompt":prompt,"stream":False,"format":"json"}, timeout=90)
        response.raise_for_status()
        data = json.loads(response.json().get("response",""))
        data["recommended_marks"] = round(bounded(data.get("recommended_marks",0),0,max_marks),2)
        for key in ("criteria","evidence","limitations"):
            if not isinstance(data.get(key), list):
                data[key] = []
        data["limitations"].append("LLM feedback can be inaccurate; teacher verification is mandatory.")
        data["method"] = "ollama:" + settings.ollama_model
        return data
    except Exception:
        return None

def evaluate_answer(answer, question_text, reference, rubric, max_marks):
    return ollama_evaluation(answer, question_text, reference, rubric, max_marks) or baseline_evaluation(answer, reference, rubric, max_marks)
