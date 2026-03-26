"""
StockBizView - SEO 색인 문제 수정
Google Search Console '크롤링됨 - 색인 미생성' 33건 해결

실행: python fix_seo_indexing.py
  → WPCode에 붙여넣을 PHP 코드 출력
  → WordPress 관리자에서 1회만 설정하면 됨

python fix_seo_indexing.py verify
  → 적용 후 검증
"""

import json
import os
import urllib.request
import urllib.error
import base64
import sys

WP_URL = os.environ.get("WP_URL", "https://stockbizview.com")
WP_USER = os.environ.get("WP_USER", "messi929@naver.com")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "s5cW A0gL vzNU AcgS exFC OL0r")

# ═══════════════════════════════════════════════════════════
# WPCode에 붙여넣을 PHP 스니펫
# ═══════════════════════════════════════════════════════════
SEO_SNIPPET_PHP = r"""<?php
/**
 * StockBizView SEO Optimization
 * 색인 최적화: 태그/피드 noindex, robots.txt 커스텀, 사이트맵 정리
 * WPCode 스니펫으로 추가 (Auto Insert: Everywhere)
 */

// ─── 1. 태그 아카이브 noindex (Yoast 연동) ───
add_filter('wpseo_robots', function($robots) {
    if (is_tag() || is_tax('post_format')) {
        return 'noindex, follow';
    }
    return $robots;
});

// 태그 페이지에 직접 noindex 메타 태그 추가 (Yoast 미적용 시 백업)
add_action('wp_head', function() {
    if (is_tag() || is_tax('post_format')) {
        echo '<meta name="robots" content="noindex, follow">' . "\n";
    }
}, 1);

// ─── 2. 피드(RSS/Atom) noindex 처리 ───
// X-Robots-Tag HTTP 헤더
add_action('send_headers', function() {
    if (is_feed()) {
        header('X-Robots-Tag: noindex, nofollow', true);
    }
});

// ─── 3. 카테고리/태그 피드 → 301 리다이렉트 ───
add_action('template_redirect', function() {
    if (is_feed()) {
        if (is_tag()) {
            wp_redirect(get_tag_link(get_queried_object_id()), 301);
            exit;
        }
        if (is_category()) {
            wp_redirect(get_category_link(get_queried_object_id()), 301);
            exit;
        }
    }
});

// ─── 4. HTML <head>에서 불필요한 피드 링크 제거 ───
remove_action('wp_head', 'feed_links_extra', 3);

// ─── 5. robots.txt 커스텀 오버라이드 ───
add_filter('robots_txt', function($output, $public) {
    if ($public) {
        return <<<'ROBOTS'
# StockBizView robots.txt
# Updated: 2026-03-26

User-agent: *
Allow: /

# RSS/Atom 피드 차단
Disallow: /*/feed/
Disallow: /feed/
Disallow: /comments/feed/

# 태그 아카이브 차단 (thin content)
Disallow: /tag/

# WordPress 코어/관리자 차단
Disallow: /wp-includes/
Disallow: /wp-admin/

# 검색 결과/작성자 차단
Disallow: /?s=
Disallow: /search/
Disallow: /author/

# Sitemap
Sitemap: https://stockbizview.com/sitemap_index.xml
ROBOTS;
    }
    return "User-agent: *\nDisallow: /\n";
}, 10, 2);

// ─── 6. Yoast 사이트맵에서 태그 제외 ───
add_filter('wpseo_sitemap_exclude_taxonomy', function($exclude, $taxonomy) {
    if (in_array($taxonomy, ['post_tag', 'post_format'])) {
        return true;
    }
    return $exclude;
}, 10, 2);

// ─── 7. 작성자 사이트맵 비활성화 (단일 저자) ───
add_filter('wpseo_sitemap_exclude_author', '__return_true');
"""


def verify_seo_fixes():
    """배포 후 검증"""
    print("\n🔍 SEO 수정사항 검증 중...\n")

    checks = {
        "robots.txt 피드 차단": (f"{WP_URL}/robots.txt", "check_robots"),
        "태그 피드 리다이렉트": (f"{WP_URL}/tag/코스피/feed/", "check_redirect"),
        "카테고리 피드 리다이렉트": (f"{WP_URL}/category/pre-market/feed/", "check_redirect"),
        "사이트맵 접근": (f"{WP_URL}/sitemap_index.xml", "check_200"),
    }

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    results = {"pass": 0, "fail": 0}

    for name, (url, check_type) in checks.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

            if check_type == "check_robots":
                with urllib.request.urlopen(req, timeout=10) as resp:
                    body = resp.read().decode("utf-8")
                    if "/*/feed/" in body and "/tag/" in body:
                        print(f"  ✅ {name}: 피드/태그 차단 규칙 확인됨")
                        results["pass"] += 1
                    else:
                        print(f"  ❌ {name}: 차단 규칙 미적용")
                        print(f"     현재 내용: {body[:200]}")
                        results["fail"] += 1

            elif check_type == "check_redirect":
                try:
                    resp = opener.open(req, timeout=10)
                    # 200이면 리다이렉트 안 됨
                    robots_header = resp.headers.get("X-Robots-Tag", "")
                    if "noindex" in robots_header.lower():
                        print(f"  ✅ {name}: X-Robots-Tag: noindex 적용됨")
                        results["pass"] += 1
                    else:
                        print(f"  ⚠️  {name}: HTTP 200 (리다이렉트 미적용, X-Robots-Tag: {robots_header or '없음'})")
                        results["fail"] += 1
                except urllib.error.HTTPError as e:
                    if e.code == 301:
                        print(f"  ✅ {name}: 301 리다이렉트 (정상)")
                        results["pass"] += 1
                    else:
                        print(f"  ⚠️  {name}: HTTP {e.code}")
                        results["fail"] += 1

            elif check_type == "check_200":
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        print(f"  ✅ {name}: 정상 접근")
                        results["pass"] += 1
                    else:
                        print(f"  ⚠️  {name}: HTTP {resp.status}")
                        results["fail"] += 1

        except Exception as e:
            print(f"  ❌ {name}: {e}")
            results["fail"] += 1

    print(f"\n결과: {results['pass']}개 통과, {results['fail']}개 실패")
    return results["fail"] == 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "generate"

    if mode == "verify":
        verify_seo_fixes()
        sys.exit(0)

    print("=" * 60)
    print("🔧 StockBizView SEO 색인 문제 수정")
    print("=" * 60)
    print()
    print("문제: Google Search Console '크롤링됨 - 색인 미생성' 33건")
    print("  - /feed/ RSS 피드 URL (~70%)")
    print("  - /tag/ 태그 아카이브 (~15%)")
    print("  - wp-includes JS 파일 (~5%)")
    print()
    print("=" * 60)
    print("📋 적용 방법 (WordPress 관리자 1회 설정)")
    print("=" * 60)
    print()
    print("1. WordPress 관리자 → WPCode → + 스니펫 추가")
    print("2. '사용자 정의 스니펫 추가' 클릭")
    print("3. 코드 유형: PHP Snippet")
    print("4. 제목: StockBizView SEO Optimization")
    print("5. 아래 코드를 붙여넣기 (<?php 제외)")
    print("6. 삽입 방법: 자동 삽입 → 모든 곳에서 실행")
    print("7. 활성화 후 저장")
    print()
    print("=" * 60)
    print("📄 PHP 코드 (아래를 복사하세요)")
    print("=" * 60)
    # WPCode에는 <?php 태그 없이 붙여넣기
    code = SEO_SNIPPET_PHP.strip()
    if code.startswith("<?php"):
        code = code[5:].strip()
    print(code)
    print()
    print("=" * 60)
    print("✅ 적용 후 확인사항")
    print("=" * 60)
    print()
    print("1. robots.txt 확인: https://stockbizview.com/robots.txt")
    print("2. 태그 피드 리다이렉트: https://stockbizview.com/tag/코스피/feed/")
    print("   → 해당 태그 페이지로 301 리다이렉트 되어야 함")
    print("3. Google Search Console → 설정 → robots.txt → 새 robots.txt 확인")
    print("4. Google Search Console → 사이트맵 → sitemap_index.xml 재제출")
    print()
    print("자동 검증:")
    print("  python fix_seo_indexing.py verify")
