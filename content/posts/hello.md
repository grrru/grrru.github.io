---
title: "PaperMod로 깃허브 블로그 시작하기"
date: 2025-11-20
tags: ["Hugo", "PaperMod", "GitHub Pages"]
categories: ["블로그"]
description: "grrru.github.io를 위한 Hugo + PaperMod 기본 설정과 첫 글 예제"
draft: false
---

첫 포스팅입니다. Hugo와 PaperMod 테마로 블로그를 세팅하고 GitHub Pages에 배포할 준비를 마쳤어요. 이 글은 앞으로 글을 추가하고 배포할 때 참고할 수 있는 짧은 가이드입니다.

## 이 블로그가 준비된 것

- PaperMod 테마 적용 및 홈 소개 섹션 구성
- 글 모음, 검색 메뉴 구성
- RSS 피드(`/index.xml`) 링크 추가

## 로컬에서 확인하기

Hugo 서버를 띄우면 변경 사항을 바로 확인할 수 있어요.

```bash
hugo server -D
```

서버가 실행되면 브라우저에서 `http://localhost:1313`으로 접속하세요.

## 새 글 작성하기

- 새 포스트 생성: `hugo new posts/새-글-제목.md`
- front matter의 `draft`를 `false`로 바꾸면 실제 배포에 포함됩니다.

## GitHub Pages로 배포하기

```bash
hugo -D
```

`public/` 폴더가 새로 생성되거나 갱신됩니다. 이 폴더 내용을 `grrru.github.io` 저장소의 `main` 브랜치에 올리면 GitHub Pages가 사이트를 호스팅합니다.
