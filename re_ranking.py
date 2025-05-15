from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from extract_years import extract_year_range, extract_year_resume

cross_encoder_model_name = "cross-encoder/stsb-roberta-base"

tokenizer = AutoTokenizer.from_pretrained(cross_encoder_model_name)
model = AutoModelForSequenceClassification.from_pretrained(cross_encoder_model_name)
model.eval()

def compute_resume_scores_crossencoder(resume_info, jd_row, top_resumes):
    results = []

    jd_role = str(jd_row.get("role", ""))
    jd_combined = f"{jd_row.get('skills', '')}. {jd_row.get('jobDescription', '')} {jd_row.get('responsibilities', '')}"

    exp_str = jd_row.get("experience", "")
    min_jd_months, max_jd_months = extract_year_range(exp_str)

    for resume in resume_info:
        score = 0.0

        role_score = get_crossencoder_score((str(resume.get("role", "")), jd_role))
        score += role_score * 0.25

        resume_combined = f"{resume.get('topSkills', '')}. {resume.get('experience', '')}"
        combined_score = get_crossencoder_score((resume_combined, jd_combined))
        score += combined_score * 0.60

        resume_exp_str = resume.get("yearOfExperience", "")
        resume_months = extract_year_resume(resume_exp_str)

        if min_jd_months == 0 and max_jd_months == 0:
            years_score = 1.0
        elif min_jd_months <= resume_months <= max_jd_months:
            years_score = 1.0
        elif resume_months < min_jd_months:
            years_score = resume_months / min_jd_months
        elif max_jd_months == float('inf'):
            years_score = 1.0
        else:
            years_score = max_jd_months / resume_months

        score += years_score * 0.15

        results.append({
            "id": resume.get("sessionId"),
            "fileName": resume.get("fileName", ""),
            "score": score
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)[:top_resumes]

def get_crossencoder_score(text_pair):
    inputs = tokenizer(text_pair[0], text_pair[1], padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        score = outputs.logits.item()
        return max(0.0, min(score / 5.0, 1.0))
