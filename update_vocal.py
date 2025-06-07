from extract_resume_vocab import convert_pdfs_to_csv
from preprocessing_vocab import preprocessing
from extract_vocab import extract_vocabs

DATASET_FOLDER = "db/dataset"
vocab_folder_path = "vocabularies"
def update_vocabs():
    df_resumes = convert_pdfs_to_csv(DATASET_FOLDER)
    df_processed_resumes = preprocessing(df_resumes)
    extract_vocabs(df_processed_resumes, vocab_folder_path)