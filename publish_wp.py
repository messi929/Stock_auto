"""
StockBizView - WordPress 발행 모듈
생성된 리포트를 WordPress REST API로 발행
"""

import json
import os
import re
import urllib.request
import urllib.parse
import base64
import datetime
import sys
import io

# 한국 시간대 (KST = UTC+9)
KST = datetime.timezone(datetime.timedelta(hours=9))

# WordPress 설정
WP_URL = os.environ.get("WP_URL", "https://stockbizview.com")
WP_USER = os.environ.get("WP_USER", "messi929@naver.com")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "s5cW A0gL vzNU AcgS exFC OL0r")

# 카테고리 매핑
# 카테고리 매핑: 주 카테고리(해당 메뉴)에만 발행
# 데일리 리포트(28)는 전체보기용 — 장전/장후에 모두 포함되므로 개별 카테고리만 지정
CATEGORIES = {
    "pre_market": [2],          # 장전 리포트
    "post_market": [3],         # 장후 리포트
    "korea_market": [6],        # 한국 시장
    "us_market": [7],           # 미국 시장
    "stock_analysis": [4],      # 종목 분석
    "investment_strategy": [5], # 투자 전략
}

# SEO 태그
TAGS_MAP = {
    "pre_market": ["장전리포트", "주식시황", "미국증시", "투자전략", "StockBizView"],
    "post_market": ["장후리포트", "코스피", "코스닥", "한국증시", "StockBizView"],
    "korea_market": ["한국시장", "코스피", "코스닥", "업종분석", "수급동향", "StockBizView"],
    "us_market": ["미국시장", "나스닥", "S&P500", "Mag7", "월가", "StockBizView"],
    "stock_analysis": ["종목분석", "주식분석", "기업분석", "투자아이디어", "StockBizView"],
    "investment_strategy": ["투자전략", "포트폴리오", "자산배분", "리스크관리", "StockBizView"],
}


def wp_request(endpoint, method="GET", data=None):
    """WordPress REST API 요청"""
    url = f"{WP_URL}/wp-json/wp/v2/{endpoint}"
    auth = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()

    if data:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
    else:
        req = urllib.request.Request(url, method=method)

    req.add_header("Authorization", f"Basic {auth}")

    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_or_create_tags(tag_names):
    """태그 ID 목록을 가져오거나 새로 생성"""
    tag_ids = []
    for name in tag_names:
        # 기존 태그 검색
        try:
            encoded_name = urllib.parse.quote(name)
            existing = wp_request(f"tags?search={encoded_name}&per_page=10")
            found = [t for t in existing if t["name"].lower() == name.lower()]
            if found:
                tag_ids.append(found[0]["id"])
                continue
        except Exception:
            pass

        # 새 태그 생성
        try:
            new_tag = wp_request("tags", method="POST", data={"name": name})
            tag_ids.append(new_tag["id"])
        except Exception:
            # slug로 재검색 (이미 존재하는 경우)
            try:
                import re
                slug = re.sub(r'[^a-z0-9가-힣]', '-', name.lower()).strip('-')
                existing = wp_request(f"tags?slug={slug}&per_page=5")
                if existing:
                    tag_ids.append(existing[0]["id"])
            except Exception:
                pass

    return tag_ids


def check_today_published(report_type):
    """오늘 같은 report_type이 이미 WordPress에 발행됐는지 확인"""
    categories = CATEGORIES.get(report_type, [])
    if not categories:
        return None

    now = datetime.datetime.now(KST)
    # WordPress는 Asia/Seoul 타임존 — 오늘 날짜 범위로 검색
    today_start = now.strftime("%Y-%m-%dT00:00:00")

    try:
        cat_param = ",".join(str(c) for c in categories)
        posts = wp_request(
            f"posts?categories={cat_param}&after={today_start}"
            f"&status=publish,draft&per_page=5&orderby=date&order=desc"
        )
        if posts:
            return {
                "post_id": posts[0]["id"],
                "title": posts[0]["title"]["rendered"],
                "url": posts[0]["link"],
                "date": posts[0]["date"],
            }
    except Exception as e:
        print(f"  ❌ WordPress 중복 체크 실패 — 안전을 위해 발행 차단: {e}")
        return {"error": True, "reason": str(e)}

    return None


def purge_cache(report_type=None):
    """Cloudways 캐시 퍼지 (Varnish + Breeze + Cloudways API)"""
    purge_urls = [
        f"{WP_URL}/",
        f"{WP_URL}/category/pre-market/",
        f"{WP_URL}/category/post-market/",
        f"{WP_URL}/category/korea-market/",
        f"{WP_URL}/category/us-market/",
        f"{WP_URL}/category/stock-analysis/",
        f"{WP_URL}/category/investment-strategy/",
        f"{WP_URL}/category/daily-report/",
    ]

    purged = 0

    # 1) Varnish PURGE/BAN
    for url in purge_urls:
        for method in ["PURGE", "BAN"]:
            try:
                req = urllib.request.Request(url, method=method, headers={"User-Agent": "Mozilla/5.0"})
                urllib.request.urlopen(req, timeout=5)
                purged += 1
            except Exception:
                pass

    # 2) Cloudways API 캐시 퍼지 (환경변수 설정 시)
    cw_email = os.environ.get("CLOUDWAYS_EMAIL", "")
    cw_api_key = os.environ.get("CLOUDWAYS_API_KEY", "")
    cw_server_id = os.environ.get("CLOUDWAYS_SERVER_ID", "")
    cw_app_id = os.environ.get("CLOUDWAYS_APP_ID", "")

    if cw_email and cw_api_key and cw_server_id and cw_app_id:
        try:
            # Cloudways API: Get OAuth token
            token_data = json.dumps({"email": cw_email, "api_key": cw_api_key}).encode("utf-8")
            token_req = urllib.request.Request(
                "https://api.cloudways.com/api/v1/oauth/access_token",
                data=token_data, method="POST",
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(token_req, timeout=15) as resp:
                token = json.loads(resp.read().decode("utf-8"))["access_token"]

            # Purge Varnish
            purge_data = json.dumps({
                "server_id": cw_server_id,
                "app_id": cw_app_id
            }).encode("utf-8")
            purge_req = urllib.request.Request(
                "https://api.cloudways.com/api/v1/service/varnish",
                data=purge_data, method="DELETE",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )
            urllib.request.urlopen(purge_req, timeout=15)
            purged += 1
            print("  ✅ Cloudways Varnish 캐시 퍼지 완료")
        except Exception as e:
            print(f"  ⚠️ Cloudways API 퍼지 실패: {e}")

    # 3) WordPress REST API로 archive 템플릿 터치 (캐시 무효화 유도)
    try:
        auth = base64.b64encode(f"{WP_USER}:{WP_APP_PASSWORD}".encode()).decode()
        req = urllib.request.Request(
            f"{WP_URL}/wp-json/wp/v2/templates?per_page=50", method="GET",
            headers={"Authorization": f"Basic {auth}"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            templates = json.loads(resp.read().decode("utf-8"))

        import datetime
        ts = datetime.datetime.now(KST).isoformat()
        for t in templates:
            if t["slug"] in ("archive", "home"):
                content = t["content"]["raw"]
                # 기존 cache-bust 코멘트 교체
                import re
                content = re.sub(r'\n<!-- cache-bust: [^>]+ -->', '', content)
                content += f'\n<!-- cache-bust: {ts} -->'
                update_data = json.dumps({"content": content}).encode("utf-8")
                update_req = urllib.request.Request(
                    f"{WP_URL}/wp-json/wp/v2/templates/{t['id']}",
                    data=update_data, method="POST",
                    headers={
                        "Authorization": f"Basic {auth}",
                        "Content-Type": "application/json"
                    }
                )
                urllib.request.urlopen(update_req, timeout=15)
                purged += 1
    except Exception:
        pass

    print(f"  🔄 캐시 퍼지: {purged}건 처리")
    return purged


def _build_seo_slug(report_type, date_str):
    """SEO 친화적 짧은 슬러그 생성 (예: pre-market-2026-03-19)"""
    slug_prefix = {
        "pre_market": "pre-market",
        "post_market": "post-market",
        "us_market": "us-market",
        "stock_analysis": "stock-analysis",
        "investment_strategy": "investment-strategy",
        "korea_market": "korea-market",
    }
    prefix = slug_prefix.get(report_type, report_type.replace("_", "-"))
    return f"{prefix}-{date_str}"


def _build_meta_description(report_type, headline, date_str):
    """Yoast SEO meta description 생성 (120~155자 목표)"""
    type_label = {
        "pre_market": "장전 브리핑",
        "post_market": "장후 리뷰",
        "us_market": "미국 시장 분석",
        "stock_analysis": "종목 심층 분석",
        "investment_strategy": "주간 투자 전략",
        "korea_market": "한국 시장 심층 분석",
    }
    label = type_label.get(report_type, "시장 리포트")
    # headline에서 핵심 내용 추출 (60자 이내)
    short_headline = headline[:60] if headline else ""
    desc = f"[{date_str} {label}] {short_headline} — AI 애널리스트의 데이터 기반 투자 인사이트 | StockBizView"
    return desc[:160]


def _set_yoast_meta(post_id, meta_description, schema_type="NewsArticle"):
    """발행 후 Yoast SEO 메타 필드 업데이트"""
    try:
        # Yoast meta description
        yoast_data = {
            "meta": {
                "_yoast_wpseo_metadesc": meta_description,
            }
        }
        wp_request(f"posts/{post_id}", method="POST", data=yoast_data)
        print(f"  🔍 SEO meta description 설정 완료")
    except Exception as e:
        print(f"  ⚠️ Yoast 메타 설정 실패 (계속 진행): {e}")


def publish_report(title, html_content, report_type="pre_market", status="draft",
                   headline="", analysis=None):
    """WordPress에 리포트 발행"""
    print(f"\n🚀 WordPress 발행 시작...")
    print(f"  제목: {title}")
    print(f"  유형: {report_type}")
    print(f"  상태: {status}")

    # 카테고리
    categories = CATEGORIES.get(report_type, [28])

    # 태그
    tag_names = TAGS_MAP.get(report_type, ["StockBizView"])
    print(f"  태그 처리 중: {tag_names}")
    tag_ids = get_or_create_tags(tag_names)

    # SEO excerpt (검색 결과 미리보기)
    now = datetime.datetime.now(KST)
    date_str = now.strftime("%Y.%m.%d")
    excerpt_map = {
        "pre_market": "장전 브리핑 — 오늘 시장을 움직일 글로벌 시그널을 짚어드립니다.",
        "post_market": "장후 리뷰 — 오늘 시장의 승자와 패자, 수급 흐름을 분석합니다.",
        "us_market": "미국 시장 — 월가 핵심 동향과 한국 투자자 시사점을 정리합니다.",
        "stock_analysis": "종목 분석 — 주목할 종목의 밸류에이션과 투자 전략을 제시합니다.",
        "investment_strategy": "투자 전략 — 자산배분과 포트폴리오 포지셔닝을 안내합니다.",
        "korea_market": "한국 시장 — KOSPI·KOSDAQ 심층 분석과 섹터별 전략을 제공합니다.",
    }
    excerpt = f"StockBizView {date_str} {excerpt_map.get(report_type, '시황 리포트 — 주요 지수, 종목, 원자재 동향을 한눈에 확인하세요.')}"

    # SEO 슬러그 (짧고 깔끔한 URL)
    slug = _build_seo_slug(report_type, now.strftime("%Y-%m-%d"))
    print(f"  🔗 SEO slug: {slug}")

    # 포스트 데이터 (date: KST — WordPress timezone이 Asia/Seoul이므로 자동 변환)
    post_data = {
        "title": title,
        "content": html_content,
        "status": status,
        "slug": slug,
        "date": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "categories": categories,
        "tags": tag_ids,
        "excerpt": excerpt,
        "comment_status": "closed",
        "ping_status": "closed",
    }

    try:
        result = wp_request("posts", method="POST", data=post_data)
        post_id = result["id"]
        post_url = result["link"]
        print(f"\n  ✅ 발행 성공!")
        print(f"  📌 Post ID: {post_id}")
        print(f"  🔗 URL: {post_url}")
        print(f"  📂 카테고리: {categories}")
        print(f"  🏷️ 태그: {tag_ids}")
        print(f"  📊 상태: {status}")

        # Yoast SEO 메타 설정
        meta_desc = _build_meta_description(report_type, headline, date_str)
        _set_yoast_meta(post_id, meta_desc)

        # 캐시 퍼지 (카테고리 페이지 갱신)
        purge_cache(report_type)

        return {"id": post_id, "url": post_url, "status": status}
    except Exception as e:
        print(f"\n  ❌ 발행 실패: {e}")
        return None


if __name__ == "__main__":
    # 테스트: 리포트 생성 후 발행
    report_type = sys.argv[1] if len(sys.argv) > 1 else "pre_market"
    status = sys.argv[2] if len(sys.argv) > 2 else "draft"

    from generate_report import generate_report, load_data

    layout_map = {"pre_market": "pre", "post_market": "post", "us_market": "pre",
                  "stock_analysis": "post", "investment_strategy": "pre", "korea_market": "post"}
    data = load_data()
    title, html = generate_report(data, layout_map.get(report_type, "post"))

    result = publish_report(title, html, report_type=report_type, status=status)

    if result:
        print(f"\n{'='*50}")
        print(f"  발행 완료: {result['url']}")
        print(f"  상태: {result['status']}")
        if status == "draft":
            print(f"  💡 draft 상태입니다. 확인 후 publish로 변경하세요.")
        print(f"{'='*50}")
