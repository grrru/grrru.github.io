---
date: 2026-02-25
draft: true
title: Python 비동기 프로그래밍
categories: python
tags: "\basyncio"
author: grrru
---

## 1. 동기 vs 비동기

### 동기(Synchronous) 실행

I/O 작업 등이 완료될 때까지 프로그램 전체가 멈춘다.

```python
import time


def do_jobs():
    time.sleep(1)
    print("A completed")
    time.sleep(1)
    print("B completed")
    time.sleep(1)
    print("C completed")


do_jobs() 약 3초
```

### 비동기(Asynchronous) 실행

하나의 스레드로 여러 I/O 작업을 동시에 진행할 수 있다.

```python
import asyncio


async def job(name, seconds):
    await asyncio.sleep(seconds)
    print(f"{name} completed")


async def do_jobs():
    await asyncio.gather(job("A", 1), job("B", 1), job("C", 1))


asyncio.run(do_jobs()) # 약 1초
```

### 동시성(Concurrency) vs 병렬성(Parallelism)

- 동시성: 여러 작업을 번갈아가며 진행한다. 한 순간에 실행 중인 작업은 하나지만, 빠른 전환으로 동시에 진행되는 것처럼 보인다. `asyncio`가 이 방식으로 실행된다.
- 병렬성: 여러 작업이 물리적으로 동시에 실행된다. CPU 코어가 여러 개 필요한 multiprocessing

`asyncio`는 동시성이다. 싱글 스레드에서 `await` 지점마다 작업을 전환하여 I/O 대기 시간을 활용한다.

### Python의 동시성 모델

| 모델              | 방식           | GIL 영향                 |
| ----------------- | --------------  | ----------------------- |
| `asyncio`           | 단일 스레드, 협력적 전환  | GIL과 무관 (스레드 1개)        |
| `threading`         | 멀티 스레드, 선점적 전환 | GIL에 의해 CPU 작업은 병렬 불가   |
| `multiprocessing`   | 멀티 프로세스, 진정한 병렬 | 프로세스별 독립 GIL |

> GIL (Global Interpreter Lock): `CPython`에서 한 번에 하나의 스레드만 Python 바이트코드를 실행할 수 있도록 하는 Lock.
> 협력적 멀티태스킹 (Cooperative Multitasking): 실행 중인 작업(coroutine)이 스스로 양보(yield)하여 넘겨주는 방식 -> `asyncio`
> 선점적 멀티태스킹 (Preemptive Multitasking): 시간이 지나면 다른 작업에 의해 뺏기는 방식 -> `threading`

## 2. async, await, yield

### `async`

`async` 키워드는 함수 정의 앞에 붙어서, 이 함수가 coroutine 함수임을 선언한다. Coroutine 함수는 호출해도 즉시 실행되지 않고, coroutine 객체를 반환한다.

```python
async def coroutine():
    return 1


coroutine() # Result of async function call is not used; use "await" or assign result to variable [reportUnusedCoroutine]
```

`async`가 붙은 함수는 내부에서만 `await` 키워드를 사용할 수 있다.

```python
async def ok():
  await asyncio.sleep(1)

def bad():
  await asyncio.sleep(1) # Syntax Error
```

`async`는 함수 외에도 `with`, `for` 앞에 붙을 수 있다.

```python
async with resource() as r:
  ...

async for item in stream():
  ...
```

### `await`

`await` 키워드는 `async` 함수 안에서만 사용 가능하며 다음 역할을 한다.

1. 대상(coroutine, Task, Future)을 실행한다.
2. 결과가 준비될 떄까지 현재 coroutine을 일시 중단하고, 이벤트 루프에 제어권을 반환한다.

```python
import asyncio


async def make_coffee():
    print("make coffee...")
    await asyncio.sleep(2)
    print("finish!")
    return "catppuccin"


async def main():
    coffee = await make_coffee()
    print(f"coffee: {coffee}")


asyncio.run(main())
```

`await make_coffee()` 처럼 작성해야 coroutine 객체를 만들고 실행까지 된다.

### awaitable 객체

`await` 뒤에 올 수 있는 객체

| 타입                  | 예시                                  | 설명                            |
| ------------------- | ----------------------------------- | ----------------------------- |
| Coroutine                 | `await fetch_data()`                | `async def`로 만든 coroutine 객체        |
| Task                | `await asyncio.create_task(coro())` | 이벤트 루프에 스케줄링된 코루틴 래퍼         |
| Future              | `await asyncio.Future()`            | 미래에 완료될 결과를 담는 저수준 객체         |
| `__await__`를 구현한 객체 | 커스텀 awaitable                       | `__await__` 메서드가 이터레이터를 반환하는 객체 |

### `yield`

`yield`는 함수를 제네레이터로 만든다. `yield`는 `return`과 다르게 값을 내보낸 뒤, 함수의 실행 상태를 유지한 채 멈춘다.

```python
import asyncio


async def async_gen():
    await asyncio.sleep(1)
    yield "first"
    await asyncio.sleep(1)
    yield "second"


async def main():
    async for value in async_gen():
        print(value)


asyncio.run(main())
```

`async def`로 정의된 함수는 본문의 `yield` 키워드 사용 여부에 따라 `coroutine` 또는 `async_generator`로 구분된다.

| 구분   | `async def` + `return`    | `async def` + `yield`        |
| ---- | ---- | ---- |
| 생성 객체 | `coroutine`               | `async_generator`            |
| 소비 방법 | `result = await coro()`   | `async for item in gen():`   |
| 용도   | 비동기 작업 후 결과 하나 반환         | 비동기 작업하며 값을 여러 개 순차 생산       |

## 3. 이벤트 루프

이벤트 루프는 `asyncio`의 핵심이다. 실행 준비가 된 coroutine을 골라서 실행하고 I/O 대기가 필요하면 다른 coroutine으로 전환하여 실행한다. 이벤트 루프는 강제로 제어권을 뻇어오지 않는다. 다른 코루틴이 `await`해야 루프가 큐에서 다음 작업을 꺼낼 수 있다.

### Coroutine 객체 상태

- `CORO_CREATED`: 실행 시작을 기다리는 상태
- `CORO_RUNNING`: 인터프리터에서 실행 중인 상태
- `CORO_SUSPENDED`: `await`에서 일시 중지된 상태
- `CORO_CLOSED`: 실행이 완료된 상태

이벤트 루프가 coroutine의 상태 전환을 관리한다. `await`에서 SUSPENDED되면 다른 coroutine을 RUNNING으로 전환하는 등...

### 이벤트 루프 사이클

```python
import asyncio


async def task_a():
    print("A-1")
    await asyncio.sleep(1)
    print("A-2")


async def task_b():
    print("B-1")
    await asyncio.sleep(0.5)
    print("B-2")


async def main():
    await asyncio.gather(task_a(), task_b())


asyncio.run(main())
```

- `task_a`와 `task_b`가 이벤트 루프에 등록된다.
- `task_a` 실행 -> print A-1 -> sleep -> task_a 보류
- `task_b` 실행 -> print B-1 -> sleep -> task_b 보류
- 이벤트 루프에 실행 가능한 coroutine이 없어서 대기
- `task_b`의 sleep 완료 -> print B-2 -> `task_a`의 sleep 완료 -> print A-2

> `await`로 coroutine이 중단되면 이벤트 루프가 **실행 가능한 다른 coroutine**으로 전환한다. 스레드가 잠 드는 것이 아니라, 같은 스레드 내에서 다른 작업을 처리하는 것.

### `asyncio.run()` 동작

1. 새 이벤트 루프 생성
2. 모든 coroutine이 종료될 때까지 루프 실행
3. 루프 정리 및 종료

한 스레드에서는 한 번에 하나의 이벤트 루프만 실행될 수 있다. 이미 루프가 가동 중인 비동기 환경에서 다시 `asyncio.run()`을 호출하면 에러가 발생한다.  
`asyncio.run()`은 비동기 세계의 진입점으로, 내부의 모든 로직이 종료될 때까지 호출 지점에서 코드 실행을 멈춘다.

> 보통 FastAPI/uvicorn같은 프레임워크가 이벤트 루프를 관리하므로 직접 `asyncio.run()`를 호출하는 경우는 거의 없다.

## 4. `asyncio.create_task`

`create_task`는 coroutine을 이벤트 루프에 즉시 스케줄링하고 `Task` 객체를 반환한다.

### 동작 예제

```python
import asyncio


async def say(delay, message):
    await asyncio.sleep(delay)
    print(message)


async def main():
    # 1. coroutine 객체 생성 후 즉시 await으로 coroutine 실행
    await say(1, "hello") # coro1
    await say(2, "hello") # coro2

    # 2. create_task로 coroutine 객체를 이벤트 루프에 등록
    task1 = asyncio.create_task(say(1, "hello")) # coro3
    task2 = asyncio.create_task(say(2, "hello")) # coro4

    await task1
    await task2


asyncio.run(main())
```

1. coroutine 객체를 만들고 await, 만들고 await
    - 만들어진 `coro1`가 이벤트 루프에 스케줄링되고 실행된다.
    - `coro1`이 sleep을 한 후 대기 상태로 바뀌면, 이벤트 루프가 다음 실행할 coroutine을 확인한다.
    - 하지만 등록된 다른 coroutine이 없기 때문에 무작정 대기한다.
    - `coro1` 동작이 끝난 후 `coro2`가 이벤트 루프에 등록되어 실행되어 약 3초 소요.

1. `create_task`로 두 coroutine 객체를 이벤트 루프에 등록

    - main 스레드가 `task1`, `task2`를 생성한 후 `await task1`으로 대기한다. 이 때 이벤트 루프가 제어권을 가져간다.
    - `coro3`이 sleep 후 이벤트 루프가 다음에 실행할 coroutine(`coro4`)을 찾아서 실행한다.
    - `await`로 Task 내부의 coroutine의 동작이 끝날 때까지 대기한다.
    - `await`으로 Task가 coroutine의 동작이 끝났다는 신호를 받아주지 않으면 메인 스레드가 즉시 종료되어 제대로 coroutine의 실행 결과를 받을 수 없다. (fire-and-forget)

### fire-and-forget 패턴

```python
async def log_event(event):
    await asyncio.sleep(1) 
    print(f"logged: {event}")

async def handler():
    asyncio.create_task(log_event("user_clicked"))  # 결과를 기다리지 않음
    return {"status": "ok"}                          # 즉시 반환
```

의도적으로 task 등록 후 `await`하지 않음으로써 백그라운드 실행을 하는 패턴
> fire-and-forget 태스크에서 예외가 발생하면 조용히 무시된다.

### Task 취소

```python
task = asyncio.create_task(long_running())
task.cancel()
try:
    await task
except asyncio.CancelledError:
    print("task cancelled")
```

## 5. `asyncio.gather`

`gather`는 여러 coroutine/task를 동시에 실행하고, 모든 결과를 리스트로 반환한다.

```python
import asyncio


async def job(name, seconds):
    print(f"{name} start")
    await asyncio.sleep(seconds)
    print(f"{name} completed")
    return f"{name} result"


async def main():
    results = await asyncio.gather(
        job("first", 2),
        job("second", 3),
        job("third", 1),
    )
    print(results)  # ['first result', 'second result', 'third result']


asyncio.run(main())
```

`gather`로 coroutine을 등록하고 `await`로 대기한다. 반환 값은 리스트인데, coroutine들의 종료 순서와는 상관없이 등록된 순서대로 정렬된다.

### TaskGroup (Python 3.11+)

`gather`의 대안으로, 하나가 실패하면 나머지는 자동 취소된다.

```python
async def main():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(job("A", 1))
        task2 = tg.create_task(job("B", 2))
        task3 = tg.create_task(job("C", 3))
    print(task1.result(), task2.result(), task3.result())
```





















