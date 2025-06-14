from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from ranking import compute_resume_scores
from re_ranking import compute_resume_scores_crossencoder
from util import verify_token
from extract_feature_tfidf import extract_feature
from crawl_pipeline import Crawl_Pipeline
from update_vocal import update_vocabs

app = FastAPI()
crawl_pipeline = Crawl_Pipeline()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = BackgroundScheduler()
scheduler.add_job(
    crawl_pipeline.process_crawl_pdf,
    trigger='cron',
    hour=0,
    minute=0,
    id='daily_job'
)
scheduler.add_job(
    crawl_pipeline.process_crawl_profile,
    trigger='cron',
    day_of_week='mon',
    hour=0,
    minute=0,
    id='weekly_job'
)
scheduler.add_job(
    update_vocabs,
    trigger='cron',
    day_of_week='mon',
    hour=0,
    minute=0,
    id='monthly_job'
)
scheduler.start()

@app.get('/')
def hello():
    return 'Hello World!\n'

class RankingDto(BaseModel):
    resumes: List[Dict[str, Any]]
    jd: Dict[str, Any]
    topResume: int

@app.post('/api/rank')
def ranking (dto: RankingDto, current_user: dict = Depends(verify_token)):
    resumes_data = dto.resumes
    jd_data = dto.jd
    top_resumes = dto.topResume

    print("resume_1: \n", resumes_data[0])
    jd_feature, resume_feature_list = extract_feature(resumes_data, jd_data)

    # ranking
    if (top_resumes + 5 >= len(resumes_data)):
        top_ranking_resumes = compute_resume_scores(resume_feature_list, jd_feature, len(resumes_data))
    else:
        top_ranking_resumes = compute_resume_scores(resume_feature_list, jd_feature, top_resumes + 5)

    # Lấy danh sách resume_id từ top_ranking_resumes
    top_resume_ids = [item['id'] for item in top_ranking_resumes]

    # Lọc ra các resumes có _id nằm trong top_resume_ids
    matched_resumes = [resume for resume in resumes_data if resume['_id'] in top_resume_ids]
    top_reranking_resumes = compute_resume_scores_crossencoder(matched_resumes, jd_data, top_resumes)

    return top_reranking_resumes