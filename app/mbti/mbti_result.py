import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.imweb.imweb_member_handler import ImwebMemberHandler

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response 모델
class MBTIResultRequest(BaseModel):
    email: EmailStr
    result: str


class MBTIResultResponse(BaseModel):
    email: str
    mbti: str | None = None
    message: str


# MBTI 결과 저장 엔드포인트
@router.post("/result")
async def save_mbti_result(request: MBTIResultRequest, max_retries: int = 5):
    """MBTI 결과 저장 (재시도 로직 포함)"""
    retry_count = 0
    last_error = None

    while retry_count < max_retries:
        try:
            logger.info(
                f"MBTI 결과 저장 시도 {retry_count + 1}/{max_retries}: {request.email}"
            )

            handler = ImwebMemberHandler()
            success = await handler.save_mbti_result(request.email, request.result)

            if success:
                return {
                    "email": request.email,
                    "mbti": request.result,
                    "message": "MBTI 결과가 성공적으로 저장되었습니다",
                }

            # 실패 시 재시도
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    f"저장 실패, 1초 후 재시도... ({retry_count}/{max_retries})"
                )
                await asyncio.sleep(1)  # 3초 대기
            else:
                logger.error(f"최대 재시도 횟수 도달: {request.email}")
                raise HTTPException(
                    status_code=500, detail="MBTI 결과 저장에 실패했습니다"
                )

        except HTTPException as he:
            last_error = he
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    f"HTTP 예외 발생, 1초 후 재시도... ({retry_count}/{max_retries}): {str(he)}"
                )
                await asyncio.sleep(1)
            else:
                logger.error(f"최대 재시도 횟수 도달 (HTTP 예외): {str(he)}")
                raise he

        except Exception as e:
            last_error = e
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    f"예외 발생, 1초 후 재시도... ({retry_count}/{max_retries}): {str(e)}"
                )
                await asyncio.sleep(1)
            else:
                logger.error(f"최대 재시도 횟수 도달 (예외): {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

    # 모든 재시도 실패 시
    if last_error:
        if isinstance(last_error, HTTPException):
            raise last_error
        raise HTTPException(status_code=500, detail=str(last_error))


# MBTI 결과 조회 엔드포인트
@router.get("/result/{email}")
async def get_mbti_result(email: str, max_retries: int = 5):
    """MBTI 결과 조회 (재시도 로직 포함)"""
    retry_count = 0
    last_error = None

    while retry_count < max_retries:
        try:
            logger.info(f"MBTI 결과 조회 시도 {retry_count + 1}/{max_retries}: {email}")

            handler = ImwebMemberHandler()
            mbti_result = await handler.get_mbti_result(email)

            if mbti_result:
                return {
                    "email": email,
                    "mbti": mbti_result,
                    "message": "MBTI 결과 조회 성공",
                }

            # 실패 시 재시도
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    f"조회 실패, 1초 후 재시도... ({retry_count}/{max_retries})"
                )
                await asyncio.sleep(1)  # 1초 대기
            else:
                logger.error(f"최대 재시도 횟수 도달: {email}")
                raise HTTPException(
                    status_code=404, detail="MBTI 결과를 찾을 수 없습니다"
                )

        except HTTPException as he:
            last_error = he
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    f"HTTP 예외 발생, 1초 후 재시도... ({retry_count}/{max_retries}): {str(he)}"
                )
                await asyncio.sleep(1)
            else:
                logger.error(f"최대 재시도 횟수 도달 (HTTP 예외): {str(he)}")
                raise he

        except Exception as e:
            last_error = e
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    f"예외 발생, 1초 후 재시도... ({retry_count}/{max_retries}): {str(e)}"
                )
                await asyncio.sleep(1)
            else:
                logger.error(f"최대 재시도 횟수 도달 (예외): {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

    # 모든 재시도 실패 시
    if last_error:
        if isinstance(last_error, HTTPException):
            raise last_error
        raise HTTPException(status_code=500, detail=str(last_error))
