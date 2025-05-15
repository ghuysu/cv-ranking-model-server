import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

tfidf_fields = ["Role", "Top Skills", "Experience"]


def load_vocabularies(tfidf_fields):
    vocabs = {}
    for field in tfidf_fields:
        with open(f"vocabularies/{field}_vocab.json", "r", encoding="utf-8") as f:
            vocabs[field] = json.load(f)
    return vocabs


def extract_resume_features(row):
    features = {}
    vocabs = load_vocabularies(tfidf_fields)

    vectorizer_role = TfidfVectorizer(vocabulary=vocabs["Role"])
    role_text = row.get("role", "")
    features["role_vector"] = vectorizer_role.fit_transform([role_text])

    vectorizer_skills = TfidfVectorizer(vocabulary=vocabs["Top Skills"])
    skills_text = row.get("topSkills", "")
    features["skills_vector"] = vectorizer_skills.fit_transform([skills_text])

    vectorizer_exp = TfidfVectorizer(vocabulary=vocabs["Experience"])
    exp_text = row.get("experience", "")
    features["experience_vector"] = vectorizer_exp.fit_transform([exp_text])

    features["years_of_experience"] = row.get("yearOfExperience", "")

    edu_raw = row.get("education", "")
    edu_text = str(edu_raw).lower() if pd.notna(edu_raw) else ""

    edu_mapping = {
        "doctorate": 4, "phd": 4, "master": 4,
        "university": 3, "bachelor": 3,
        "associate": 2, "high school": 1,
    }
    mapped_edu = max([v for k, v in edu_mapping.items() if k in edu_text], default=0)
    features["education_level"] = mapped_edu
    features["fileName"] = row.get("fileName", "")
    features["id"] = row.get("_id")

    return features


def extract_jd_features(jd_row):
    features = {}
    vocabs = load_vocabularies(tfidf_fields)

    vectorizer_role = TfidfVectorizer(vocabulary=vocabs["Role"])
    role_text = jd_row.get("role", "")
    features["role_vector"] = vectorizer_role.fit_transform([role_text])

    vectorizer_skills = TfidfVectorizer(vocabulary=vocabs["Top Skills"])
    skills_text = jd_row.get("skills", "")
    features["skills_vector"] = vectorizer_skills.fit_transform([skills_text])

    vectorizer_exp = TfidfVectorizer(vocabulary=vocabs["Experience"])
    exp_text = jd_row.get("jobDescription", "") + " " + jd_row.get("responsibilities", "")
    features["experience_vector"] = vectorizer_exp.fit_transform([exp_text])

    features["years_of_experience"] = jd_row.get("experience", "")
    return features


def extract_feature(cleaned_resume_list, cleaned_jd):
    resume_feature_list = []

    feature_jd = extract_jd_features(cleaned_jd)

    for resume in cleaned_resume_list:
        feature_resume = extract_resume_features(resume)
        resume_feature_list.append(feature_resume)

    return feature_jd, resume_feature_list