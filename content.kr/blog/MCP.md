---
date: 2026-03-03
draft: false
title: MCP (Model Context Protocol)
categories: mcp
tags:
  - mcp
author: claude-4.6-opus
---
## 들어가며

2022년 말 ChatGPT가 세상에 등장했을 때, 사람들은 AI가 마치 사람처럼 대화할 수 있다는 사실에 놀랐다. 하지만 곧 한계가 드러났다. LLM(Large Language Model)은 본질적으로 **텍스트를 생성하는 모델**일 뿐이었다. 최신 날씨를 알 수 없고, 데이터베이스를 조회할 수 없으며, 이메일을 보낼 수도 없었다. 학습 데이터의 시점에 갇힌, 똑똑하지만 고립된 존재였다.

이 글은 LLM이 외부 세계와 연결되기 위해 거쳐 온 여정을 다룬다. Function Calling의 등장, AI Agent와 Tools 생태계의 폭발, 그리고 마침내 등장한 **MCP(Model Context Protocol)** 까지. 이 흐름을 이해하면, MCP가 단순한 새 기술이 아니라 필연적인 귀결이었음을 알 수 있다.

## 1. LLM의 한계

ChatGPT(GPT-3.5 기반)가 2022년 11월에 공개되었을 때, 세계는 열광했다. 자연어로 코드를 작성하고, 에세이를 쓰고, 복잡한 개념을 설명하는 능력은 놀라웠다. 하지만 한계는 있었다.

```text
사용자: "오늘 서울 날씨 알려줘"
ChatGPT: "죄송합니다. 저는 실시간 정보에 접근할 수 없습니다. 2021년 9월까지의 학습 데이터만 보유하고 있습니다."
```

LLM의 한계는 명확했다:

- **실시간 데이터 접근 불가**: 학습 시점 이후의 정보를 알 수 없다.
- **외부 시스템 연동 불가**: API를 호출하거나, 데이터베이스를 조회하거나, 파일을 읽을 수 없다.
- **행동(Action) 수행 불가**: 이메일 전송, 일정 등록, 코드 실행 등 실제 작업을 할 수 없다.

LLM은 아무리 똑똑해도, **세상과 단절된 뇌**에 불과했다. 이 모델에 "손과 발"을 달아주는 것이 2023년부터 시작된 흐름이다.

## 2. Function Calling의 등장

### Function Calling이란

2023년 6월 13일, OpenAI는 GPT-3.5와 GPT-4 API에 **Function Calling** 기능을 추가했다. 이것은 LLM과 외부 도구를 연결하는 방식에 있어 패러다임 전환이었다.  
핵심 아이디어는 단순했다. LLM이 직접 함수를 실행하는 것이 아니라, "이 함수를 이런 인자로 호출해달라"고 구조화된 형태로 요청하는 것이다.

```text
[1단계] 개발자가 사용 가능한 함수 목록을 JSON Schema로 정의하여 API에 전달

{
  "name": "get_weather",
  "description": "주어진 도시의 현재 날씨를 조회합니다",
  "parameters": {
    "type": "object",
    "properties": {
      "city": { "type": "string", "description": "도시 이름" }
    },
    "required": ["city"]
  }
}

[2단계] 사용자가 "서울 날씨 알려줘"라고 말하면,
        LLM이 대화 맥락을 분석하여 적절한 함수 호출을 결정

[3단계] LLM이 구조화된 JSON으로 응답
{
  "function_call": {
    "name": "get_weather",
    "arguments": "{\"city\": \"서울\"}"
  }
}

[4단계] 애플리케이션이 실제 함수를 실행하고,
        결과를 다시 LLM에게 전달

[5단계] LLM이 함수 실행 결과를 자연어로 변환하여 사용자에게 응답
        → "서울의 현재 기온은 15°C이고, 맑은 날씨입니다."
```

LLM은 **의사결정자** 역할만 하고, 실제 실행은 애플리케이션이 담당한다. 이렇게 함으로써:

- LLM이 직접 외부 시스템에 접근하는 보안 리스크를 줄였다.
- 개발자가 실행 로직을 완전히 제어할 수 있게 되었다.
- 구조화된 JSON 출력으로 파싱 오류를 크게 줄였다.

### 한계

하지만 Function Calling에도 분명한 한계가 있었다:

- **플랫폼 종속**: OpenAI API에서 정의한 형식이었다. Anthropic Claude, Google Gemini 등은 각자 다른 형식을 사용했다.
- **정적 정의**: 사용할 함수 목록을 미리 코드에 하드코딩해야 했다. 런타임에 동적으로 도구를 발견할 수 없었다.
- **실행 로직의 중복**: 같은 기능(예: GitHub 이슈 조회)을 10개의 다른 AI 앱에서 쓰려면, 10번 각각 구현해야 했다.

## 3. AI Agent의 시대 - Tools, 그리고 Skills

### Agent 패러다임의 폭발

Function Calling이 "LLM에 도구를 연결하는 방법"을 제시하자, 더 큰 꿈이 싹텄다. **AI Agent** — LLM이 스스로 계획을 세우고, 도구를 사용하며, 목표를 달성하는 자율적 시스템이다.  
2023년, `AutoGPT`와 `BabyAGI` 같은 프로젝트가 등장하며 AI Agent의 가능성을 보여주었다. "항공편을 검색하고, 호텔을 예약하고, 일정에 등록해줘"와 같은 복합 작업을 LLM이 단계별로 수행하는 비전이었다.

### Tools: Agent의 도구 상자

Agent 프레임워크에서 **Tool**은 핵심 개념이다. Agent가 외부 세계와 상호작용하기 위해 사용하는 **모든 기능 단위**를 통칭한다.  
LangChain이 이 패턴을 대중화했다:

```python
from langchain.tools import Tool

search_tool = Tool(
    name="web_search",
    description="인터넷에서 최신 정보를 검색합니다",
    func=search_function
)

calculator_tool = Tool(
    name="calculator", 
    description="수학 계산을 수행합니다",
    func=calculate_function
)

# Agent에게 도구 목록을 전달
agent = initialize_agent(
    tools=[search_tool, calculator_tool],
    llm=llm,
    agent_type="zero-shot-react-description"
)
```

Tool의 본질은 **LLM이 호출할 수 있는 외부 기능의 추상화**라는 점에서 Function Calling과 같지만, LangChain같은 프레임워크가 이를 표준화된 **인터페이스**로 감싸주면서, 다양한 도구를 쉽게 조합할 수 있게 되었다.

### Skills: 더 모듈화된 접근

Tools가 개별 함수 수준의 능력이라면, **Skills**는 한 단계 높은 추상화다. Skills는 특정 도메인의 지식과 도구 사용 능력을 **재사용 가능한 패키지**로 묶은 것이다.
예를 들어, "GitHub 관리" 스킬은 다음을 포함할 수 있다:

- GitHub API 호출 도구 세트
- PR 리뷰 시 따라야 할 프롬프트 가이드
- 코드 컨벤션에 대한 도메인 지식

Skills 패턴의 장점은 **점진적 공개(Progressive Disclosure)** 에 있었다. Agent가 모든 도구를 한번에 로드하는 대신, 필요한 시점에 적절한 스킬을 활성화하여 컨텍스트 윈도우를 효율적으로 사용할 수 있었다.

### N×M 통합 문제

2024년이 되자, 생태계는 **폭발적으로 성장**하는 동시에 **심각하게 파편화**되었다.
**LLM 제공자** 측:

- OpenAI (GPT-4, GPT-4 Turbo)
- Anthropic (Claude 2, Claude 3)
- Google (Gemini)
- Meta (LLaMA)
- 수십 개의 오픈소스 모델

**AI 애플리케이션** 측:

- Cursor, GitHub Copilot (코딩 도구)
- ChatGPT, Claude.ai (대화형 AI)
- 수백 개의 AI 에이전트 프레임워크

**외부 서비스** 측:

- GitHub, Slack, Jira, Google Drive, Notion, DB, 클라우드 서비스...

문제는 이들을 연결하는 **표준이 없었다**는 것이다.

```
              AI 앱 A        AI 앱 B        AI 앱 C
           (OpenAI 사용)  (Claude 사용)  (Gemini 사용)
                ↕               ↕               ↕  
GitHub ─ [커스텀 코드A] ─ [커스텀 코드B] ─ [커스텀 코드C]
Slack  ─ [커스텀 코드D] ─ [커스텀 코드E] ─ [커스텀 코드F]
Jira   ─ [커스텀 코드G] ─ [커스텀 코드H] ─ [커스텀 코드I]
```

N개의 AI 앱과 M개의 외부 서비스를 연결하려면, **N×M개의 커스텀 통합**이 필요했다. 새로운 AI 앱이 등장할 때마다, 새로운 서비스가 추가될 때마다, 통합 코드는 기하급수적으로 늘어났다.  
이것은 지속 가능하지 않았다. **USB가 등장하기 전, 모든 기기마다 다른 커넥터를 사용하던 시절**과 같았다.

## 4. MCP의 탄생

### MCP란

2024년 11월 25일, Anthropic은 **MCP(Model Context Protocol)** 를 오픈소스로 공개했다. MCP는 LLM 애플리케이션과 외부 데이터 소스 및 도구 사이의 양방향 연결을 위한 **개방형 표준 프로토콜**이다.  

### 왜 MCP가 필요했는가

앞서 살펴본 N×M 문제를 다시 보자. MCP 이전과 이후를 비교하면:

**MCP 이전 (N×M 통합):**

```
AI 앱 A ──[커스텀]──→ GitHub
AI 앱 A ──[커스텀]──→ Slack  
AI 앱 A ──[커스텀]──→ DB

AI 앱 B ──[커스텀]──→ GitHub
AI 앱 B ──[커스텀]──→ Slack
AI 앱 B ──[커스텀]──→ DB

→ 6개의 커스텀 통합 필요 (2 앱 × 3 서비스)
```

**MCP 이후 (N+M 통합):**

```
AI 앱 A ──[MCP]──┐
                  ├──→ GitHub MCP 서버
AI 앱 B ──[MCP]──┤    Slack MCP 서버
                  └──→ DB MCP 서버

→ 5개의 구현만 필요 (2개 MCP 클라이언트 + 3개 MCP 서버)
```

AI 앱은 MCP 클라이언트만 구현하면 **모든 MCP 서버**에 연결할 수 있다. 외부 서비스는 MCP 서버만 한 번 구현하면 **모든 AI 앱**에서 사용할 수 있다. N×M이 N+M으로 줄어든다.

### Language Server Protocol에서 영감을 얻다

MCP의 설계는 Microsoft의 **LSP(Language Server Protocol)** 에서 직접적인 영감을 받았다.  
LSP 이전에는 각 IDE(VS Code, IntelliJ, Vim...)가 각 프로그래밍 언어(Python, Go, Typescript...)에 대해 별도의 자동완성/린팅/포매팅 로직을 구현해야 했다. LSP가 등장하면서, 언어별로 하나의 Language Server만 구현하면 모든 IDE에서 사용할 수 있게 되었다.  
MCP는 이와 동일한 접근을 AI 도구 통합에 적용한 것이다.

## 5. MCP의 동작 원리

### 아키텍처: Host → Client → Server

MCP는 세 가지 핵심 컴포넌트로 구성된다.

**Host (호스트)**

- LLM 애플리케이션 그 자체. Cursor IDE, Claude Desktop, 또는 사용자가 만든 AI 앱이 될 수 있다.
- 여러 개의 MCP Client를 생성하고 관리한다.
- 보안 정책을 적용하고, 사용자 승인을 관리한다.

**Client (클라이언트)**

- Host 내부에서 동작하며, **하나의 Server와 1:1로 연결**된다.
- 프로토콜 협상(capability negotiation)을 수행한다.
- Host와 Server 사이에서 메시지를 양방향으로 중계한다.

**Server (서버)**

- 외부 서비스의 기능을 MCP 프로토콜로 노출하는 경량 프로세스.
- 각 서버는 독립적으로 운영되며, 다른 서버의 존재를 알지 못한다.
- 서버 간 격리를 통해 보안을 확보한다.

### 서버가 제공하는 세 가지 — Tools, Resources, Prompts

MCP 서버는 세 가지 종류의 기능을 노출할 수 있다:

#### 1. Tools (도구)

LLM이 호출할 수 있는 **실행 가능한 함수**. Function Calling의 진화형이다.

```json
{
  "name": "create_github_issue",
  "description": "GitHub 저장소에 새 이슈를 생성합니다",
  "inputSchema": {
    "type": "object",
    "properties": {
      "repo": { "type": "string", "description": "owner/repo 형식" },
      "title": { "type": "string" },
      "body": { "type": "string" }
    },
    "required": ["repo", "title"]
  }
}
```

기존 Function Calling과의 차이점: Tool의 **정의와 실행 로직이 서버에 함께 존재**한다. 클라이언트는 서버에게 "이 도구를 이 인자로 실행해줘"라고 요청하기만 하면 된다.

#### 2. Resources (리소스)

LLM에 **컨텍스트로 제공되는 데이터**. 읽기 전용이다.

```json
{
  "uri": "github://repos/myorg/myrepo/issues/42",
  "name": "Issue #42",
  "mimeType": "application/json"
}
```

파일 내용, 데이터베이스 레코드, API 응답 등 LLM이 참고할 수 있는 정보를 제공한다. Tool이 "행동"이라면, Resource는 "지식"이다.

#### 3. Prompts (프롬프트)

미리 정의된 **프롬프트 템플릿과 워크플로우**.

```json
{
  "name": "code_review",
  "description": "코드 리뷰를 수행하는 프롬프트 템플릿",
  "arguments": [
    { "name": "diff", "description": "리뷰할 코드 diff", "required": true }
  ]
}
```

특정 작업에 최적화된 프롬프트를 서버가 제공하여, LLM이 일관된 방식으로 작업을 수행하도록 안내한다.

### MCP가 표준화한 것과 하지 않은 것 — 두 개의 통신 구간

MCP를 이해할 때 가장 흔히 오해하는 부분이 있다. MCP 시스템에는 **두 개의 서로 다른 통신 구간**이 존재하고, MCP가 표준화한 것은 그 중 하나뿐이다.

```text
   MCP와 무관한 영역                    MCP가 표준화한 영역
◄─────────────────────►    ◄──────────────────────────────►

┌───────┐  벤더 고유 형식    ┌──────┐     JSON-RPC 2.0     ┌──────────┐
│  LLM  │ ═══════════════ │ Host │ ═══════════════════ │MCP Server│
│       │  (REST API)     │      │  (MCP 프로토콜)       │          │
└───────┘                 └──────┘                     └──────────┘
                              ▲
                              │
                         Host가 번역
```

**구간 ① Host ↔ LLM (벤더 고유 형식, MCP와 무관)**
Host가 LLM에게 "사용 가능한 도구 목록"과 "사용자 메시지"를 보내는 구간이다. 이것은 **각 LLM 벤더의 REST API 형식**을 따르며, JSON-RPC가 아니다.

LLM이 도구 호출이 필요하다고 판단하면, 역시 벤더 고유 형식으로 응답한다. 같은 내용이라도 벤더마다 형식이 다르다.  
LLM이 이런 형식의 JSON을 어떻게 만들어내는가? LLM이 학습/파인튜닝을 통해 이 형식을 "생성"하도록 훈련된 것이다. **MCP는 이 구간에 전혀 관여하지 않는다.**

**구간 ② MCP Client ↔ MCP Server (JSON-RPC 2.0, MCP 표준)**
LLM이 "이 도구를 호출해달라"고 응답하면, Host가 그 벤더 고유 형식을 파싱하여 **MCP 표준 형식(JSON-RPC 2.0)으로 변환**한 후, MCP Client를 통해 Server에 전달한다.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "create_github_issue",
    "arguments": {
      "repo": "myorg/myrepo",
      "title": "버그 수정 필요",
      "body": "로그인 페이지에서 오류 발생"
    }
  }
}
```

서버가 실행 결과를 돌려보내면, 역시 JSON-RPC 형식이다:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "이슈 #143이 성공적으로 생성되었습니다."
    }]
  }
}
```

정리하면, **Host가 중간에서 번역기 역할**을 한다. LLM의 벤더 고유 형식을 MCP 형식으로 변환하고, MCP 결과를 다시 벤더 형식으로 변환하여 LLM에게 넘긴다.  
MCP가 표준화한 것은 "AI 앱 ↔ 외부 도구" 구간이지, "AI 앱 ↔ LLM" 구간이 아니다. 비유하자면, MCP는 **도구 쪽의 커넥터를 USB-C로 통일한 것**이고, LLM 쪽의 커넥터는 아직 각 벤더가 자기 방식을 쓰고 있는 셈이다. 그래서 GitHub MCP 서버를 한 번 만들어 두면, Cursor에서든 Claude Desktop에서든 어떤 LLM을 쓰든 그대로 작동한다. 각 Host가 자기 LLM의 tool calling 형식을 MCP 형식으로 번역하는 부분만 구현하면 된다.

### LLM의 Tool Calling은 실패할 수 있다

여기서 자연스럽게 따라오는 질문이 있다. LLM이 tool calling을 어떤 형식으로 할지는 학습을 통해 익힌 것인데, **잘못된 형식으로 응답할 수도 있지 않은가?**
맞다. LLM은 결국 다음 토큰을 예측하는 모델이다. Tool calling 응답도 LLM이 `{`, `"`, `n`, `a`, `m`, `e`, ... 이렇게 토큰을 하나씩 생성한 결과물이다. 그래서 다양한 오류가 발생할 수 있다:

- **JSON 문법 오류**: 복잡한 중첩 구조에서 괄호 짝을 놓치는 경우
- **존재하지 않는 도구 이름**: `create_github_issue`가 아닌 `make_github_issue`처럼 비슷하지만 다른 이름을 환각(hallucinate)하는 경우
- **잘못된 파라미터**: 스키마에 `repo`로 정의된 필드를 `repository`로 쓰거나, 필수 필드를 빠뜨리는 경우
- **타입 불일치**: 배열(array)이어야 할 값을 문자열로 생성하는 경우

최신 LLM들은 파인튜닝을 통해 올바른 JSON을 생성하도록 훈련되며, OpenAI의 Structured Outputs처럼 **Constrained Decoding(제약 디코딩)** 을 적용하는 경우도 있다. Constrained Decoding은 토큰 생성 시 JSON 문법에 맞는 토큰만 선택되도록 확률 분포를 제한하는 방식이다. 이런 기법들 덕분에 GPT-4나 Claude 같은 모델에서 JSON 문법 오류 자체는 거의 발생하지 않는다. 하지만 **"문법적으로 올바르지만 의미적으로 틀린"** 경우(잘못된 도구 이름, 잘못된 파라미터)는 여전히 발생한다.

이를 완화하기 위해 Host는 도구 이름이 실제 존재하는지 확인하고, 파라미터가 스키마에 맞는지 검증하며, 필수 필드 누락 여부를 체크하는 등의 검증을 수행한다.  
그래서 LLM의 tool calling은 100% 신뢰할 수 없다. 이것이 MCP 스펙에서 Host가 **모든 도구 호출에 대해 사용자의 명시적 동의를 받도록** 설계 원칙에 명시하고 있는 이유다. 실무적으로는 `readOnlyHint`, `destructiveHint` 같은 어노테이션을 활용해 위험도에 따라 자동 승인 정책을 적용하기도 하지만, 기본 원칙은 모든 도구에 대한 사용자 승인이다. Cursor에서 터미널 명령 실행 전에 승인을 묻는 것도 같은 맥락이다.

### 전송 계층(Transport)

MCP는 두 가지 표준 전송 방식을 정의한다:

**1. stdio (Standard I/O)**

```
Host 프로세스 ──stdin/stdout──→ Server 프로세스 (자식 프로세스)
```

- Host가 MCP 서버를 **자식 프로세스**로 실행한다.
- stdin/stdout을 통해 JSON-RPC 메시지를 주고받는다.
- 로컬 도구에 적합하다. (파일 시스템, 로컬 DB 등)

**2. Streamable HTTP**

```
Client ──HTTP POST/GET──→ Remote Server 
  ←── SSE (Server-Sent Events) ──
```

- 서버가 독립적인 HTTP 서비스로 운영된다.
- POST로 요청을 보내고, SSE로 스트리밍 응답을 받을 수 있다.
- 원격 서비스에 적합하다. (클라우드 API, SaaS 등)

## 마치며

MCP는 혁명적인 새 기술이 아니다. Function Calling이라는 검증된 개념을 가져다가, LSP라는 검증된 아키텍처 패턴을 적용하고, JSON-RPC라는 검증된 프로토콜 위에 구축한 것이다. **올바른 추상화를 올바른 시점에 제시한 것** — 그것이 MCP가 빠르게 산업 표준이 된 이유다.

LLM은 이제 더 이상 고립된 천재가 아니다. MCP라는 표준 연결 고리를 통해, AI는 비로소 **세상과 연결된 지능**이 되어가고 있다.

---

_이 글은 2026년 3월 기준으로 작성되었습니다._
