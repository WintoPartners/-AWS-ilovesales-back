import logging
from typing import Optional

import aiohttp
from fastapi import HTTPException

from app.imweb.old_imweb import imweb_service

logger = logging.getLogger(__name__)


class ImwebMemberHandler:
    async def get_mbti_result(self, email: str) -> Optional[str]:
        """회원의 MBTI 결과 조회"""
        try:
            # 액세스 토큰 얻기
            access_token = await imweb_service.get_access_token()
            if not access_token:
                logger.error("토큰 발급 실패")
                return None

            # 아임웹 API로 회원 정보 조회
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "access-token": access_token,
                }

                # 이메일로 회원 검색
                search_url = f"{imweb_service.base_url}/member/members"
                params = {"search_type": "email", "search_value": email, "limit": 1}

                logger.info(f"회원 검색 요청: {search_url} - {params}")

                async with session.get(
                    search_url, headers=headers, params=params
                ) as response:
                    if response.status == 404:
                        logger.error("회원을 찾을 수 없음")
                        return None

                    if not response.ok:
                        error_text = await response.text()
                        logger.error(f"회원 검색 실패: {error_text}")
                        return None

                    data = await response.json()
                    members = data.get("data", {}).get("list", [])

                    if not members:
                        logger.error("검색된 회원 없음")
                        return None

                    # home_page 필드에서 MBTI 결과 추출
                    member = members[0]
                    mbti_result = member.get("home_page")

                    logger.info(f"조회된 회원 정보: {member}")
                    logger.info(f"MBTI 결과: {mbti_result}")

                    if mbti_result and len(mbti_result) == 4:  # MBTI는 4글자
                        return mbti_result
                    return None

        except Exception as e:
            logger.error(f"MBTI 결과 조회 실패: {str(e)}")
            return None

    async def save_mbti_result(self, email: str, mbti_result: str) -> bool:
        """회원의 MBTI 결과 저장"""
        try:
            # 액세스 토큰 얻기
            access_token = await imweb_service.get_access_token()
            if not access_token:
                raise HTTPException(status_code=401, detail="토큰 발급 실패")

            # 회원 검색
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "access-token": access_token,
                }

                # 이메일로 회원 검색
                search_url = f"{imweb_service.base_url}/member/members"
                params = {"search_type": "email", "search_value": email, "limit": 1}

                async with session.get(
                    search_url, headers=headers, params=params
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error(f"회원 검색 실패: {error_text}")
                        raise HTTPException(
                            status_code=404, detail="회원을 찾을 수 없습니다"
                        )

                    data = await response.json()
                    members = data.get("data", {}).get("list", [])

                    if not members:
                        raise HTTPException(
                            status_code=404, detail="회원을 찾을 수 없습니다"
                        )

                    member = members[0]
                    member_code = member.get("member_code")

                    # MBTI 결과 저장
                    update_url = f"{imweb_service.base_url}/member/member/{member_code}"
                    update_data = {"home_page": mbti_result}

                    async with session.patch(
                        update_url, headers=headers, json=update_data
                    ) as update_response:
                        if update_response.status == 200:
                            return True
                        logger.error(
                            f"MBTI 결과 저장 실패: {await update_response.text()}"
                        )
                        return False

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"MBTI 결과 저장 중 오류 발생: {str(e)}")
            return False
