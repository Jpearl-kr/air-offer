# 항공권 실구매가 비교 서비스 — 아이디어 및 MVP 설계

출처: [ChatGPT 대화 공유 링크](https://chatgpt.com/share/6aa68b09-eb68-83ee-8f6e-075dd3b0aeed) (2026-09-13 저장)

## 핵심 컨셉

단순 "항공권 최저가 검색" 서비스가 아니라,

> "검색엔진에서 보이는 최저가 vs 항공사 공식 홈페이지에서 각종 할인까지 적용한 실제 결제 최저가"를 비교해주는 서비스

기존 스카이스캐너와 경쟁하는 게 아니라 **보완하는 서비스**로 포지셔닝.

- Skyscanner: "시장에서 가장 싼 가격"
- 이 서비스: "내 조건(카드/쿠폰/간편결제)에서 실제로 가장 싼 가격"

장기적으로는 Flight Search Engine이 아니라 **Flight Purchase Optimization Engine**(여행 결제 최적화 엔진)으로 확장.

## 예시 시나리오

인천 → 세부, 11월 17일, 성인 2 + 아동 2 검색 시:

| 구분 | 표시 가격 |
|---|---|
| Skyscanner 최저가 | 1,120,000원 |
| Trip.com 최저가 | 1,105,000원 |
| 항공사 공식 홈페이지 | 1,180,000원 |
| 신규회원 쿠폰 | -50,000원 |
| 카카오페이 할인 | -30,000원 |
| 특정 카드 할인 | -40,000원 |
| **실제 최종가** | **1,060,000원** |

→ "🔥 공식 홈페이지에서 결제하면 45,000원 더 저렴합니다."

## 가장 어려운 부분

- 항공권 기본 가격(Skyscanner API 등)은 상대적으로 쉬움 — 1,200개 이상 공급 파트너 데이터 제공.
- 항공사 공식 홈페이지의 결제수단별/카드사별 할인은 API로 제공되지 않음 → **별도의 프로모션 엔진이 필요**.
- API 계약/사용조건 주의: 예) Travelpayouts Search API는 다른 메타검색 API와의 결합을 제한. Skyscanner Live Prices API도 실제 예약 연결 용도라 단순 가격 DB로만 쓰기엔 제약 있음.

## 데이터 출처 4단계

1. **항공편 기본 데이터**: Skyscanner Flights API, Amadeus, Travelpayouts/Aviasales, GDS, 항공사 직접 API/NDC 등. MVP에서는 GDS 직접 구축 지양.
2. **제휴 판매**: Travelpayouts 등 affiliate network.
3. **Trip.com**: affiliate/partner 프로그램 활용.
4. **공식 항공사 할인**: 초기엔 무리한 자동 크롤링 대신 핵심 항공사만 직접 제휴/합법적 연동.

## 할인 DB (핵심 자산/moat)

`promotion_rules` 테이블 필드 예:

```
id, provider, airline, promotion_type, discount_type, discount_value, max_discount,
payment_method, card_company, card_type, new_member_required, app_only,
minimum_amount, travel_start, travel_end, booking_start, booking_end,
coupon_code, stackable, source_url, verified_at, confidence, status
```

### 할인정보 수집처
1. 공식 홈페이지 (신뢰도 최고)
2. 카드사 (신한/삼성/현대/KB국민/롯데/우리/하나/NH농협)
3. 간편결제 (카카오페이/네이버페이/토스페이/삼성페이)
4. 사용자 제보 → 검증 대기 → 직원/자동 검증 → DB 반영

### 주의사항
- "자동 할인 적용"을 섣불리 하면 안 됨 — 할인마다 조건(신규회원+앱결제+최소금액+노선+기간+선착순 등)이 다르므로 조건을 구조화해서 저장해야 함.
- 할인 간 중복 적용 가능 여부(`stackable`)를 반드시 관리.

## 할인 Rule Engine

`DiscountRule` 객체로 조건과 중복 가능 여부를 관리. 예:

- Rule 1: 신규회원 쿠폰 — 조건: 신규회원 / 할인: 50,000 / 중복 가능
- Rule 2: 카카오페이 — 조건: 카카오페이 / 할인: 30,000 / 중복 불가능
- Rule 3: 현대카드 — 조건: 현대카드 / 할인: 20,000 / 중복 가능

엔진이 사용자 조건에 맞는 가능한 조합을 계산해 최종 예상가를 산출.

## 사용자 입력 (민감정보 없음)

카드번호 등 결제정보는 절대 받지 않음. 단순 체크박스:

- 보유 카드: 현대카드 / 삼성카드 / 신한카드 / KB국민카드 / 롯데카드 등
- 간편결제: 카카오페이 / 네이버페이 등
- 회원 상태: 해당 항공사 신규회원 여부

## 신뢰도 표시

- 🟢 확인됨 (오늘 확인)
- 🟡 최근 확인 (3일 전)
- 🔴 확인 필요 (7일 이상 경과)

DB 필드: `verified_at`, `verification_method`, `confidence_score`

가격 표시도 "확정 가격"이 아니라 "예상 최종 결제금액 약 X원 — 예약 직전 공식 결제화면에서 최종 금액을 확인하세요"로 안전하게 표기.

## 기술 스택 제안

- Backend: Python + FastAPI, PostgreSQL, Redis, Celery
- Frontend: Next.js (또는 초기엔 HTML/CSS/JS)

## DB 테이블 (최소)

```
airports, airlines, routes, flight_searches, flight_results
providers, provider_prices
promotions, promotion_rules
payment_methods, card_companies
users, user_payment_preferences
price_comparisons, clicks, bookings
```

## 수익 모델

1. **Affiliate**: 예약하기 클릭 → 제휴 링크 → Trip.com/OTA/항공사 → 예약 → Commission (Travelpayouts, Skyscanner 파트너 트래픽 커미션 구조 활용)
2. **프리미엄 구독**: 무료(월 10회 검색) vs 프리미엄(월 3,900원, 무제한 검색/가격 하락 알림/카드별 최저가/쿠폰 자동 적용)
3. **가격 알림**: 목표가 이하로 내려가면 알림 → 재방문 유도
4. **카드/결제 제휴**: 카드 발급 연결 (단, 금융상품 광고 규제 검토 필요 — MVP에서는 우선순위 낮춤)

## MVP 범위 (좁게 시작)

- 노선: 한국 출발 → 일본/동남아 주요 노선 (인천-도쿄/오사카/후쿠오카/방콕/다낭/세부/괌 등)
- 항공사: 5~10개 (대한항공/아시아나/제주항공/진에어/티웨이/에어부산 등)
- OTA: 주요 2~3개

## 버전 로드맵

- **v0.1**: 항공권 API + 수동 관리 할인 DB + 최종가격 계산 + 제휴 링크
- **v0.2**: + 자동 프로모션 수집 + 할인 Rule Engine
- **v0.3**: + 사용자 카드/결제수단 → 개인별 최저가
- **v1.0**: + 가격 추적/하락 알림 + 쿠폰 알림 + Affiliate + 프리미엄

## 4주 MVP 로드맵

| 주차 | 개발 내용 |
|---|---|
| 1주 | 항공권 검색 API + 검색 UI |
| 2주 | 항공사/OTA 가격 정규화 + 결과 화면 |
| 3주 | 쿠폰·카드·간편결제 할인 DB + Rule Engine |
| 4주 | Affiliate 링크 + 가격 비교 + 알림 |

## 핵심 KPI

매출보다 먼저: **"검색 결과 중 몇 %에서 기존 최저가보다 더 싼 실구매 방법을 발견했는가?"**

예: 1,000번 검색 중 320번에서 "숨은 할인으로 추가 절약"을 찾으면 강력한 상품성. 20번 수준이면 할인 DB를 키워도 사용자 가치가 약함.

## 진짜 핵심 기술 (요약)

항공권 API 자체가 핵심이 아니라:

1. 여러 판매처의 동일 항공편을 정확히 매칭
2. 할인 조건을 구조화
3. 할인 중복 여부 판단
4. 사용자 결제수단에 맞춰
5. "실제로 살 수 있는 가격"을 계산

---

## 후속: FastAPI + PostgreSQL 개발계획서

위 대화에서 이어서, 실제 개발 가능한 수준의 폴더 구조·DB 스키마·REST API 명세·화면 설계·할인 Rule Engine·제휴 링크·4주 MVP 로드맵을 다루는 별도 작업이 ChatGPT에서 생성됨 (해당 공유 링크에는 상세 내용이 포함되어 있지 않고, "새 Work 작업으로 넘겼다"는 안내만 존재 — 필요 시 원본 ChatGPT 대화에서 후속 작업 내용을 별도로 확인해야 함).
