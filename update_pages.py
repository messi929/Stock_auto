"""
StockBizView - WordPress 정적 페이지 일괄 업데이트
AdSense 승인을 위한 페이지 품질 개선
- About, Contact, Privacy Policy, Disclaimer, Data Sources
"""

import json
import os
import urllib.request
import base64
import sys

# ─── 설정 ───
WP_URL = os.environ.get("WP_URL", "https://stockbizview.com")
WP_USER = os.environ.get("WP_USER", "messi929@naver.com")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "s5cW A0gL vzNU AcgS exFC OL0r")


def wp_request(endpoint, method="GET", data=None):
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


def find_page_id(slug):
    pages = wp_request(f"pages?slug={slug}&status=publish")
    if pages:
        return pages[0]["id"]
    pages = wp_request(f"pages?slug={slug}&status=draft,private")
    if pages:
        return pages[0]["id"]
    return None


def create_page(title, slug, content):
    """Create a new page if it doesn't exist."""
    result = wp_request("pages", method="POST", data={
        "title": title,
        "slug": slug,
        "content": content,
        "status": "publish",
    })
    return result["id"]


# ═══════════════════════════════════════════════════════════
# About
# ═══════════════════════════════════════════════════════════
ABOUT_HTML = """
<!-- wp:heading {"level":1} -->
<h1 class="wp-block-heading">소개</h1>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>StockBizView</strong>는 AI 기술을 활용한 글로벌 주식 시황 분석 플랫폼입니다. 한국(KOSPI·KOSDAQ)과 미국(S&amp;P 500·NASDAQ) 시장의 핵심 동향을 매일 분석하여, 투자자에게 증권사 리서치센터 수준의 시황 리포트를 무료로 제공합니다.</p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">발행자 소개</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>시그널제이 (Signal J)</strong> | StockBizView 운영자</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>현직 금융권 5년차 종사자로, 매일 증권사 리서치 리포트를 분석하고 시장을 모니터링하는 것이 일상입니다. 업무 중 느낀 한 가지 아쉬움이 있었습니다 — 기관 투자자에게는 당연하게 제공되는 수준 높은 시황 분석이, 개인 투자자에게는 너무 멀리 있다는 것.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>이 간극을 메우기 위해 StockBizView를 만들었습니다. 금융 현장에서 쌓은 시장 분석 노하우를 AI 시스템에 녹여, 글로벌 IB 수준의 분석 프레임워크를 자동화했습니다. 동시에 <strong>주식 자동매매 프로그램</strong>도 직접 개발·운영하며 퀀트 전략을 실전에 적용하고 있습니다.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>StockBizView는 그 과정에서 얻은 인사이트를 공유하는 공간입니다. AI가 데이터를 분석하고, 금융 현장의 경험이 분석 프레임워크를 설계합니다. 매일 아침 장 열리기 전, 그리고 장 마감 후 — 개인 투자자도 기관급 시황 브리핑을 받을 수 있도록 하는 것이 이 사이트의 목표입니다.</p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">미션</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Goldman Sachs, JP Morgan, Morgan Stanley 등 글로벌 IB 리서치 노트의 분석 프레임워크를 참고하여, 단순 수치 나열이 아닌 <strong>WHY → SO WHAT → WHAT TO DO</strong> 3단 논리 분석을 제공합니다.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>기관 투자자만 접할 수 있었던 수준 높은 시장 분석을 개인 투자자에게도 제공하는 것이 StockBizView의 미션입니다.</p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">제공 콘텐츠</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>StockBizView는 다음과 같은 정기 리포트를 매일 자동 발행합니다:</p>
<!-- /wp:paragraph -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>리포트</th><th>발행 시간</th><th>내용</th></tr></thead><tbody><tr><td><strong>장전 리포트</strong></td><td>매일 오전 7시</td><td>미국 시장 마감 요약, 글로벌 이슈, 오늘의 전략</td></tr><tr><td><strong>장후 리포트</strong></td><td>매일 오후 7시</td><td>한국 시장 마감 분석, 수급 동향, 내일 전망</td></tr><tr><td><strong>미국 시장 분석</strong></td><td>주 2회 (화/금)</td><td>S&amp;P 500·NASDAQ 심층 분석, 섹터별 동향</td></tr><tr><td><strong>한국 시장 분석</strong></td><td>주 2회 (월/목)</td><td>KOSPI·KOSDAQ 심층 분석, 업종별 분석</td></tr><tr><td><strong>종목 분석</strong></td><td>주 2회 (화/금)</td><td>주목할 종목 심층 분석, 밸류에이션 점검</td></tr><tr><td><strong>투자 전략</strong></td><td>주 1회 (수)</td><td>자산 배분 전략, 포트폴리오 가이드</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">AI 콘텐츠 생성 및 품질 관리</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>본 사이트의 모든 리포트는 <strong>AI(인공지능) 시스템이 자동으로 작성</strong>합니다. 운영자가 설계한 분석 프레임워크와 품질 기준에 따라 다음과 같은 프로세스로 생성됩니다:</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol class="wp-block-list">
<li><strong>데이터 수집</strong> — 공인 금융 데이터 API(Yahoo Finance, Finnhub, FRED 등)로부터 실시간 시장 데이터를 자동 수집합니다.</li>
<li><strong>AI 분석</strong> — 수집된 데이터를 기반으로 AI가 시황을 분석하고, WHY → SO WHAT → WHAT TO DO 프레임워크에 따라 리포트를 작성합니다.</li>
<li><strong>품질 검증</strong> — AI 분석 결과가 품질 기준(제목 검증, 내용 완결성, 데이터 정합성)을 통과해야만 발행됩니다. 기준 미달 시 발행이 자동 차단됩니다.</li>
<li><strong>자동 발행</strong> — 품질 검증을 통과한 리포트만 사이트에 게시됩니다.</li>
</ol>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><em>※ AI가 생성한 콘텐츠는 정보 제공 목적이며, 정확성을 보장하지 않습니다. 투자 판단은 반드시 본인의 책임 하에 이루어져야 합니다. 자세한 내용은 <a href="/disclaimer/">면책조항</a>을 참고하세요.</em></p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">데이터 출처</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>StockBizView는 신뢰할 수 있는 공인 데이터 소스만을 사용합니다. 자세한 내용은 <a href="/data-sources/">데이터 출처</a> 페이지를 참고하세요.</p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">문의</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>사이트 관련 문의는 <a href="/contact/">문의하기</a> 페이지를 이용해 주시기 바랍니다.</p>
<!-- /wp:paragraph -->
"""

# ═══════════════════════════════════════════════════════════
# Contact (Formspree 폼 포함)
# ═══════════════════════════════════════════════════════════
CONTACT_HTML = """
<!-- wp:heading {"level":1} -->
<h1 class="wp-block-heading">문의하기</h1>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>StockBizView에 대한 문의, 제안, 광고 협업, 오류 신고 등은 아래 양식이나 이메일로 연락해 주시기 바랍니다.</p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">문의 양식</h2>
<!-- /wp:heading -->

<!-- wp:html -->
<form action="https://formsubmit.co/contact@stockbizview.com" method="POST" style="max-width:600px;">
  <input type="hidden" name="_subject" value="StockBizView 문의">
  <input type="hidden" name="_captcha" value="false">
  <input type="hidden" name="_next" value="https://stockbizview.com/contact/?submitted=true">
  <input type="text" name="_honey" style="display:none">
  <div style="margin-bottom:16px;">
    <label style="display:block;margin-bottom:6px;font-weight:600;color:#e0e0e0;">이름 <span style="color:#ef4444;">*</span></label>
    <input type="text" name="name" required placeholder="홍길동"
      style="width:100%;padding:12px 16px;border:1px solid #374151;border-radius:8px;background:#1a1a2e;color:#e0e0e0;font-size:15px;"/>
  </div>
  <div style="margin-bottom:16px;">
    <label style="display:block;margin-bottom:6px;font-weight:600;color:#e0e0e0;">이메일 <span style="color:#ef4444;">*</span></label>
    <input type="email" name="email" required placeholder="example@email.com"
      style="width:100%;padding:12px 16px;border:1px solid #374151;border-radius:8px;background:#1a1a2e;color:#e0e0e0;font-size:15px;"/>
  </div>
  <div style="margin-bottom:16px;">
    <label style="display:block;margin-bottom:6px;font-weight:600;color:#e0e0e0;">문의 유형 <span style="color:#ef4444;">*</span></label>
    <select name="category" required
      style="width:100%;padding:12px 16px;border:1px solid #374151;border-radius:8px;background:#1a1a2e;color:#e0e0e0;font-size:15px;">
      <option value="">선택해 주세요</option>
      <option value="report">리포트 관련 문의</option>
      <option value="error">기술적 오류 신고</option>
      <option value="business">광고 및 협업</option>
      <option value="suggestion">기타 제안</option>
    </select>
  </div>
  <div style="margin-bottom:16px;">
    <label style="display:block;margin-bottom:6px;font-weight:600;color:#e0e0e0;">제목 <span style="color:#ef4444;">*</span></label>
    <input type="text" name="subject" required placeholder="문의 제목을 입력해 주세요"
      style="width:100%;padding:12px 16px;border:1px solid #374151;border-radius:8px;background:#1a1a2e;color:#e0e0e0;font-size:15px;"/>
  </div>
  <div style="margin-bottom:20px;">
    <label style="display:block;margin-bottom:6px;font-weight:600;color:#e0e0e0;">내용 <span style="color:#ef4444;">*</span></label>
    <textarea name="message" required rows="6" placeholder="문의 내용을 자세히 작성해 주세요"
      style="width:100%;padding:12px 16px;border:1px solid #374151;border-radius:8px;background:#1a1a2e;color:#e0e0e0;font-size:15px;resize:vertical;"></textarea>
  </div>
  <div>
    <button type="submit"
      style="padding:14px 32px;background:linear-gradient(135deg,#3b82f6,#2563eb);color:#fff;border:none;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;">
      문의 보내기
    </button>
  </div>
</form>
<!-- /wp:html -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">이메일</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>일반 문의:</strong> contact@stockbizview.com</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>광고 및 비즈니스:</strong> messi929@naver.com</p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">문의 유형 안내</h2>
<!-- /wp:heading -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>유형</th><th>설명</th><th>예시</th></tr></thead><tbody><tr><td><strong>리포트 관련</strong></td><td>시황 리포트 내용에 대한 질문, 데이터 정정 요청</td><td>"장전 리포트에서 KOSPI 수치가 다릅니다"</td></tr><tr><td><strong>기술적 오류</strong></td><td>사이트 표시 오류, 데이터 누락 등</td><td>"모바일에서 차트가 표시되지 않습니다"</td></tr><tr><td><strong>광고 및 협업</strong></td><td>광고 게재, 콘텐츠 제휴, 비즈니스 파트너십</td><td>"금융 서비스 광고 게재 문의"</td></tr><tr><td><strong>기타 제안</strong></td><td>새로운 콘텐츠 요청, 기능 제안 등</td><td>"암호화폐 분석 리포트도 추가해 주세요"</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">응답 안내</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
<li>문의 접수 후 영업일 기준 <strong>1~3일 이내</strong>에 답변드리겠습니다.</li>
<li>긴급한 사안의 경우 제목에 <strong>[긴급]</strong>을 표기해 주시면 우선 처리됩니다.</li>
<li>주말 및 공휴일에는 응답이 지연될 수 있습니다.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><em>※ 본 사이트는 투자 자문 서비스를 제공하지 않으며, 개별 종목에 대한 매수·매도 상담은 진행하지 않습니다.</em></p>
<!-- /wp:paragraph -->
"""

# ═══════════════════════════════════════════════════════════
# Privacy Policy (AdSense/YMYL 강화)
# ═══════════════════════════════════════════════════════════
PRIVACY_HTML = """
<!-- wp:heading {"level":1} -->
<h1 class="wp-block-heading">개인정보처리방침</h1>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>StockBizView(이하 "본 사이트")는 이용자의 개인정보를 소중히 여기며, 「개인정보 보호법」 및 관련 법령을 준수합니다. 본 방침은 수집하는 정보의 종류, 사용 목적, 보호 방법을 안내합니다.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>최종 수정일:</strong> 2026년 3월 18일</p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">1. 수집하는 개인정보 항목</h2>
<!-- /wp:heading -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>수집 항목</th><th>수집 목적</th><th>수집 방법</th></tr></thead><tbody><tr><td>이메일 주소</td><td>뉴스레터 발송, 문의 응답</td><td>뉴스레터 구독, 문의 양식</td></tr><tr><td>이름 (선택)</td><td>맞춤형 응대</td><td>문의 양식</td></tr><tr><td>IP 주소, 브라우저 정보</td><td>서비스 운영, 보안, 통계 분석</td><td>자동 수집</td></tr><tr><td>쿠키 및 유사 기술</td><td>사이트 이용 분석, 광고 최적화</td><td>자동 수집 (동의 기반)</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">2. 쿠키 및 추적 기술</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>본 사이트는 다음과 같은 쿠키 및 추적 기술을 사용합니다:</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">2-1. 필수 쿠키</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>사이트 기본 기능(로그인 상태 유지, 보안)에 필요한 쿠키로, 비활성화할 수 없습니다.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">2-2. 분석 쿠키 — Google Analytics</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>방문자 수, 페이지 조회수, 이용 패턴 등을 파악하기 위해 <strong>Google Analytics</strong>를 사용합니다. Google Analytics는 쿠키를 통해 익명화된 통계 데이터를 수집하며, 개인을 식별하지 않습니다.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
<li>수집 데이터: 페이지 조회수, 세션 시간, 유입 경로, 기기 정보</li>
<li>데이터 처리: Google LLC (미국) — <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">Google 개인정보처리방침</a></li>
<li>IP 익명화: 활성화됨</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">2-3. 광고 쿠키 — Google AdSense</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>본 사이트는 <strong>Google AdSense</strong>를 통해 광고를 게재하며, 이를 위해 쿠키가 사용됩니다.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
<li><strong>개인 맞춤 광고:</strong> Google은 이용자의 관심사에 기반한 광고를 표시할 수 있습니다.</li>
<li><strong>제3자 광고 네트워크:</strong> Google의 광고 파트너가 쿠키를 설정할 수 있습니다.</li>
<li><strong>광고 개인화 해제:</strong> <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener">Google 광고 설정</a>에서 개인 맞춤 광고를 비활성화할 수 있습니다.</li>
<li><strong>추가 옵트아웃:</strong> <a href="https://optout.aboutads.info/" target="_blank" rel="noopener">Digital Advertising Alliance 옵트아웃 페이지</a>를 통해 제3자 광고 쿠키를 관리할 수 있습니다.</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">2-4. 쿠키 관리 방법</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>이용자는 브라우저 설정을 통해 쿠키를 관리할 수 있습니다:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
<li><strong>Chrome:</strong> 설정 → 개인정보 및 보안 → 쿠키 및 기타 사이트 데이터</li>
<li><strong>Firefox:</strong> 설정 → 개인 정보 및 보안 → 쿠키 및 사이트 데이터</li>
<li><strong>Safari:</strong> 환경설정 → 개인 정보 보호 → 쿠키 관리</li>
<li><strong>Edge:</strong> 설정 → 쿠키 및 사이트 권한</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><em>※ 쿠키를 비활성화하면 사이트 일부 기능이 정상 작동하지 않을 수 있습니다.</em></p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">3. 개인정보 이용 목적</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
<li>뉴스레터 및 시장 리포트 발송</li>
<li>문의 접수 및 응답</li>
<li>서비스 개선을 위한 통계 분석 (익명화)</li>
<li>광고 게재 및 최적화 (Google AdSense)</li>
<li>부정 이용 방지 및 보안</li>
</ul>
<!-- /wp:list -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">4. 개인정보 보유 및 파기</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
<li><strong>뉴스레터 구독 정보:</strong> 구독 해지 요청 시 즉시 삭제</li>
<li><strong>문의 내용:</strong> 응답 완료 후 1년간 보관 후 파기</li>
<li><strong>접속 로그:</strong> 3개월간 보관 후 자동 삭제</li>
<li><strong>쿠키 데이터:</strong> 브라우저 종료 시 또는 만료일에 자동 삭제</li>
</ul>
<!-- /wp:list -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">5. 이용자의 권리</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>이용자는 언제든지 다음 권리를 행사할 수 있습니다:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
<li><strong>열람권:</strong> 수집된 개인정보의 열람을 요청할 수 있습니다.</li>
<li><strong>정정권:</strong> 부정확한 정보의 정정을 요청할 수 있습니다.</li>
<li><strong>삭제권:</strong> 개인정보의 삭제를 요청할 수 있습니다.</li>
<li><strong>처리 거부권:</strong> 개인정보 처리의 중단을 요청할 수 있습니다.</li>
<li><strong>광고 옵트아웃:</strong> 개인 맞춤 광고를 거부할 수 있습니다.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>위 권리를 행사하려면 <a href="mailto:contact@stockbizview.com">contact@stockbizview.com</a>으로 연락해 주세요. 요청 접수 후 <strong>영업일 기준 7일 이내</strong>에 처리합니다.</p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">6. 제3자 제공 및 위탁</h2>
<!-- /wp:heading -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>서비스</th><th>제공 업체</th><th>목적</th><th>처리 국가</th></tr></thead><tbody><tr><td>웹 분석</td><td>Google LLC</td><td>사이트 이용 통계</td><td>미국</td></tr><tr><td>광고</td><td>Google LLC (AdSense)</td><td>광고 게재 및 수익화</td><td>미국</td></tr><tr><td>웹 호스팅</td><td>Cloudways/Vultr</td><td>서비스 운영</td><td>한국/미국</td></tr><tr><td>문의 폼</td><td>Formspree</td><td>문의 접수 처리</td><td>미국</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">7. 개인정보 보호책임자</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
<li><strong>담당:</strong> StockBizView 운영팀</li>
<li><strong>이메일:</strong> <a href="mailto:contact@stockbizview.com">contact@stockbizview.com</a></li>
</ul>
<!-- /wp:list -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">8. 방침 변경</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>본 방침이 변경되는 경우, 사이트 내 공지를 통해 안내하며, 변경 내용은 게시 즉시 효력이 발생합니다.</p>
<!-- /wp:paragraph -->
"""

# ═══════════════════════════════════════════════════════════
# Disclaimer (YMYL 강화)
# ═══════════════════════════════════════════════════════════
DISCLAIMER_HTML = """
<!-- wp:heading {"level":1} -->
<h1 class="wp-block-heading">면책조항</h1>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>최종 수정일:</strong> 2026년 3월 18일</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>본 면책조항은 StockBizView(이하 "본 사이트")가 제공하는 모든 콘텐츠에 적용됩니다. 본 사이트를 이용하기 전에 아래 내용을 반드시 읽어주시기 바랍니다.</p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">1. 정보 제공 목적</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>본 사이트의 모든 콘텐츠(리포트, 분석, 데이터, 차트 등)는 <strong>일반적인 정보 제공 목적</strong>으로만 작성되었으며, 다음에 해당하지 않습니다:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
<li>투자 자문, 투자 권유, 또는 투자 추천</li>
<li>특정 금융 상품의 매수·매도·보유 권고</li>
<li>개인 재무 상황에 대한 맞춤형 조언</li>
<li>전문적인 금융, 법률, 세무 자문</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>투자 결정은 반드시 본인의 판단과 책임 하에 이루어져야 하며, 필요 시 공인 재무설계사, 투자상담사 등 전문가의 조언을 구하시기 바랍니다.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">2. 투자 위험 경고</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>모든 투자에는 원금 손실을 포함한 위험이 수반됩니다:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
<li><strong>시장 변동성:</strong> 주식, 채권, 원자재 등 모든 금융 자산의 가격은 예측 불가능하게 급변할 수 있습니다.</li>
<li><strong>원금 손실:</strong> 투자한 원금의 일부 또는 전부를 잃을 수 있습니다.</li>
<li><strong>레버리지 위험:</strong> 신용거래, 선물, 옵션 등 레버리지 상품은 투자금을 초과하는 손실이 발생할 수 있습니다.</li>
<li><strong>환율 위험:</strong> 해외 자산 투자 시 환율 변동으로 인한 추가 손실이 발생할 수 있습니다.</li>
<li><strong>유동성 위험:</strong> 시장 상황에 따라 원하는 시점에 매매가 불가능할 수 있습니다.</li>
<li><strong>과거 수익률:</strong> 과거의 투자 수익률이 미래의 수익을 보장하지 않습니다.</li>
</ul>
<!-- /wp:list -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">3. AI 생성 콘텐츠 고지</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>본 사이트의 리포트는 <strong>AI(인공지능) 시스템이 자동으로 생성</strong>합니다. AI 생성 콘텐츠의 특성상:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
<li>정보의 정확성, 완전성, 적시성을 보장하지 않습니다.</li>
<li>AI 모델의 한계로 인해 부정확하거나 오해의 소지가 있는 분석이 포함될 수 있습니다.</li>
<li>시장 데이터는 실시간이 아닌 <strong>지연 데이터</strong>일 수 있으며, 데이터 소스의 오류가 반영될 수 있습니다.</li>
<li>AI 분석은 인간 전문가의 판단을 대체할 수 없습니다.</li>
</ul>
<!-- /wp:list -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">4. 데이터 정확성</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>본 사이트에 표시되는 시장 데이터, 가격 정보, 통계 자료에 대해:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
<li>데이터는 제3자 API(Yahoo Finance, Finnhub 등)로부터 수집되며, 데이터 소스의 오류나 지연이 반영될 수 있습니다.</li>
<li>실시간 데이터로 표기되더라도 최대 <strong>15~30분의 지연</strong>이 있을 수 있습니다.</li>
<li>데이터 오류 발견 시 <a href="/contact/">문의하기</a> 페이지를 통해 알려주시면 신속히 수정하겠습니다.</li>
</ul>
<!-- /wp:list -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">5. 이해 상충 고지</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>운영자 및 관련자는 본 사이트에서 언급되는 증권, 금융 상품을 보유하거나 거래할 수 있습니다. 이러한 보유 또는 거래가 사이트 콘텐츠의 객관성에 영향을 줄 수 있음을 인지하시기 바랍니다.</p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">6. 책임의 한계</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>본 사이트는 다음 사항에 대해 어떠한 법적 책임도 지지 않습니다:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
<li>본 사이트 정보를 기반으로 한 투자 결정에서 발생하는 손실</li>
<li>데이터의 부정확성, 누락, 지연으로 인한 손해</li>
<li>서비스 중단, 기술적 오류로 인한 불편 또는 손해</li>
<li>제3자 링크를 통해 접근한 외부 사이트의 콘텐츠 또는 서비스</li>
<li>천재지변, 시스템 장애 등 불가항력으로 인한 서비스 중단</li>
</ul>
<!-- /wp:list -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">7. 분쟁 해결</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
<li><strong>준거법:</strong> 본 면책조항은 대한민국 법률에 따라 해석됩니다.</li>
<li><strong>관할 법원:</strong> 본 사이트 이용과 관련한 분쟁은 서울중앙지방법원을 전속 관할로 합니다.</li>
<li><strong>분쟁 해결:</strong> 분쟁 발생 시 먼저 <a href="/contact/">문의하기</a>를 통해 원만한 해결을 시도하며, 합의에 이르지 못할 경우 관할 법원에 소를 제기할 수 있습니다.</li>
</ul>
<!-- /wp:list -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">8. 외부 링크</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>본 사이트에 포함된 외부 링크는 이용자의 편의를 위해 제공되며, 해당 외부 사이트의 콘텐츠, 개인정보 처리, 보안에 대해 본 사이트는 책임지지 않습니다.</p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:paragraph -->
<p><em>본 사이트를 이용함으로써 위 면책조항에 동의한 것으로 간주됩니다. 동의하지 않는 경우, 사이트 이용을 중단해 주시기 바랍니다.</em></p>
<!-- /wp:paragraph -->
"""

# ═══════════════════════════════════════════════════════════
# Data Sources (신규 페이지)
# ═══════════════════════════════════════════════════════════
DATA_SOURCES_HTML = """
<!-- wp:heading {"level":1} -->
<h1 class="wp-block-heading">데이터 출처</h1>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>StockBizView는 신뢰할 수 있는 공인 데이터 소스로부터 시장 데이터를 수집합니다. 모든 데이터는 각 제공업체의 이용 약관에 따라 사용됩니다.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>최종 수정일:</strong> 2026년 3월 18일</p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">시장 데이터</h2>
<!-- /wp:heading -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>데이터 유형</th><th>제공업체</th><th>설명</th><th>지연</th></tr></thead><tbody><tr><td>글로벌 주가 지수</td><td>Yahoo Finance</td><td>S&amp;P 500, NASDAQ, 다우존스, KOSPI, KOSDAQ 등</td><td>최대 15분</td></tr><tr><td>개별 종목 시세</td><td>Yahoo Finance</td><td>미국 Mag7, 한국 대표주 시세 및 등락률</td><td>최대 15분</td></tr><tr><td>원자재 · 환율</td><td>Yahoo Finance</td><td>WTI 원유, 금, USD/KRW, 비트코인 등</td><td>최대 15분</td></tr><tr><td>변동성 지수</td><td>Yahoo Finance / Finnhub</td><td>VIX, 달러인덱스 등</td><td>최대 15분</td></tr><tr><td>채권 수익률</td><td>Yahoo Finance</td><td>미국 10년 국채 수익률 등</td><td>최대 15분</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">거시경제 지표</h2>
<!-- /wp:heading -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>데이터 유형</th><th>제공업체</th><th>설명</th></tr></thead><tbody><tr><td>금리 · 통화정책</td><td>미 연방준비제도 (FRED)</td><td>기준금리, FOMC 결정, 통화정책 관련 지표</td></tr><tr><td>고용 지표</td><td>미 노동부 통계청 (BLS)</td><td>비농업 고용, 실업률, 임금 상승률</td></tr><tr><td>물가 지표</td><td>미 노동부 통계청 (BLS)</td><td>CPI, PPI 등 인플레이션 관련 지표</td></tr><tr><td>경제 캘린더</td><td>Finnhub</td><td>주요 경제 이벤트 및 일정</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">한국 시장 데이터</h2>
<!-- /wp:heading -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>데이터 유형</th><th>제공업체</th><th>설명</th></tr></thead><tbody><tr><td>주가 · 거래량</td><td>한국거래소 (KRX)</td><td>KOSPI, KOSDAQ 지수 및 종목별 시세</td></tr><tr><td>투자자별 매매동향</td><td>한국거래소 (KRX)</td><td>외국인, 기관, 개인 순매수 현황</td></tr><tr><td>기업 공시</td><td>금융감독원 (DART)</td><td>분기 실적, 주요 공시 사항</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">기업 재무 데이터</h2>
<!-- /wp:heading -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>데이터 유형</th><th>제공업체</th><th>설명</th></tr></thead><tbody><tr><td>미국 기업 공시</td><td>SEC (EDGAR)</td><td>10-K, 10-Q 보고서, 분기 실적</td></tr><tr><td>어닝 캘린더</td><td>Finnhub</td><td>주요 기업 실적 발표 일정</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">데이터 갱신 주기</h2>
<!-- /wp:heading -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>항목</th><th>갱신 주기</th><th>비고</th></tr></thead><tbody><tr><td>홈페이지 시세 (티커바)</td><td>30분마다</td><td>거래 시간 외에도 갱신</td></tr><tr><td>장전 리포트</td><td>매일 07:00 KST</td><td>미국 시장 마감 후</td></tr><tr><td>장후 리포트</td><td>매일 19:00 KST</td><td>한국 시장 마감 후</td></tr><tr><td>주간 분석 리포트</td><td>주 2~5회</td><td>리포트 유형별 상이</td></tr><tr><td>마켓 캘린더</td><td>매주 월요일</td><td>주간 경제 이벤트</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">데이터 이용 관련 유의사항</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
<li>모든 시장 데이터는 <strong>정보 제공 목적</strong>으로만 제공되며, 투자 자문이 아닙니다.</li>
<li>데이터는 제3자 제공업체로부터 수집되며, <strong>정확성·완전성·적시성을 보장하지 않습니다.</strong></li>
<li>"실시간"으로 표기된 데이터도 최대 <strong>15~30분의 지연</strong>이 있을 수 있습니다.</li>
<li>데이터 오류 발견 시 <a href="/contact/">문의하기</a>를 통해 알려주시기 바랍니다.</li>
<li>투자 결정 시에는 반드시 증권사 HTS/MTS 등 <strong>공인 실시간 데이터</strong>를 확인하시기 바랍니다.</li>
</ul>
<!-- /wp:list -->
"""


# ═══════════════════════════════════════════════════════════
# 업데이트 실행
# ═══════════════════════════════════════════════════════════
PAGES = {
    "about":          ("소개",             ABOUT_HTML),
    "contact":        ("문의하기",         CONTACT_HTML),
    "privacy-policy": ("개인정보처리방침", PRIVACY_HTML),
    "disclaimer":     ("면책조항",         DISCLAIMER_HTML),
    "data-sources":   ("데이터 출처",      DATA_SOURCES_HTML),
}


def update_page(slug, title, html):
    page_id = find_page_id(slug)
    if page_id:
        print(f"[UPDATE] {slug} (ID: {page_id})")
        wp_request(f"pages/{page_id}", method="POST", data={
            "content": html,
            "status": "publish",
        })
    else:
        print(f"[CREATE] {slug}")
        page_id = create_page(title, slug, html)
    print(f"[OK] {slug} (ID: {page_id})")
    return True


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["all"]

    for slug, (title, html) in PAGES.items():
        if "all" in targets or slug in targets:
            update_page(slug, title, html)

    print("\nDone! Check:")
    for slug in PAGES:
        if "all" in targets or slug in targets:
            print(f"  https://stockbizview.com/{slug}/")
