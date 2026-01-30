---
date: 2026-01-30
draft: false
title: JSON RPC
categories: backend
tags: 
  - JSON
  - RPC
  - JSON RPC
author: grrru
---

## JSON
Javascript Object Notation의 약자로, `key-value` 쌍의 집합.

```json
{
  "이름": "홍길동",
  "나이": 25,
  "성별": "남성",
  "직업": "학생",
  "취미": ["독서", "영화", "운동"]
}
```

JSON은 구문이 간결하고 XML보다 빠르게 파싱된다.

---

## JSON RPC
`RPC`는 Remote Procedure Call의 약자로, 별도의 원격 제어 코딩 없이 네트워크로 연결된 다른 컴퓨터의 프로그램(함수/프로시저)를 로컬 함수처럼 호출하는 통신 기술이다.  

### JSON RPC 동작 구조
- 클라이언트는 JSON 형태의 메시지를 생성하고 서버로 전송한다.
- 서버는 메시지를 처리하고 결과를 다시 JSON 형태의 메시지로 만들어 클라이언트에 전달한다.

### JSON RPC 구성 요소

1. 요청
- `jsonrpc`: 버전 (e.g. "2.0")
- `method`: 실행할 원격 프로시저명
- `params`: 함수에 전달할 매개변수
- `id`: 클라이언트가 설정한 고유 식별자

1. 응답
- `jsonrpc`: 버전 (e.g. "2.0")
- `result`: 결과 데이터
- `error`: 메소드 실패 시 에러 객체
- `id`: 요청 객체와 동일한 식별자

---

## JSON RPC 장점
간단하고 직관적이며 언어 독립적이고 네트워크 통신에 효율적이며 확장성이 높고 에러 처리가 용이하다.

---

## Reference
- [# JSON RPC란 무엇인가?](https://lab.wallarm.com/what/json-rpc%EB%9E%80-%EB%AC%B4%EC%97%87%EC%9D%B8%EA%B0%80/?lang=ko)

---