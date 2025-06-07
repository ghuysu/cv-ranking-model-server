from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dateutil import parser
from datetime import datetime
import pandas as pd
import re
import nltk
import spacy
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
nlp = spacy.load("en_core_web_sm")


# Download necessary resources
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')

# Initialize NLP tools
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def preprocess_text(text, keep_numbers=False):
    if pd.isna(text):  
        return ""
    
    text = text.lower().strip() 
    text = re.sub(r'\bpage\s+\d+\s+of\s+\d+\b', '', text)
    text = re.sub(r"\S+@\S+", "", text)  # Remove email
    text = re.sub(r"#[A-Za-z0-9_]+", "", text)  # Remove hashtags
    text = re.sub(r"@[A-Za-z0-9_]+", "", text)  # Remove mentions
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text) if keep_numbers else re.sub(r'[^a-zA-Z\s]', '', text)
   
    words = word_tokenize(text)
    words = [word for word in words if word not in stop_words]
    words = [lemmatizer.lemmatize(word) for word in words]
    return " ".join(words)

def translate_french_date_string(date_str):
    month_map = {
        "janvier": "January", "février": "February", "fevrier": "February", "vrier": "February",
        "mars": "March", "avril": "April", "mai": "May", "juin": "June", "juillet": "July",
        "août": "August", "aout": "August", "septembre": "September", "octobre": "October",
        "novembre": "November", "décembre": "December", "decembre": "December", "cembre": "December"
    }
    for fr, en in month_map.items():
        if fr in date_str.lower():
            date_str = re.sub(fr, en, date_str, flags=re.IGNORECASE)
            break
    return date_str

def process_experience(text):
    lines = text.split("\n")
    all_matches = []
    lines_to_remove = []

    pattern = re.compile(r"([\wéèêëàâîïôöûüç]+\s+\d{4})\s*[-–]\s*(Present|[\wéèêëàâîïôöûüç]+\s+\d{4})(?:\s*\(.*?\))?", re.IGNORECASE)

    for i, line in enumerate(lines):
        matches = pattern.findall(line)
        if matches:
            all_matches.extend(matches)
            lines_to_remove.append(line)
            if i + 1 < len(lines):  # Thêm dòng ngay sau nó
                lines_to_remove.append(lines[i + 1])

    total_months = 0

    for start_str, end_str in all_matches:
        try:
            start_str_translated = translate_french_date_string(start_str)
            end_str_translated = translate_french_date_string(end_str)

            start_date = parser.parse(start_str_translated)
            end_date = datetime.now() if 'present' in end_str_translated.lower() else parser.parse(end_str_translated)

            diff_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
            total_months += max(diff_months, 0)
        except Exception as e:
            continue

    years = total_months // 12
    months = total_months % 12
    cleaned_text = " ".join([line for line in lines if line not in lines_to_remove])

    return f"{years} years {months} months", cleaned_text

def process_education(text):
    if pd.isna(text):
        return ""
    text = str(text)
    lines = text.split("\n")
    cleaned_lines = []
    
    pattern = re.compile(r"\b[\wéèêëàâîïôöûüç]+\s+\d{4}\b|\b\d{4}\b", re.IGNORECASE)

    for line in lines:
        cleaned_line = pattern.sub("", line) 
        cleaned_lines.append(cleaned_line.strip())

    cleaned_text = " ".join(cleaned_lines)
    return cleaned_text

def clean_languages(x):
    if not isinstance(x, str):
        return ""
    
    doc = nlp(x)
    languages = [ent.text.lower() for ent in doc.ents if ent.label_ in ["LANGUAGE", "NORP"]]
    unique_languages = list(set(languages))
    return " ".join(unique_languages)

# Hàm gán Top Skills dựa trên độ tương đồng của Role + Experience
def fill_missing_skills_from_similarity(df, combined_text, threshold=0.5):
    filled_indices = []

    combined_vectorizer = TfidfVectorizer(max_features=50).fit(combined_text)
    combined_vectors = combined_vectorizer.transform(combined_text)

    missing_skills = df[df['Top Skills'].isna() | (df['Top Skills'].str.strip() == '')]
    print(f"Missing Top Skills: {missing_skills.shape[0]} rows")

    df_index_to_position = {idx: pos for pos, idx in enumerate(df.index)}

    for idx, row in missing_skills.iterrows():
        query_text = f"{row['Role']} {row['Experience']}"
        query_vec = combined_vectorizer.transform([query_text])

        sims = cosine_similarity(query_vec, combined_vectors)[0]

        similar_rows = df[df['Top Skills'].notna() & (df['Top Skills'].str.strip() != '')]

        ranked = sorted(
            [
                (i, sims[df_index_to_position[i]])
                for i in similar_rows.index
                if sims[df_index_to_position[i]] > threshold
            ],
            key=lambda x: -x[1]
        )

        if ranked:
            best_match_idx = ranked[0][0]
            df.at[idx, 'Top Skills'] = df.at[best_match_idx, 'Top Skills']
            filled_indices.append(idx)

    return df, filled_indices


def preprocessing (df):
    
    for col in ['Experience', 'Top Skills', 'Summary']:
        df[col] = df[col].apply(lambda x: str(x).strip() if pd.notna(x) else x)

    df.replace(to_replace=r'(?i)^n/?a$', value=pd.NA, regex=True, inplace=True)

    def is_empty(x):
       return pd.isna(x) or str(x).strip().lower() in ['', 'n/a']

    condition_drop = (
        (df['Experience'].apply(is_empty) & df['Top Skills'].apply(is_empty)) |
        (df['Top Skills'].apply(is_empty) & df['Summary'].apply(is_empty))
    )
    df_clean = df[~condition_drop].copy()

    # Define preprocessing rules for each column
    column_rules = {
        "Role": {"keep_numbers": False},
        "Top Skills": {"keep_numbers": True},
        "Experience": {"keep_numbers": False},
        "Education": {"keep_numbers": True},
        "Languages": {"keep_numbers": False},
    }
    
    df_clean[["Years of Experience", "Experience"]] = df_clean["Experience"].apply(
        lambda x: pd.Series(process_experience(x))
    )

    df_clean["Education"] = df_clean["Education"].apply(lambda x: process_education(x))

    # Apply preprocessing based on column-specific rules
    for col, rules in column_rules.items():        
        df_clean[col] = df_clean[col].apply(lambda x: preprocess_text(
            x, 
            keep_numbers=rules["keep_numbers"],
        ))
        if col == "Languages":
            df_clean[col] = df_clean[col].apply(lambda x: clean_languages(x))


    # Process empty data
    combined_text = df_clean[['Role', 'Experience']].fillna('').apply(
        lambda r: f"{r['Role']} {r['Experience']}", axis=1
    ).tolist()

    df_clean, filled = fill_missing_skills_from_similarity(df_clean, combined_text)
    print(f"Đã gán Top Skills cho {len(filled)} dòng.")

    if 'Publications' in df_clean.columns:
        df_clean.drop(columns=['Publications'], inplace=True)

    # sort columns
    desired_column_order = [
        "Category", "Name", 'Role', "Top Skills", "Experience", "Years of Experience",
        "Education", "Languages", "Filename"
    ]
    df_clean = df_clean[[col for col in desired_column_order if col in df_clean.columns]]

    print("Tiền xử lý hoàn thành.")
    return df_clean