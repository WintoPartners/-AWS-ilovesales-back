import asyncio
import hashlib
import hmac
import logging
import os
import time
from typing import Optional

import aiohttp
from dotenv import load_dotenv

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class ImwebService:
    def __init__(self):
        self.api_key = os.getenv("IMWEB_API_KEY")
        self.secret_key = os.getenv("IMWEB_SECRET_KEY")
        self.base_url = "https://api.imweb.me/v2"
        self.access_token = None
        self.token_timestamp = None
        self.category_mapping = {}

    def generate_signature(self, timestamp: str) -> str:
        """HMAC 서명 생성"""
        message = f"{self.api_key}{timestamp}"
        signature = hmac.new(
            self.secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return signature

    async def get_access_token(self):
        """액세스 토큰 발급 또는 재사용"""
        current_time = time.time()

        # 토큰이 없거나, 발급된지 50분이 지났으면 새로 발급
        if (
            not self.access_token
            or not self.token_timestamp
            or current_time - self.token_timestamp > 3000
        ):  # 50분 = 3000초
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.base_url}/auth"
                    params = {"key": self.api_key, "secret": self.secret_key}

                    async with session.get(url, params=params) as response:
                        result = await response.json()
                        if response.status == 200 and result.get("access_token"):
                            self.access_token = result["access_token"]
                            self.token_timestamp = current_time
                            return self.access_token
                        logger.error(f"토큰 발급 실패: {result}")
                        return None
            except Exception as e:
                logger.error(f"토큰 발급 실패: {str(e)}")
                return None

        return self.access_token

    async def refresh_token_if_needed(self, response_data: dict) -> bool:
        """토큰 에러 시 갱신"""
        if response_data.get("code") == -2:  # Error Token
            logger.info("토큰 만료 감지, 새로운 토큰 발급 시도")
            self.access_token = None
            self.token_timestamp = None
            return True
        return False

    async def get_all_members(self, page: int = 1):
        """모든 회원 목록 조회"""
        try:
            # 토큰 가져오기 (캐시된 토큰 사용)
            access_token = await self.get_access_token()
            if not access_token:
                return {"error": "토큰 발급 실패"}

            headers = {"Content-Type": "application/json", "access-token": access_token}

            params = {"page": page, "limit": 100}

            url = f"{self.base_url}/member/members"

            # API 호출 전 1초 대기
            await asyncio.sleep(1)

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    return await response.json()

        except Exception as e:
            logging.error(f"API 호출 에러: {str(e)}")
            return {"error": str(e)}

    async def get_member_by_email(self, email: str):
        """이메일로 회원 정보를 조회하는 메서드"""
        try:
            # 아임웹 API를 통해 회원 정보 조회
            access_token = await self.get_access_token()
            if not access_token:
                return None

            headers = {"Content-Type": "application/json", "access-token": access_token}
            url = f"{self.base_url}/member/members"
            params = {"search_type": "email", "keyword": email}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    result = await response.json()
                    if response.status == 200 and "data" in result:
                        members = result["data"].get("list", [])
                        return members[0] if members else None
                    return None

        except Exception as e:
            logger.error(f"회원 정보 조회 실패: {str(e)}")
            return None

    async def get_categories(self) -> Optional[list]:
        """아임웹 카테고리 목록 조회"""
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return None

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "access-token": access_token,
                }
                url = f"{self.base_url}/shop/categories"

                async with session.get(url, headers=headers) as response:
                    result = await response.json()
                    if response.status == 200:
                        return result.get("categories", [])
                    return None
        except Exception as e:
            logger.error(f"카테고리 조회 실패: {str(e)}")
            return None

    async def initialize_categories(self):
        """카테고리 매핑 초기화"""
        try:
            categories = await self.get_categories()
            if categories:
                self.category_mapping.clear()
                for category in categories:
                    self.category_mapping[category["name"]] = category["no"]
                logger.info(f"카테고�� 매핑 완료: {self.category_mapping}")
            else:
                logger.warning("카테고리 정보를 가져오지 못했습니다.")
        except Exception as e:
            logger.error(f"카테고리 초기화 실패: {str(e)}")

    def get_category_id(self, category_name: str) -> Optional[str]:
        """카테고리 이름으로 ID 조회"""
        return self.category_mapping.get(category_name)

    async def upload_image(
        self, access_token: str, image_data: bytes, filename: str, content_type: str
    ) -> Optional[str]:
        """이미지 업로드"""
        try:
            headers = {"access-token": access_token, "Accept": "application/json"}

            # multipart/form-data로 이미지 전송
            data = aiohttp.FormData()
            data.add_field(
                "files[]",  # 파일 필드
                image_data,
                filename=filename,
                content_type=content_type,
            )
            # 추가 필드
            data.add_field("target", "shop")  # 업로드 대상
            data.add_field("type", "image")  # 파일 타입

            # 아임웹 API 엔드포인트
            url = f"{self.base_url}/file"  # 수정된 엔드포인트

            logger.info(f"이미지 업로드 시도 - URL: {url}")
            logger.info(
                f"파일 정보 - 이름: {filename}, 타입: {content_type}, 크기: {len(image_data)} bytes"
            )
            logger.info(f"헤더 정보: {headers}")

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    response_text = await response.text()
                    logger.info(
                        f"아임웹 응답 - 상태: {response.status}, 내용: {response_text}"
                    )

                    if response.status == 200:
                        try:
                            result = await response.json()
                            if result.get("code") == 200:
                                files = result.get("data", {}).get("files", [])
                                if files and len(files) > 0:
                                    # 이미지 URL 구성
                                    file_info = files[0]
                                    image_url = file_info.get("url")
                                    if image_url:
                                        logger.info(
                                            f"이미지 업로드 성공 - URL: {image_url}"
                                        )
                                        return image_url
                        except Exception as e:
                            logger.error(f"응답 파싱 실패: {str(e)}")

                    logger.error(
                        f"이미지 업로드 실패 - 상태: {response.status}, 응답: {response_text}"
                    )
                    return None

        except Exception as e:
            logger.error(f"이미지 업로드 중 예외 발생: {str(e)}")
            return None


# 서비스 인스턴스 생성
imweb_service = ImwebService()
