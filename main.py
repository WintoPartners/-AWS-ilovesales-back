import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agency_admin.agency_endpoint import router as agency_router
from app.imweb.old_imweb import imweb_service
from app.mbti.mbti_result import router as mbti_router

app = FastAPI(title="ILOVESALES API")

# CORS 설정 수정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.ilovesales.site",  # 메인 도메인
        "https://ilovesales.site",  # 서브 도메인 없는 버전
        "https://ilovesales-site.imweb.me",  # 아임웹 도메인
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# 시작 시 이벤트
@app.on_event("startup")
async def startup_event():
    # 초기 액세스 토큰 발급
    await imweb_service.get_access_token()


# 라우터 등록
app.include_router(agency_router, prefix="/agency", tags=["agency"])
app.include_router(mbti_router, prefix="/mbti", tags=["mbti"])


# 헬스체크 엔드포인트
@app.get("/")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
