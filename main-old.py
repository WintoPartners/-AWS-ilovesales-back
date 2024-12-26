import logging
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import agency, user
from .services.imweb_service import imweb_service

# 로깅 설정
log_dir = Path("/var/www/app/logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"),
    ],
)

logger = logging.getLogger(__name__)

app = FastAPI()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    try:
        response = await call_next(request)
        duration = datetime.now() - start_time
        logger.info(
            f"Path: {request.url.path} Duration: {duration.total_seconds()}s Status: {response.status_code}"
        )
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}", exc_info=True)
        raise


# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(agency.router, prefix="/api/agency", tags=["agency"])
app.include_router(user.router, prefix="/users", tags=["users"])


@app.on_event("startup")
async def startup_event():
    logger.info("애플리케이션 시작")
    # 초기 액세스 토큰 발급
    await imweb_service.get_access_token()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("애플리케이션 종료")


@app.get("/")
async def root():
    return {"message": "API 서버가 정상 작동 중입니다."}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health_check():
    """서버 상태 확인용 엔드포인트"""
    return {
        "status": "ok",
        "service": "ilovesales-api",
        "timestamp": datetime.now().isoformat(),
    }
