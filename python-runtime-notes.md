# Python Runtime Notes

이 문서는 Python, FastAPI, asyncio, GIL, ASGI 실행 흐름을 빠르게 다시 보기 위한 정리다.

## Python의 진입점

Python에는 C/C++/Go/Java처럼 언어 차원에서 고정된 `main()` 진입점이 없다.

어떤 파일이나 모듈을 어떻게 실행하느냐가 진입점을 결정한다.

```bash
python some_file.py
```

위 명령은 `some_file.py`의 최상위 코드를 위에서 아래로 실행한다.

```python
if __name__ == "__main__":
    main()
```

이 패턴은 "이 파일이 직접 실행될 때만 `main()`을 호출한다"는 관례다. `main`이라는 이름 자체가 특별한 것은 아니다.

## FastAPI와 uvicorn

FastAPI 앱은 그 자체로 서버가 아니다.

```python
from fastapi import FastAPI

app = FastAPI()
```

`app`은 HTTP 요청을 어떻게 처리할지 아는 ASGI 애플리케이션 객체다. 직접 TCP 포트를 열고 요청을 받지는 않는다.

서버로 실행하려면 ASGI 서버가 필요하다.

```bash
uvicorn b2s.api:app --reload
```

이 명령은 대략 다음과 같이 동작한다.

```text
uvicorn 실행
  -> b2s.api 모듈 import
  -> b2s/api.py 최상위 코드 실행
  -> app = FastAPI(...) 객체 생성
  -> @app.post(...) 라우트 등록
  -> uvicorn이 app을 ASGI 앱으로 실행
  -> HTTP 요청 대기
```

`b2s.api:app`은 파일 경로가 아니라 Python import path다.

```text
b2s.api = b2s/api.py 모듈
app     = 그 모듈 안의 변수 이름
```

## ASGI

ASGI는 Python 웹 서버와 웹 애플리케이션 사이의 표준 인터페이스다.

역할은 다음처럼 나뉜다.

```text
FastAPI
  - 라우팅
  - 요청 파싱
  - validation
  - 응답 생성
  - OpenAPI 문서 생성

uvicorn
  - TCP 포트 열기
  - HTTP 요청 받기
  - ASGI 형식으로 FastAPI app 호출
  - 응답을 HTTP로 내보내기
```

즉:

```text
FastAPI = 웹 애플리케이션 프레임워크
uvicorn = ASGI 서버
ASGI    = 둘 사이의 규격
```

FastAPI는 이미 ASGI 표준을 만족하는 앱 객체를 만들어준다. 개발자가 직접 ASGI 함수를 구현할 필요는 거의 없다.

## uvicorn 프로세스

`uvicorn`을 실행하면 서버 프로세스가 계속 떠 있다.

```text
uvicorn 프로세스 실행
  -> 포트 열기
  -> 요청 대기
  -> 요청이 오면 FastAPI app 호출
  -> 응답 반환
  -> 다시 요청 대기
```

`Ctrl+C`로 종료하기 전까지 계속 실행된다.

`--reload`를 붙이면 코드 변경 감시용 프로세스도 함께 동작한다.

## async 함수와 coroutine

`async def` 함수는 호출만으로 바로 실행되지 않는다.

```python
async def read():
    return 1

coro = read()
```

위 코드는 `read()`를 실행하는 것이 아니라 coroutine 객체를 만든다.

실행하려면 `await`해야 한다.

```python
result = await read()
```

정리하면:

```text
async 함수 호출 = coroutine 객체 생성
await coroutine = coroutine 실행/대기/결과 반환
```

`await`는 "무조건 즉시 끝까지 실행"이 아니라, coroutine을 실행하다가 다시 `await` 지점이 나오면 이벤트 루프에 제어권을 돌려준다.

## 이벤트 루프

Python에서 말하는 이벤트 루프는 보통 `asyncio` 이벤트 루프를 뜻한다.

`asyncio`는 Python 표준 라이브러리 모듈이고, 이벤트 루프는 런타임에 생성되는 객체다.

FastAPI에서는 직접 `asyncio.run()`을 호출하지 않는다. `uvicorn`이 서버를 시작하면서 이벤트 루프를 만든다.

```text
uvicorn 실행
  -> 이벤트 루프 생성
  -> FastAPI app 로드
  -> HTTP 요청 대기
  -> 요청이 오면 coroutine을 Task로 등록
  -> 이벤트 루프가 Task 실행/재개
```

이벤트 루프는 coroutine 자체를 직접 관리한다기보다, coroutine을 감싼 `Task`/`Future`를 스케줄링한다.

```text
coroutine = 실행 가능한 비동기 함수의 상태 객체
Task      = coroutine을 이벤트 루프에 올려 실행/관리하는 wrapper
Future    = 나중에 완료될 결과를 표현하는 객체
event loop = Task/Future를 스케줄링하는 관리자
```

## await와 I/O

예를 들어 FastAPI에서 업로드 파일을 읽을 때:

```python
content = await file.read()
```

흐름은 대략 다음과 같다.

```text
file.read() coroutine 생성
await로 실행 시작
현재 요청 coroutine 일시 중단
이벤트 루프는 다른 요청 처리 가능
파일 read 완료
현재 coroutine 재개
content에 bytes 반환
```

다만 모든 I/O가 같은 방식으로 처리되는 것은 아니다.

```text
네트워크 I/O
  -> 보통 OS non-blocking socket을 이벤트 루프가 감시

파일 I/O
  -> Python에서는 threadpool에 맡기는 경우가 많음

CPU 작업
  -> await만 붙인다고 자동 병렬화되지 않음
```

중요한 점:

```python
pipeline.process(...)
```

같은 무거운 동기 함수는 `async def` 라우트 안에서 그냥 호출하면 이벤트 루프를 막을 수 있다.

## GIL

GIL은 Global Interpreter Lock의 약자다.

CPython에서 한 프로세스 안의 Python bytecode를 한 순간에 하나의 스레드만 실행하게 하는 전역 락이다.

정확히는:

```text
한 CPython 프로세스 안에서,
한 시점에 Python bytecode를 실행할 수 있는 스레드는 하나뿐이다.
```

Python 프로세스가 여러 OS 스레드를 만들 수 없다는 뜻은 아니다.

```python
import threading
```

으로 여러 스레드를 만들 수 있다. 다만 순수 Python bytecode를 동시에 병렬 실행할 수 없다는 뜻이다.

```text
Thread A: Python bytecode 실행 중, GIL 보유
Thread B: Python bytecode 실행하려고 대기
Thread C: Python bytecode 실행하려고 대기
```

GIL을 잡은 스레드는 시간에 따라 바뀔 수 있다.

```text
t1: Thread A가 Python bytecode 실행
t2: Thread B가 Python bytecode 실행
t3: Thread A가 다시 실행
```

즉 "고정된 하나의 스레드만 실행한다"가 아니라, "동시에 하나만 실행한다"가 정확하다.

## GIL과 I/O

I/O는 대기 중에 GIL을 놓을 수 있다.

더 정확히는:

```text
I/O를 시작하거나 결과를 처리하는 Python 코드는 GIL이 필요하다.
하지만 I/O 대기 중에는 GIL을 놓을 수 있다.
```

예:

```text
파일/네트워크 요청 준비: Python 코드, GIL 필요
OS에 I/O 요청 후 대기: GIL을 놓을 수 있음
I/O 완료 후 응답 처리: Python 코드, GIL 필요
```

그래서 I/O 위주의 서버는 async/await나 threadpool로 높은 동시성을 얻을 수 있다.

## FastAPI 요청 처리와 GIL

여러 요청이 FastAPI에 동시에 들어와도, Python 코드를 실행하는 순간에는 GIL이 필요하다.

`async def` 라우트는 보통 이벤트 루프에서 coroutine으로 실행된다.

```text
요청 A: Python 코드 실행, GIL 필요
요청 A: await I/O, 일시 중단
요청 B: Python 코드 실행, GIL 필요
요청 B: await I/O, 일시 중단
요청 A: I/O 완료, 다시 실행
```

`def` 라우트는 FastAPI/Starlette가 threadpool에서 실행한다. 하지만 threadpool 스레드도 Python bytecode를 실행하려면 GIL이 필요하다.

```text
async def route
  -> 이벤트 루프에서 실행
  -> Python 코드 실행 시 GIL 필요

def route
  -> threadpool에서 실행
  -> Python 코드 실행 시 GIL 필요
```

## worker 프로세스

FastAPI 자체가 자동으로 여러 worker 프로세스를 만드는 것은 아니다.

`uvicorn`이나 `gunicorn` 실행 옵션으로 worker 프로세스를 여러 개 띄울 수 있다.

프로세스가 여러 개면 각 프로세스마다 Python interpreter와 GIL이 따로 있다.

```text
Worker process 1: GIL 1
Worker process 2: GIL 2
Worker process 3: GIL 3
```

그래서 프로세스 단위 병렬 처리가 가능하다.

## 이 프로젝트의 현재 흐름

FastAPI 입구:

```text
b2s/api.py
  -> POST /convert
```

핵심 파이프라인:

```text
b2s/pipeline.py
  -> process_to_midi()
  -> process()
```

MIDI 생성 흐름:

```text
input audio / URL
  -> YouTube URL이면 다운로드
  -> Demucs로 drums.wav 생성
  -> STRUM backend 실행
  -> STRUM notes.mid 생성
  -> General MIDI drums.mid 변환
```

PDF 생성 흐름:

```text
drums.mid
  -> MusicXML
  -> MuseScore CLI
  -> drums.pdf
```

현재 무거운 작업은 대부분 외부 프로세스로 실행된다.

```text
demucs-infer
STRUM subprocess
ffmpeg
MuseScore
```

이들은 Python GIL에 직접 묶이지 않는다. 다만 현재 FastAPI 라우트에서 동기적으로 기다리기 때문에, 웹 서버 관점에서는 장기 작업을 job queue/background worker로 분리하는 개선 여지가 있다.

