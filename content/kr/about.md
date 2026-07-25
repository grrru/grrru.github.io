---
title: NamSeok Kim
layout: about
role: Backend Developer
location: South Korea
locale: ko
page_language: kr
---

<section class="about-section" aria-labelledby="experience-title">
  <header class="about-section-heading">
    <h2 id="experience-title">Work Experience</h2>
  </header>
  <div class="about-timeline">
    <article class="about-entry">
      <div class="about-entry-meta">
        <p class="about-period">Jul 2025 — Present</p>
        <p class="about-location">South Korea</p>
      </div>
      <div class="about-entry-content">
        <header class="about-entry-heading">
          <div>
            <h3><a href="https://www.navercorp.com/en/main" target="_blank" rel="noopener noreferrer">NAVER ↗</a></h3>
            <p class="about-role">Lens Dev · Backend Developer</p>
          </div>
        </header>
        <ul class="about-work-list">
          <li>Smart Lens 백엔드 서비스 개발 및 운영</li>
          <li>RabbitMQ 기반 비동기 이미지 삭제 처리 흐름 구현</li>
          <li>Go의 <code>runtime/trace.FlightRecorder</code>를 활용한 운영 환경 런타임 진단 기능 구축</li>
          <li>Dependency 보안 취약점 수정 및 CI 실패 원인 분석 자동화 도구 개발</li>
        </ul>
      </div>
    </article>
    <article class="about-entry">
      <div class="about-entry-meta">
        <p class="about-period">Aug 2024 — Jun 2025</p>
        <p class="about-location">South Korea</p>
      </div>
      <div class="about-entry-content">
        <header class="about-entry-heading">
          <div>
            <h3><a href="https://www.lotteinnovate.com/" target="_blank" rel="noopener noreferrer">Lotte Innovate ↗</a></h3>
            <p class="about-role">Hotel IS Team · Backend Developer</p>
          </div>
        </header>
        <ul class="about-work-list">
          <li>호텔 식음 POS 시스템 백엔드 서비스 개발 및 운영</li>
          <li>다중 테이블 JOIN 및 단계별 집계를 포함한 MSSQL 리포트 쿼리 개발</li>
          <li>실행 계획 분석을 통한 데이터베이스·애플리케이션 계층의 대용량 리포트 처리 개선</li>
        </ul>
      </div>
    </article>
  </div>
</section>

<section class="about-section" aria-labelledby="project-title">
  <header class="about-section-heading">
    <h2 id="project-title">Projects</h2>
  </header>
  <article class="about-entry">
    <div class="about-entry-meta">
      <p class="about-period">Jun 2024 — Aug 2024</p>
    </div>
    <div class="about-entry-content">
      <header class="about-entry-heading">
        <div>
          <h3><a href="https://github.com/grrru/poppin" target="_blank" rel="noopener noreferrer">Poppin ↗</a></h3>
          <p class="about-role">SSAFY Team Project</p>
        </div>
      </header>
      <ul class="about-work-list">
        <li>한국어 Sentence-Transformer 임베딩과 코사인 유사도를 활용한 FastAPI 추천 서비스 구현 및 예약·좋아요·선호 카테고리의 가중합을 통한 사용자 프로필 벡터 구성</li>
        <li>Redis Sorted Set 기반 현장 대기열 설계 및 실시간 순위 계산, 중복 등록 방지, 상태 변경·취소, 만료, DB 동기화 처리</li>
        <li>리뷰·댓글 작성·수정·논리 삭제, 이미지 업로드, 도메인 예외 처리와 컨트롤러·서비스 테스트 구현</li>
      </ul>
    </div>
  </article>
</section>

<section class="about-section" aria-labelledby="case-studies-title">
  <header class="about-section-heading">
    <h2 id="case-studies-title">Case Studies</h2>
  </header>
  <article class="about-case-study" aria-labelledby="lotte-report-title">
    <header class="about-case-header">
      <div>
        <p class="about-case-kicker">Lotte Innovate · Performance</p>
        <h3 id="lotte-report-title">High-volume discount report</h3>
      </div>
      <p class="about-case-metric">
        <strong>~50%</strong>
        <span>faster in production</span>
      </p>
    </header>
    <dl class="about-case-story">
      <div>
        <dt>Context</dt>
        <dd>A complex report joined sales, menu, discount, and authorization data while calculating detailed rows, subtotals, and grand totals entirely in MSSQL.</dd>
      </div>
      <div>
        <dt>Approach</dt>
        <dd>Compared execution plans over approximately 580K records, identified a Table Spool regression in a CTE-based query, and moved summary aggregation to Java.</dd>
      </div>
      <div>
        <dt>Outcome</dt>
        <dd>Reduced production end-to-end response time by approximately 50%; the development benchmark improved from 155.7 seconds to 3.7 seconds.</dd>
      </div>
    </dl>
  </article>
  <article class="about-case-study" aria-labelledby="poppin-waitlist-title">
    <header class="about-case-header">
      <div>
        <p class="about-case-kicker">Poppin · Data Structure</p>
        <h3 id="poppin-waitlist-title">Redis-backed on-site waitlist</h3>
      </div>
    </header>
    <dl class="about-case-story">
      <div>
        <dt>Context</dt>
        <dd>Each pop-up store required an independent daily waitlist with duplicate-entry prevention, real-time position lookup, status changes, and persistent reservation history.</dd>
      </div>
      <div>
        <dt>Approach</dt>
        <dd>Modeled each waitlist as a Redis Sorted Set, combining reservation status and sequence number into the score. Added a secondary phone-based index, synchronized final states to MySQL at 3 a.m., and expired daily Redis data at 4 a.m.</dd>
      </div>
      <div>
        <dt>Outcome</dt>
        <dd>Supported registration, cancellation, status transitions, and live queue positions while keeping the core insertion and rank operations at O(log N) through Redis ZADD and ZRANK.</dd>
      </div>
    </dl>
  </article>
</section>

<section class="about-section" aria-labelledby="skills-title">
  <header class="about-section-heading">
    <h2 id="skills-title">Skills</h2>
  </header>
  <dl class="about-skills">
    <div>
      <dt>Languages</dt>
      <dd>Go, Python, Java, SQL</dd>
    </div>
    <div>
      <dt>Backend</dt>
      <dd>Gin, FastAPI, Spring Boot, Kubernetes</dd>
    </div>
    <div>
      <dt>Data & Messaging</dt>
      <dd>Redis, RabbitMQ</dd>
    </div>
  </dl>
</section>

<section class="about-section" aria-labelledby="certifications-title">
  <header class="about-section-heading">
    <h2 id="certifications-title">Certifications</h2>
  </header>
  <div class="about-education">
    <article class="about-education-entry">
      <div>
        <h3>건축기사</h3>
        <p>HRDKorea</p>
      </div>
      <p class="about-period">2023</p>
    </article>
    <article class="about-education-entry">
      <div>
        <h3>정보처리기사</h3>
        <p>HRDKorea</p>
      </div>
      <p class="about-period">2024</p>
    </article>
    <article class="about-education-entry">
      <div>
        <h3>SQL Developer (SQLD)</h3>
        <p>Korea Data Agency (KDATA)</p>
      </div>
      <p class="about-period">2024</p>
    </article>
  </div>
</section>

<section class="about-section" aria-labelledby="education-title">
  <header class="about-section-heading">
    <h2 id="education-title">Education</h2>
  </header>
  <div class="about-education">
    <article class="about-education-entry">
      <div>
        <h3><a href="https://www.yonsei.ac.kr/en_sc/index.do" target="_blank" rel="noopener noreferrer">Yonsei University ↗</a></h3>
        <p>B.S. in Architectural Engineering</p>
      </div>
      <p class="about-period">Mar 2018 — Feb 2024</p>
    </article>
    <article class="about-education-entry">
      <div>
        <h3><a href="https://www.ssafy.com/" target="_blank" rel="noopener noreferrer">SSAFY 11th ↗</a></h3>
        <p>SW Competency Test Professional (Level B)</p>
      </div>
      <p class="about-period">Jan 2024 — Aug 2024</p>
    </article>
  </div>
</section>
