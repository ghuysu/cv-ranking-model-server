from sklearn.feature_extraction.text import TfidfVectorizer
import json
import os

def extract_vocabs(df, vocab_folder_path):
    
    tfidf_max_features = {
        "Role": 20,
        "Top Skills": 65,
        "Experience": 55,
        "Education": 20,
        "Languages": 10
    }

    os.makedirs(vocab_folder_path, exist_ok=True)

    # TF-IDF cho từng trường
    vectorizers = {}
    tfidf_features = []
    feature_names = []

    for column_name, max_features in tfidf_max_features.items():
        text_data = df[column_name].fillna('') 
        vectorizer = TfidfVectorizer(max_features=max_features)
        tfidf_matrix = vectorizer.fit_transform(text_data)

        # Lưu lại vectorizer và ma trận
        vectorizers[column_name] = vectorizer
        tfidf_features.append(tfidf_matrix)

        # Tạo tên đặc trưng
        tokens = vectorizer.get_feature_names_out()
        feature_names.extend([f"{column_name}_{token}" for token in tokens])

        # Lưu từ vựng ra file json
        vocab_path = f"{vocab_folder_path}/{column_name}_vocab.json"
        vocab_clean = {k: int(v) for k, v in vectorizer.vocabulary_.items()}
        with open(vocab_path, "w", encoding="utf-8") as f:
            json.dump(vocab_clean, f, ensure_ascii=False, indent=2)


    print("Các bộ từ vựng TF-IDF đã được lưu vào thư mục 'vocabularies/'")
