# air-offer MVP 개발계획서 (FastAPI + PostgreSQL)

전제: [service-idea.md](service-idea.md)의 컨셉("검색엔진 최저가 vs 내 조건 실구매 최저가 비교")을 4주 안에 동작하는 MVP로 구현.

범위: 항공권 검색 → 가격 수집 → 할인 DB → 최종가격 계산 → 제휴 링크.

---

## 1. 기술 스택

| 영역 | 선택 | 비고 |
|---|---|---|
| Backend | Python 3.12 + FastAPI | 비동기 I/O로 외부 API 다중 호출에 유리 |
| DB | PostgreSQL 16 | JSONB로 조건(condition) 유연하게 저장 |
| ORM | SQLAlchemy 2.0 (async) + Alembic | 마이그레이션 관리 |
| 캐시/큐 | Redis + Celery (또는 초기엔 APScheduler) | 가격 캐싱, 프로모션 만료 배치 검증 |
| Frontend | Next.js (App Router) 또는 정적 HTML/JS | MVP는 후자로 시작해도 무방 |
| 외부 연동 | Skyscanner Partner API / Travelpayouts / Trip.com Affiliate | 계약·심사 필요, 착수 즉시 신청 |
| 인증 | 없음 (MVP는 비로그인, localStorage로 카드 선택 보존) 또는 이메일 매직링크 | 카드번호 등 민감정보는 절대 저장 안 함 |

---

## 2. 폴더 구조

```
air-offer/
├── docs/
│   ├── service-idea.md
│   └── dev-plan.md
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app 진입점
│   │   ├── core/
│   │   │   ├── config.py               # 환경설정 (pydantic Settings)
│   │   │   ├── database.py             # async engine/session
│   │   │   └── logging.py
│   │   ├── models/                     # SQLAlchemy ORM 모델
│   │   │   ├── airport.py
│   │   │   ├── airline.py
│   │   │   ├── route.py
│   │   │   ├── flight_search.py
│   │   │   ├── flight_result.py
│   │   │   ├── provider.py
│   │   │   ├── provider_price.py
│   │   │   ├── promotion.py
│   │   │   ├── promotion_rule.py
│   │   │   ├── payment_method.py
│   │   │   ├── card_company.py
│   │   │   ├── price_comparison.py
│   │   │   ├── click.py
│   │   │   └── price_alert.py
│   │   ├── schemas/                    # Pydantic 요청/응답 스키마
│   │   │   ├── search.py
│   │   │   ├── comparison.py
│   │   │   ├── promotion.py
│   │   │   └── alert.py
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   │       ├── router.py
│   │   │       ├── search.py           # POST /search, GET /search/{id}
│   │   │       ├── comparisons.py      # GET /comparisons/{search_id}
│   │   │       ├── promotions.py       # 프로모션 CRUD (내부 관리용)
│   │   │       ├── payment_methods.py  # 카드/간편결제 목록
│   │   │       ├── clicks.py           # 제휴 클릭 트래킹
│   │   │       └── alerts.py           # 가격 알림 등록/조회
│   │   ├── services/
│   │   │   ├── flight_providers/
│   │   │   │   ├── base.py             # Provider 인터페이스
│   │   │   │   ├── skyscanner.py
│   │   │   │   └── tripcom.py
│   │   │   ├── price_normalizer.py     # 동일 항공편 매칭/정규화
│   │   │   ├── discount_rule_engine.py # 핵심 Rule Engine
│   │   │   ├── affiliate.py            # 제휴 링크 생성
│   │   │   └── alert_checker.py        # 가격 알림 배치 로직
│   │   └── worker/
│   │       ├── celery_app.py
│   │       └── tasks.py                # 프로모션 재검증, 가격 알림 배치
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   ├── test_discount_rule_engine.py
│   │   ├── test_price_normalizer.py
│   │   └── test_api_search.py
│   ├── pyproject.toml
│   └── alembic.ini
├── frontend/
│   ├── app/ (또는 정적 파일)
│   │   ├── page.tsx                    # 검색 페이지
│   │   ├── results/[searchId]/page.tsx # 결과/비교 페이지
│   │   ├── settings/page.tsx           # 내 카드/간편결제 설정
│   │   └── alerts/page.tsx             # 가격 알림 관리
│   └── ...
└── docker-compose.yml                  # postgres + redis + backend
```

---

## 3. DB 스키마 (핵심 DDL)

```sql
-- 공항/항공사/노선
CREATE TABLE airports (
    code CHAR(3) PRIMARY KEY,          -- ICN, CEB ...
    name VARCHAR(100) NOT NULL,
    country VARCHAR(2) NOT NULL
);

CREATE TABLE airlines (
    code CHAR(2) PRIMARY KEY,          -- KE, OZ, 7C ...
    name VARCHAR(100) NOT NULL,
    official_site_url TEXT
);

CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    origin CHAR(3) REFERENCES airports(code),
    destination CHAR(3) REFERENCES airports(code),
    UNIQUE (origin, destination)
);

-- 검색 요청/결과
CREATE TABLE flight_searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origin CHAR(3) NOT NULL,
    destination CHAR(3) NOT NULL,
    depart_date DATE NOT NULL,
    return_date DATE,
    adults SMALLINT NOT NULL DEFAULT 1,
    children SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,   -- 'skyscanner', 'tripcom', 'ke_official'
    provider_type VARCHAR(20) NOT NULL, -- 'meta_search' | 'ota' | 'airline_official'
    affiliate_base_url TEXT
);

CREATE TABLE flight_results (
    id BIGSERIAL PRIMARY KEY,
    search_id UUID REFERENCES flight_searches(id) ON DELETE CASCADE,
    airline_code CHAR(2) REFERENCES airlines(code),
    flight_number VARCHAR(10),
    depart_at TIMESTAMPTZ,
    arrive_at TIMESTAMPTZ,
    itinerary_hash VARCHAR(64) NOT NULL, -- 동일 항공편 매칭용 정규화 키
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_flight_results_search ON flight_results(search_id);
CREATE INDEX idx_flight_results_itinerary ON flight_results(itinerary_hash);

CREATE TABLE provider_prices (
    id BIGSERIAL PRIMARY KEY,
    flight_result_id BIGINT REFERENCES flight_results(id) ON DELETE CASCADE,
    provider_id INT REFERENCES providers(id),
    base_price NUMERIC(12,0) NOT NULL,   -- 원화, 기본가 (할인 전)
    currency CHAR(3) NOT NULL DEFAULT 'KRW',
    deep_link TEXT NOT NULL,             -- 제휴 파라미터 포함 전 원본 링크
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_provider_prices_result ON provider_prices(flight_result_id);

-- 결제수단
CREATE TABLE card_companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE     -- '현대카드', '삼성카드' ...
);

CREATE TABLE payment_methods (
    id SERIAL PRIMARY KEY,
    type VARCHAR(20) NOT NULL,           -- 'card' | 'simple_pay' | 'membership'
    name VARCHAR(50) NOT NULL UNIQUE,    -- '카카오페이', '네이버페이', '현대카드' ...
    card_company_id INT REFERENCES card_companies(id)
);

-- 프로모션 (핵심 자산)
CREATE TABLE promotions (
    id SERIAL PRIMARY KEY,
    airline_code CHAR(2) REFERENCES airlines(code),
    provider_id INT REFERENCES providers(id),
    title VARCHAR(200) NOT NULL,
    source_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active/expired/pending_review
    verified_at TIMESTAMPTZ,
    verification_method VARCHAR(20),     -- 'manual' | 'user_report' | 'auto'
    confidence_score SMALLINT DEFAULT 50, -- 0~100
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE promotion_rules (
    id SERIAL PRIMARY KEY,
    promotion_id INT REFERENCES promotions(id) ON DELETE CASCADE,
    discount_type VARCHAR(10) NOT NULL,   -- 'fixed' | 'percent'
    discount_value NUMERIC(10,2) NOT NULL,
    max_discount NUMERIC(12,0),
    payment_method_id INT REFERENCES payment_methods(id), -- NULL이면 결제수단 무관
    new_member_required BOOLEAN NOT NULL DEFAULT false,
    app_only BOOLEAN NOT NULL DEFAULT false,
    minimum_amount NUMERIC(12,0),
    travel_start DATE,
    travel_end DATE,
    booking_start DATE,
    booking_end DATE,
    applicable_routes INT[] DEFAULT NULL, -- routes.id 배열, NULL이면 전체 노선
    coupon_code VARCHAR(50),
    stackable BOOLEAN NOT NULL DEFAULT false,
    stack_group VARCHAR(50)               -- 같은 그룹끼리는 상호 배타
);
CREATE INDEX idx_promo_rules_promotion ON promotion_rules(promotion_id);

-- 사용자 (비로그인 지원, 세션 기반도 가능)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_payment_preferences (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    payment_method_id INT REFERENCES payment_methods(id),
    PRIMARY KEY (user_id, payment_method_id)
);

-- 비교 결과 스냅샷 (감사/통계용)
CREATE TABLE price_comparisons (
    id BIGSERIAL PRIMARY KEY,
    search_id UUID REFERENCES flight_searches(id),
    flight_result_id BIGINT REFERENCES flight_results(id),
    provider_id INT REFERENCES providers(id),
    base_price NUMERIC(12,0) NOT NULL,
    applied_promotion_ids INT[] NOT NULL DEFAULT '{}',
    final_price NUMERIC(12,0) NOT NULL,
    is_best BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE clicks (
    id BIGSERIAL PRIMARY KEY,
    price_comparison_id BIGINT REFERENCES price_comparisons(id),
    user_id UUID REFERENCES users(id),
    clicked_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE bookings (
    id BIGSERIAL PRIMARY KEY,
    click_id BIGINT REFERENCES clicks(id),
    provider_id INT REFERENCES providers(id),
    commission_amount NUMERIC(12,0),
    confirmed_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' -- pending/confirmed/cancelled
);

CREATE TABLE price_alerts (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    origin CHAR(3) NOT NULL,
    destination CHAR(3) NOT NULL,
    depart_date DATE,
    target_price NUMERIC(12,0) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    triggered_at TIMESTAMPTZ
);
```

`applicable_routes`를 배열 대신 `promotion_rule_routes` 조인 테이블로 정규화해도 되지만, MVP에서는 단순함을 위해 배열 컬럼으로 시작.

---

## 4. REST API 명세

Base path: `/api/v1`

### 4.1 검색

`POST /search`
```json
// request
{
  "origin": "ICN",
  "destination": "CEB",
  "depart_date": "2026-11-17",
  "return_date": null,
  "adults": 2,
  "children": 2
}
// response 202
{ "search_id": "b3f1...-uuid" }
```
비동기 조회(create/poll 방식) — Skyscanner류 API가 즉시 완결 응답을 주지 않으므로 그대로 따름.

`GET /search/{search_id}/status` → `{"status": "pending" | "ready" | "failed"}`

### 4.2 비교 결과 조회

`GET /comparisons/{search_id}?payment_methods=hyundai_card,kakaopay&new_member=true`

```json
{
  "search_id": "b3f1...",
  "route": { "origin": "ICN", "destination": "CEB" },
  "results": [
    {
      "flight_result_id": 123,
      "airline": "KE",
      "flight_number": "KE631",
      "depart_at": "2026-11-17T09:35:00+09:00",
      "arrive_at": "2026-11-17T13:00:00+09:00",
      "offers": [
        {
          "provider": "skyscanner",
          "base_price": 1120000,
          "final_price": 1120000,
          "applied_promotions": [],
          "deep_link": "https://..."
        },
        {
          "provider": "ke_official",
          "base_price": 1180000,
          "final_price": 1040000,
          "applied_promotions": [
            { "id": 12, "title": "신규회원 쿠폰", "discount": -50000 },
            { "id": 15, "title": "현대카드 5%", "discount": -90000, "max_discount": 30000 }
          ],
          "deep_link": "https://...",
          "confidence": "verified_today"
        }
      ],
      "best_offer_provider": "ke_official",
      "savings_vs_market_lowest": 40000
    }
  ]
}
```

쿼리 파라미터로 결제수단/신규회원 여부를 받아 **매 요청마다 Rule Engine을 재계산**(캐시는 base_price 레벨에서만 함) — 개인화 결과이므로 저장하지 않고 즉시 계산.

### 4.3 결제수단 목록

`GET /payment-methods` → 카드사/간편결제 목록 (프론트 체크박스 렌더링용)

### 4.4 클릭/제휴

`POST /clicks`
```json
{ "price_comparison_id": 456 }
```
→ `{"redirect_url": "https://provider.com/...?aff_id=..."}` (서버가 제휴 파라미터를 부착해 리다이렉트 URL 생성)

### 4.5 프로모션 관리 (내부 어드민, 인증 필요)

- `GET /admin/promotions`
- `POST /admin/promotions`
- `PATCH /admin/promotions/{id}` (status, verified_at 갱신)
- `POST /admin/promotions/{id}/rules`

### 4.6 가격 알림

- `POST /alerts` `{origin, destination, depart_date, target_price, email}`
- `GET /alerts?email=...`
- `DELETE /alerts/{id}`

---

## 5. 할인 Rule Engine 설계

```python
# services/discount_rule_engine.py
from dataclasses import dataclass

@dataclass
class UserContext:
    payment_method_ids: set[int]
    is_new_member: bool
    booking_date: date
    travel_date: date
    route_id: int
    amount_hint: Decimal  # base_price, minimum_amount 판정용

@dataclass
class AppliedDiscount:
    rule_id: int
    promotion_title: str
    amount: Decimal
    stack_group: str | None

def is_rule_applicable(rule: PromotionRule, ctx: UserContext) -> bool:
    if rule.payment_method_id and rule.payment_method_id not in ctx.payment_method_ids:
        return False
    if rule.new_member_required and not ctx.is_new_member:
        return False
    if rule.minimum_amount and ctx.amount_hint < rule.minimum_amount:
        return False
    if rule.travel_start and not (rule.travel_start <= ctx.travel_date <= rule.travel_end):
        return False
    if rule.booking_start and not (rule.booking_start <= ctx.booking_date <= rule.booking_end):
        return False
    if rule.applicable_routes and ctx.route_id not in rule.applicable_routes:
        return False
    return True

def compute_discount_amount(rule: PromotionRule, base_price: Decimal) -> Decimal:
    if rule.discount_type == "percent":
        amount = base_price * rule.discount_value / 100
    else:
        amount = rule.discount_value
    if rule.max_discount:
        amount = min(amount, rule.max_discount)
    return amount

def best_combination(rules: list[PromotionRule], base_price: Decimal, ctx: UserContext) -> list[AppliedDiscount]:
    applicable = [r for r in rules if is_rule_applicable(r, ctx)]
    # stack_group이 있는 규칙은 그룹 내 최댓값 1개만 선택, 나머지(stackable=True, 그룹 없음)는 모두 합산
    grouped: dict[str, list[PromotionRule]] = defaultdict(list)
    standalone: list[PromotionRule] = []
    for r in applicable:
        (grouped[r.stack_group] if r.stack_group else standalone).append(r)

    chosen: list[AppliedDiscount] = []
    for r in standalone:
        chosen.append(AppliedDiscount(r.id, r.promotion.title, compute_discount_amount(r, base_price), None))
    for group, group_rules in grouped.items():
        best = max(group_rules, key=lambda r: compute_discount_amount(r, base_price))
        chosen.append(AppliedDiscount(best.id, best.promotion.title, compute_discount_amount(best, base_price), group))
    return chosen
```

핵심 설계 포인트:
- **조합 폭발 방지**: `stack_group`으로 상호 배타 규칙을 묶고, 그룹 내에서는 그리디하게 최댓값만 선택(완전 조합 탐색은 MVP에서 불필요).
- Rule Engine은 순수 함수로 만들어 단위 테스트를 촘촘히 작성(`tests/test_discount_rule_engine.py`) — 이 서비스 신뢰도의 핵심이므로 회귀 테스트 필수.
- 결과에는 항상 `applied_promotions` 상세를 반환해 "왜 이 가격이 나왔는지" 사용자에게 투명하게 보여줌.

---

## 6. 가격 정규화 / 동일 항공편 매칭

`services/price_normalizer.py`:

- `itinerary_hash = sha256(airline_code + flight_number + depart_at_iso + arrive_at_iso)`
- 여러 provider가 같은 항공편을 서로 다른 가격으로 제시할 때, 이 해시로 `flight_results` 1건에 여러 `provider_prices`를 연결.
- Provider별 응답 스키마가 다르므로 `flight_providers/base.py`에 `NormalizedFlight` 공통 DTO를 정의하고 각 provider 어댑터가 이를 반환하도록 강제.

---

## 7. 화면 설계

### 화면 1 — 검색 페이지 (`/`)
- 출발지/도착지 (공항 자동완성), 날짜, 인원(성인/아동) 입력
- "내 카드/간편결제 선택" 접이식 섹션 (localStorage에 선택값 저장, 재방문 시 자동 유지)
- 검색 버튼 → `POST /search` → `search_id`로 결과 페이지 이동

### 화면 2 — 결과/비교 페이지 (`/results/[searchId]`)
- 상단: "검색엔진 최저가 ₩X" 배너
- 카드형 리스트: 항공편별로 provider별 가격 나열, 최저가(내 조건 반영) 강조 배지 🥇
- 각 offer에 적용된 할인 내역 펼쳐보기 (신뢰도 아이콘 🟢🟡🔴 표시)
- "예약하기" 버튼 → `POST /clicks` → 반환된 `redirect_url`로 새 탭 이동
- 하단: "이 가격 이하로 떨어지면 알림받기" CTA → 알림 등록 모달

### 화면 3 — 내 카드/간편결제 설정 (`/settings`)
- 체크박스 목록 (카드사, 간편결제, 신규회원 여부)
- 저장 시 localStorage + (로그인 시) `user_payment_preferences`에 반영

### 화면 4 — 가격 알림 관리 (`/alerts`)
- 등록한 알림 목록, 활성/비활성 토글, 삭제

### 화면 5 — (내부용) 프로모션 어드민
- 프로모션/규칙 CRUD, `verified_at` 갱신 버튼, 만료 임박 목록

---

## 8. 제휴 링크 처리

`services/affiliate.py`:
- provider별 affiliate 파라미터 템플릿을 `providers.affiliate_base_url`에 저장 (예: `?aff_id={AFF_ID}&sub_id={click_id}`)
- 클릭 시점에 `click_id`를 발급해 `sub_id`로 부착 → 추후 Travelpayouts/Trip.com 리포트와 `clicks`/`bookings` 테이블을 매칭해 커미션 정산 추적
- 리다이렉트는 서버사이드 302가 아니라 클라이언트에서 `redirect_url`을 받아 이동 (클릭 로깅이 먼저 끝난 뒤 이동 보장)

---

## 9. 4주 실행 로드맵 (구체화)

| 주차 | 작업 | 산출물 |
|---|---|---|
| 1주 | DB 스키마 확정 + Alembic 마이그레이션, Skyscanner/Trip.com API 신청, 검색 API(`POST /search`, provider 어댑터 1개) + 검색 UI | 검색 → provider 원본 가격 조회 동작 |
| 2주 | 가격 정규화(`itinerary_hash`), 다중 provider 병합, `GET /comparisons` 기본형(할인 미적용), 결과 화면 | 여러 판매처 동일 항공편 병렬 비교 화면 |
| 3주 | `promotions`/`promotion_rules` 테이블 채우기(5개 항공사 초기 데이터 수동 입력), Discount Rule Engine 구현 + 단위 테스트, 내 카드 설정 화면 | 개인화된 "예상 최종가" 계산 |
| 4주 | 제휴 링크/클릭 트래킹(`clicks`), 가격 알림(`price_alerts` + Celery 배치), 신뢰도 배지, 버그 픽스/QA | 엔드투엔드 MVP: 검색→비교→클릭→알림 |

KPI 계측은 1주차부터 `price_comparisons`에 `is_best`/`savings_vs_market_lowest`를 기록해두면, 이후 "숨은 할인 발견율" 지표를 바로 집계 가능.

---

## 10. 우선순위 밖으로 미루는 것 (MVP 범위 제외)

- 로그인/회원 시스템 전체 (이메일 매직링크 정도로 최소화하거나 아예 생략)
- 자동 프로모션 크롤링 (수동 관리로 시작, v0.2에서 도입)
- 카드 발급 제휴/광고 (금융상품 광고 규제 검토 필요)
- 다국어/다통화 지원
- GDS 직접 연동
