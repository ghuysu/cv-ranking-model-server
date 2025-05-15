import re
from sklearn.metrics.pairwise import cosine_similarity
from extract_years import extract_year_range, extract_year_resume

def compute_resume_scores(resume_features_list, jd_features, top_resumes):
    results = []

    exp_str = jd_features.get("years_of_experience", "")
    min_jd_months, max_jd_months = extract_year_range(exp_str)

    for resume in resume_features_list:
        score = 0.0
        role_sim = cosine_similarity(resume["role_vector"], jd_features["role_vector"])[0][0]
        print("role: ", role_sim)
        score += role_sim * 0.25

        skills_sim = cosine_similarity(resume["skills_vector"], jd_features["skills_vector"])[0][0]
        print("skills: ", skills_sim)
        score += skills_sim * 0.30

        exp_sim = cosine_similarity(resume["experience_vector"], jd_features["experience_vector"])[0][0]
        print("exp: ", exp_sim)
        score += exp_sim * 0.30

        resume_exp_str = resume.get("years_of_experience", "")
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
            "id": resume['id'],
            "fileName": resume['fileName'],
            "score": score
        })

    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_resumes]
    return sorted_results
