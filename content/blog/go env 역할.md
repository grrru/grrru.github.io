---
date: 2026-05-06
draft: false
title: go env 역할/ mise
categories: go
tags:
  - "go"
author: grrru
---

## GOROOT / GOPATH / GOBIN
- `GOROOT` — Go SDK 자체가 설치되는 위치.
- `GOPATH` — 작업공간 루트. 모듈 캐시(`pkg/mod`)와 `go install` 바이너리 기본 위치(`bin/`)
- `GOBIN` — `go install` 결과물 출력 경로. 미설정 시 `GOPATH/bin`으로 fallback

**go build vs go install**
- 둘 다 의존 모듈을 `GOPATH/pkg/mod`에 캐시하는 건 동일
- `go build` → 현재 디렉토리에 바이너리 생성, 원격 모듈 직접 지정 불가
- `go install` → GOBIN에 바이너리 설치, `@latest` 같은 원격 모듈 직접 지정 가능

**mise의 전략**
- `GOROOT/bin`과 `GOBIN`을 동일 경로로 설정해서 SDK 바이너리와 `go install` 결과물을 한 곳에 모음
- Go 버전 전환 시 GOBIN 경로도 함께 바뀌어 버전별 바이너리 격리가 자동으로 됨
