---
date: 2026-01-14
draft: false
title:
categories: Linux
tags:
  - linux
  - shell
author: grrru
---

## 변수 확장
```bash
${VAR:-word} # 기본값 할당: VAR가 비어있으면 word 사용
${VAR:=word} # 기본값 대입: VAR가 비어있으면 word를 아예 저장함
${VAR:?word} # 에러 출력: VAR가 비어있으면 word를 출력하고 종료
${VAR:+word} # 대체값 사용: VAR가 있을 때만 word 사용
```

```bash
add_path_bash() {
  local mode="append"

  case "${1-}" in
    --prepend|-p) mode="prepend"; shift ;;
    --append|-a)  mode="append"; shift ;;
  esac

  [[ -z "${1-}" ]] && return 0
  local p="$1"
  [[ -d "$p" ]] || return 0

  case "::$PATH::" in
    *::"$p"::*) return 0 ;;
  esac

  if [[ "$mode" == "prepend" ]]; then
    export PATH="$p${PATH:+:$PATH}"
  else
    export PATH="${PATH:+$PATH:}$p"
  fi
}
```
