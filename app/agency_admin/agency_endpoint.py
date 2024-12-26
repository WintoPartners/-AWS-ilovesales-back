import asyncio
import json
import logging
import os

import aiohttp
from fastapi import APIRouter, HTTPException

from app.imweb.old_imweb import imweb_service

router = APIRouter()
logger = logging.getLogger(__name__)


# 상수 추가
LOCATION_MAP = {"서울": "s", "그 외": "e"}

REVERSE_LOCATION_MAP = {"s": "서울", "e": "그 외"}

MBTI_MAP = {
    "ENFJ": "1",
    "ENFP": "2",
    "ENTJ": "3",
    "ENTP": "4",
    "ESFJ": "5",
    "ESFP": "6",
    "ESTJ": "7",
    "ESTP": "8",
    "INFJ": "9",
    "INFP": "0",
    "INTJ": "a",
    "INTP": "b",
    "ISFJ": "c",
    "ISFP": "d",
    "ISTJ": "e",
    "ISTP": "f",
}

REVERSE_MBTI_MAP = {v: k for k, v in MBTI_MAP.items()}

CATEGORY_MAP = {
    "웹개발": "w",
    "디자인": "d",
    "앱개발": "a",
    "영상/사진": "p",
    "브랜딩": "b",
    "마케팅": "m",
    "번역/통역": "t",
    "컨설팅": "c",
}

REVERSE_CATEGORY_MAP = {v: k for k, v in CATEGORY_MAP.items()}

SUB_CATEGORY_MAP = {
    # 웹개발
    "프론트엔드": "1",
    "백엔드": "2",
    "풀스택": "3",
    "쇼핑몰": "4",
    "랜딩페이지": "5",
    "기타 웹개발": "6",
    # 디자인/브랜딩 공통
    "UI/UX": "a",
    "그래픽": "b",
    "3D": "c",
    "일러스트": "d",
    "편집": "e",
    "CI/BI": "f",
    "패키지": "g",
    "네이밍": "h",
    "브랜드전략": "i",
    "기타 디자인": "j",
    "기타 브랜딩": "k",
    # 앱개발
    "안드로이드": "l",
    "iOS": "m",
    "크로스플랫폼": "n",
    "하이브리드": "o",
    "기타 앱개발": "p",
    # 영상/사진
    "영상촬영": "q",
    "영상편집": "r",
    "사진촬영": "s",
    "사진편집": "t",
    "기타 영상/사진": "u",
    # 마케팅
    "SNS마케팅": "v",
    "퍼포먼스": "w",
    "콘텐츠제작": "x",
    "PR": "y",
    "기타 마케팅": "z",
    # 번역/통역
    "영어": "7",
    "중국어": "8",
    "일본어": "9",
    "기타 번역/통역": "0",
    # 컨설팅
    "경영컨설팅": "A",
    "IT컨설팅": "B",
    "마케팅컨설": "C",
    "기타 컨설팅": "D",
}

REVERSE_SUB_CATEGORY_MAP = {v: k for k, v in SUB_CATEGORY_MAP.items()}


# 이미지 URL 처리 함수 추가
def process_image_url(image_urls):
    """이미지 URL 처리 및 검증"""
    if not image_urls:
        return None

    try:
        if isinstance(image_urls, dict):
            # 이미지 URL이 딕셔너리인 경우 첫 번째 URL 사용
            first_url = next(iter(image_urls.values()), None)
            if first_url and isinstance(first_url, str):
                # 이미 전체 URL인 경우 그대로 사용
                if first_url.startswith(("http://", "https://")):
                    return first_url
                # CDN URL 구성 - 이미 S20241019b5f39d60ebd35가 포함되어 있으므로 base URL만 추가
                return f"https://cdn-optimized.imweb.me/upload/{first_url}"
        elif isinstance(image_urls, str):
            # 이미지 URL이 문자열인 경우
            if image_urls.startswith(("http://", "https://")):
                return image_urls
            # CDN URL 구성 - 이미 S20241019b5f39d60ebd35가 포함되어 있으므로 base URL만 추가
            return f"https://cdn-optimized.imweb.me/upload/{image_urls}"
    except Exception as e:
        logger.error(f"이미지 URL 처리 오류: {str(e)}")
        return None


@router.get("/list")
async def get_agencies():
    """에이전시 목록 조회"""
    try:
        # 토큰 재시도 로직
        for attempt in range(3):
            access_token = await imweb_service.get_access_token()
            logger.info(
                f"액세스 토큰 발급 시도 {attempt + 1}: {access_token is not None}"
            )

            if access_token:
                break

            await asyncio.sleep(1)

        if not access_token:
            logger.error("토큰 발급 3회 시도 실패")
            raise HTTPException(status_code=401, detail="토큰 발급 실패")

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            headers = {"Content-Type": "application/json", "access-token": access_token}
            products_url = f"{imweb_service.base_url}/shop/products"
            params = {"per_page": 100, "page": 1}

            async with session.get(
                products_url,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                logger.info(f"상품 목록 조회 상태 코드: {response.status}")
                result = await response.json()

                if result.get("code") != 200:
                    logger.error(f"API 응답 에러: {result}")
                    if result.get("code") == 401:
                        await imweb_service.refresh_token()
                        raise HTTPException(
                            status_code=401, detail="토큰 만료, 재시도 필요"
                        )

                products = result.get("data", {}).get("list", [])
                logger.info(f"조회된 전체 상품 수: {len(products)}")

                agencies = []
                for item in products:
                    try:
                        # 이미지 URL 처리
                        image_urls = item.get("image_url", {})
                        logger.info(f"상품 {item.get('name')} 이미지 URL: {image_urls}")
                        first_image_url = (
                            next(iter(image_urls.values()), None)
                            if image_urls
                            else None
                        )

                        # brand 데이터 파싱
                        brand_data = json.loads(item.get("brand", "[]"))
                        logger.info(
                            f"상품 {item.get('name')} brand 데이터: {brand_data}"
                        )

                        if isinstance(brand_data, list) and len(brand_data) >= 4:
                            location = REVERSE_LOCATION_MAP.get(brand_data[0], "서울")
                            mbti = REVERSE_MBTI_MAP.get(brand_data[1], "ENFJ")
                            main_category = brand_data[2]
                            sub_categories = brand_data[3]
                        else:
                            location = "서울"
                            mbti = "ENFJ"
                            main_category = ""
                            sub_categories = []

                        agency = {
                            "no": item.get("no"),
                            "name": item.get("name"),
                            "content": item.get("simple_content_plain", ""),
                            "category": item.get("categories", []),
                            "brand": item.get("brand"),
                            "location": location,
                            "mbti": mbti,
                            "main_category": main_category,
                            "sub_categories": sub_categories,
                            "image_url": first_image_url,
                            "status": item.get("prod_status"),
                        }
                        logger.info(f"파싱된 에이전시 데이터: {agency}")
                        agencies.append(agency)

                    except Exception as e:
                        logger.error(f"데이터 처리 중 오류 발생: {str(e)}")
                        logger.error(f"문제가 된 데이터: {item.get('brand')}")
                        continue

                logger.info(f"최종 처리된 에이전시 수: {len(agencies)}")
                return {"code": 200, "message": "success", "data": agencies}

    except aiohttp.ClientError as e:
        logger.error(f"API 요청 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="API 요청 실패")


@router.patch("/{agency_id}")
async def update_agency(agency_id: str, data: dict):
    """에이전시 정보 업데이트"""
    try:
        logger.info(f"에이전시 업데이트 시작 - agency_id: {agency_id}")
        logger.info(f"요청 데이터: {data}")

        access_token = await imweb_service.get_access_token()
        if not access_token:
            logger.error("토큰 발급 실패")
            raise HTTPException(status_code=401, detail="토큰 발급 실패")
        image_url = None
        if "image" in data:
            image_data = data["image"]
            image_url = await imweb_service.upload_image(access_token, image_data)
            if image_url:
                logger.info(f"이미지 업로드 성공: {image_url}")
        update_data = {
            "no": data.get("no"),  # 상품번호
            "name": data.get("name"),  # 상품명
            "content": data.get("content"),  # 상세설명
            "simple_content": data.get("simple_content"),  # 요약설명이 누락되어 있었음
            "category": data.get("category", []),  # 카테고리 코드
            "brand": data.get("brand"),  # 브랜드 정보
            "location": data.get("location"),  # 위치 정보
            "mbti": data.get("mbti"),  # MBTI 정보
            "main_category": data.get("main_category"),  # 메인 카테고리
            "sub_categories": data.get("sub_categories", []),  # 서브 카테고리 목록
            "image_url": image_url if image_url else data.get("image_url"),
            "status": data.get("status", "sale"),  # 상태
            "display_status": "VISIBLE",  # 노출 상태 추가
        }

        logger.info(f"구성된 업데이트 데이터: {update_data}")

        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/json", "access-token": access_token}
            url = f"{imweb_service.base_url}/shop/products/{agency_id}"

            async with session.patch(
                url, headers=headers, json=update_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"아임웹 API 응답: {result}")
                    return {"code": 200, "message": "업데이트 성공", "data": result}
                else:
                    error_data = await response.text()
                    logger.error(f"아임웹 API 오류 응답: {error_data}")
                    raise HTTPException(status_code=response.status, detail=error_data)

    except Exception as e:
        logger.error(f"에이전시 업데이트 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_agency(data: dict):
    """새 에이전시 추가"""
    try:
        access_token = await imweb_service.get_access_token()
        if not access_token:
            raise HTTPException(status_code=401, detail="토큰 발급 실패")

        # 상품 데이터 준비
        product_data = {
            "name": data["name"],
            "content": data["content"],
            "simple_content": data["simple_content"],
            "brand": data["brand"],
            "prod_status": "sale",
            "price": 0,
            "price_tax": False,
            "stock_use": False,
            "categories": [os.getenv("IMWEB_AGENCY_CATEGORY")],
            "display_status": "VISIBLE",
            "images": [
                {
                    "url": "https://cdn.imweb.me/upload/S202411023d3941ab4335b/6b53a30e8b45a.png",
                    "thumb_url": "https://cdn.imweb.me/upload/S202411023d3941ab4335b/6b53a30e8b45a.png",
                    "caption": "",
                }
            ],
        }

        logger.info(f"아임웹 전송 데이터: {product_data}")

        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/json", "access-token": access_token}
            url = f"{imweb_service.base_url}/shop/products"

            async with session.post(
                url, headers=headers, json=product_data
            ) as response:
                result = await response.json()
                logger.info(f"에이전시 생성 결과: {result}")
                return {"code": 200, "data": result}

    except Exception as e:
        logger.error(f"에이전시 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agency_id}")
async def get_agency(agency_id: str):
    """개별 에이전시 정보 조회"""
    try:
        access_token = await imweb_service.get_access_token()
        if not access_token:
            raise HTTPException(status_code=401, detail="토큰 발급 실패")

        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/json", "access-token": access_token}
            url = f"{imweb_service.base_url}/shop/products/{agency_id}"

            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    error_data = await response.text()
                    logger.error(f"아임웹 API 응답: {error_data}")
                    raise HTTPException(
                        status_code=response.status, detail="에이전시 정보 조회 실패"
                    )

                data = await response.json()
                item = data.get("data", {})

                try:
                    # 이미지 URL 처리
                    image_urls = item.get("image_url", {})
                    first_image_url = (
                        next(iter(image_urls.values()), None) if image_urls else None
                    )

                    # brand 데이터 파싱
                    brand_data = json.loads(item.get("brand", "[]"))
                    if isinstance(brand_data, list) and len(brand_data) >= 4:
                        location = REVERSE_LOCATION_MAP.get(brand_data[0], "서")
                        mbti = REVERSE_MBTI_MAP.get(brand_data[1], "ENFJ")
                        main_category = brand_data[2]
                        sub_categories = brand_data[3]
                    else:
                        location = "서울"
                        mbti = "ENFJ"
                        main_category = ""
                        sub_categories = []

                    agency = {
                        "no": item.get("no"),
                        "name": item.get("name"),
                        "content": item.get("content", ""),  # HTML 형식의 상세 설명
                        "simple_content": item.get("simple_content", ""),
                        "category": item.get("categories", []),
                        "brand": item.get("brand"),
                        "location": location,
                        "mbti": mbti,
                        "main_category": main_category,
                        "sub_categories": sub_categories,
                        "image_url": first_image_url,
                        "status": item.get("prod_status"),
                    }

                    return {"code": 200, "message": "success", "data": agency}

                except Exception as e:
                    logger.error(f"데이터 처리 중 오류 발생: {str(e)}")
                    logger.error(f"문제가 된 데이터: {item.get('brand')}")
                    raise HTTPException(
                        status_code=500, detail="데이터 처리 중 오류 발생"
                    )

    except Exception as e:
        logger.error(f"에이전시 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mbti-results")
async def get_mbti_matching_data():
    """MBTI 매칭 데이터 조회"""
    try:
        results = await get_all_mbti_results()
        logger.info(f"가져온 MBTI 결과 데이터: {results}")  # 초기 데이터 로깅 추가

        # 결과를 MBTI를 키로 하는 딕셔너리로 변환
        mbti_data = {}
        for result in results:
            mbti = result["mbti"]
            # best_match와 good_match를 리스트로 변환
            best_matches = result["section_match"]["best_match"].split(", ")
            good_matches = result["section_match"]["good_match"].split(", ")

            mbti_data[mbti] = {
                "section_match": {
                    "best_match": best_matches,
                    "good_match": good_matches,
                }
            }

        logger.info(f"변환된 MBTI 매칭 데이터: {mbti_data}")  # 변환된 데이터 로깅
        return mbti_data
    except Exception as e:
        logger.error(f"MBTI 매칭 데이터 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mbti-result/{mbti}")
async def get_single_mbti_result(mbti: str):
    """특정 MBTI 결과 조회"""
    try:
        result = await get_mbti_result(mbti)
        if not result:
            raise HTTPException(status_code=404, detail="MBTI 결과를 찾을 수 없습니다")
        return result
    except Exception as e:
        logger.error(f"MBTI 결과 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/token")
async def get_token():
    """아임웹 액세스 토큰 발급"""
    try:
        access_token = await imweb_service.get_access_token()
        if not access_token:
            raise HTTPException(status_code=401, detail="토큰 발급 실패")
        # 응답 형식 수정
        return {
            "code": 200,
            "message": "success",
            "data": {
                "access_token": access_token  # 여기에 토큰을 넣어줌
            },
        }
    except Exception as e:
        logger.error(f"토큰 발급 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories():
    """아임웹 카테고리 목록 조회"""
    try:
        access_token = await imweb_service.get_access_token()
        if not access_token:
            raise HTTPException(status_code=401, detail="토큰 발급 실패")

        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/json", "access-token": access_token}
            url = f"{imweb_service.base_url}/shop/categories"

            async with session.get(url, headers=headers) as response:
                result = await response.json()
                logger.info(f"카테고리 조회 결과: {result}")
                return {"code": 200, "data": result}

    except Exception as e:
        logger.error(f"카테고리 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
