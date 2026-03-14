---
date: 2026-03-14
draft: false
title: RabbitMQ
categories: rabbitmq
tags: ["message broker","queue"]
author: grrru
---

# RabbitMQ 개념 정리

## 1. RabbitMQ란?

RabbitMQ는 AMQP(Advanced Message Queuing Protocol) 기반의 오픈소스 메시지 브로커다. Producer가 메시지를 보내면 RabbitMQ가 이를 큐에 저장하고, Consumer가 큐에서 메시지를 꺼내 처리하는 구조다.

```
Producer → [Exchange] → [Queue] → Consumer
```

메시지 브로커를 사이에 두면 Producer와 Consumer가 서로 직접 통신하지 않아도 되므로, 두 시스템 간의 결합도를 낮추고 비동기 처리가 가능해진다.

---

## 2. 핵심 구성요소

| 구성요소 | 설명 |
|---------|------|
| **Connection** | 애플리케이션과 RabbitMQ 서버 간의 TCP 연결 |
| **Channel** | Connection 위의 가상 연결. 하나의 Connection에서 여러 Channel을 열 수 있다 |
| **Exchange** | Producer가 메시지를 보내는 대상. 라우팅 규칙에 따라 큐로 메시지를 전달한다 |
| **Queue** | 메시지가 저장되는 버퍼. Consumer가 여기서 메시지를 꺼내 처리한다 |
| **Binding** | Exchange와 Queue를 연결하는 규칙. Routing Key를 기준으로 매칭한다 |
| **Routing Key** | 메시지를 발행할 때 지정하는 키. Exchange가 이 키를 보고 어떤 큐로 보낼지 결정한다 |

### Connection과 Channel의 관계

Connection은 TCP 소켓이라 생성 비용이 크다. Channel은 Connection 내부의 경량 논리 채널로, 실제 작업(큐 선언, 메시지 발행/소비)은 Channel 단위로 수행한다.

```go
// Dial accepts a string in the AMQP URI format and returns a new Connection
// over TCP using PlainAuth.
conn, _ := amqp.Dial("amqp://user:pass@localhost:5672")
defer conn.Close()

ch, _ := conn.Channel()
defer ch.Close()
```

---

## 3. Exchange 종류

### 3.1 Default Exchange (Nameless Exchange)

이름이 빈 문자열(`""`)인 특수한 Exchange다. 모든 큐는 자동으로 **큐 이름과 동일한 Routing Key**로 Default Exchange에 바인딩된다. 별도 Exchange 선언 없이 큐 이름만으로 메시지를 보낼 수 있어 가장 간단한 방식이다.

```go
// Default Exchange를 사용하여 "task_queue"에 직접 메시지 전송
ch.PublishWithContext(ctx,
    "",           // exchange: 빈 문자열 = Default Exchange
    "task_queue",  // routing key = 큐 이름
    false, false,
    amqp.Publishing{Body: []byte("hello")},
)
```

### 3.2 Direct Exchange

Routing Key가 정확히 일치하는 큐에만 메시지를 전달한다.

```
Exchange(direct) --[routing_key="error"]--> error_queue
                 --[routing_key="info"]---> info_queue
```

### 3.3 Fanout Exchange

Routing Key를 무시하고 바인딩된 **모든 큐**에 메시지를 복사하여 전달한다. 브로드캐스트 용도.

### 3.4 Topic Exchange

Routing Key에 와일드카드 패턴 매칭을 사용한다.

- `*` : 정확히 한 단어
- `#` : 0개 이상의 단어

```
routing_key="order.created"  →  "order.*" 패턴의 큐에 매칭
routing_key="order.item.shipped" → "order.#" 패턴의 큐에 매칭
```

### 3.5 Headers Exchange

Routing Key 대신 메시지 헤더의 key-value 쌍으로 라우팅한다. 잘 사용되지 않는다.

---

## 4. Binding

Binding은 Exchange와 Queue를 연결하는 규칙이다. Exchange는 메시지를 받았을 때 Binding을 참조하여 어떤 Queue로 라우팅할지 결정한다.

### Default Exchange 이외에는 Binding이 필수

Default Exchange는 모든 큐를 `routing_key = queue_name`으로 자동 바인딩해주므로 별도 설정이 필요 없다. 하지만 그 외의 Exchange를 사용하려면 **Exchange 선언 → Queue 선언 → Binding** 세 단계를 직접 구성해야 한다.

```go
// 1. Exchange 선언
ch.ExchangeDeclare(
    "log_exchange", // name
    "direct",       // type: direct, fanout, topic, headers
    true,           // durable
    false,          // autoDelete
    false,          // internal
    false,          // noWait
    nil,            // args
)

// 2. Queue 선언
ch.QueueDeclare("error_queue", true, false, false, false, nil)
ch.QueueDeclare("info_queue", true, false, false, false, nil)

// 3. Binding: Exchange와 Queue를 routing key로 연결
ch.QueueBind("error_queue", "error", "log_exchange", false, nil)
ch.QueueBind("info_queue", "info", "log_exchange", false, nil)
```

위 설정의 결과:

```
Publisher --[routing_key="error"]--> log_exchange ---> error_queue
Publisher --[routing_key= "info"]--> log_exchange ---> info_queue
```

### QueueBind 파라미터

```go
ch.QueueBind(
    "error_queue",  // queue: 바인딩할 큐 이름
    "error",        // key: 라우팅에 사용할 binding key
    "log_exchange", // exchange: 바인딩할 Exchange 이름
    false,          // noWait
    nil,            // args
)
```

여기서 두 번째 인자인 binding key의 의미는 Exchange 타입에 따라 달라진다:

| Exchange 타입 | Binding Key 역할 |
|--------------|-----------------|
| Direct | Routing Key와 정확히 일치할 때 라우팅 |
| Topic | 와일드카드 패턴으로 매칭 (`order.*`, `log.#` 등) |
| Fanout | 무시됨 (바인딩된 모든 큐에 전달) |
| Headers | 무시됨 (헤더 값으로 매칭) |

### 하나의 Queue에 여러 Binding

하나의 큐에 여러 binding key를 연결할 수 있다.

```go
ch.QueueBind("all_logs", "error", "log_exchange", false, nil)
ch.QueueBind("all_logs", "warn", "log_exchange", false, nil)
ch.QueueBind("all_logs", "info", "log_exchange", false, nil)
```

이러면 `all_logs` 큐는 `"error"`, `"warn"`, `"info"` 세 가지 routing key의 메시지를 모두 수신한다.

---

## 5. Queue 선언과 속성

`QueueDeclare`는 **멱등(idempotent)** 연산이다.

동일한 이름과 속성으로 여러 번 호출해도 이미 존재하면 기존 큐를 반환한다. 단, 이름은 같은데 속성이 다르면 에러가 발생한다.

```go
q, err := ch.QueueDeclare(
    "task_queue", // name: 큐 이름
    true,         // durable: 서버 재시작 후에도 유지
    false,        // autoDelete: 마지막 consumer 해제 시 자동 삭제 여부
    false,        // exclusive: 선언한 connection에서만 접근 가능 여부
    false,        // noWait: 서버 응답을 기다리지 않고 바로 리턴
    nil,          // args: 추가 인자 (amqp.Table)
)
```

### 주요 속성

| 속성 | 설명 |
|-----|------|
| `durable` | `true`면 RabbitMQ 재시작 후에도 큐가 남아있다. 메시지 자체의 영속성은 `DeliveryMode`로 별도 설정해야 한다 |
| `autoDelete` | Consumer가 모두 해제되면 큐를 자동 삭제한다 |
| `exclusive` | 선언한 Connection만 사용 가능하고, Connection 종료 시 큐도 삭제된다 |

### amqp.Table (Queue Arguments)

큐 선언 시 마지막 인자인 `amqp.Table`은 `map[string]interface{}` 타입으로, 큐의 부가 기능을 설정한다.

```go
amqp.Table{
    "x-message-ttl":             int32(60000),   // 메시지 TTL (밀리초)
    "x-dead-letter-exchange":    "",              // DLX 지정
    "x-dead-letter-routing-key": "main_queue",    // DLX routing key
    "x-max-length":              int32(10000),    // 큐 최대 메시지 수
}
```

`x-` 접두사가 붙은 키는 RabbitMQ가 인식하는 [공식 큐 인자](https://www.rabbitmq.com/docs/queues#optional-arguments)다.

---

## 6. 메시지 발행과 소비

### 메시지 발행 (Publish)

```go
ctx, cancel := context.WithTimeout(context.Background(), 4*time.Second)
defer cancel()

body, _ := json.Marshal(payload)

err := ch.PublishWithContext(ctx,
    "",           // exchange
    "task_queue", // routing key
    false,        // mandatory: 라우팅 실패 시 에러 반환 여부
    false,        // immediate: 즉시 소비 불가능 시 에러 반환 여부 (deprecated)
    amqp.Publishing{
        DeliveryMode: amqp.Persistent, // 메시지를 디스크에 저장
        ContentType:  "application/json",
        Body:         body,
    },
)
```

`DeliveryMode`를 `amqp.Persistent`(= 2)로 설정하면 메시지가 디스크에 저장되어 RabbitMQ가 재시작되어도 유실되지 않는다. 단, `durable` 큐와 함께 사용해야 의미가 있다.

### 메시지 소비 (Consume)

```go
msgs, _ := ch.Consume(
    "task_queue", // queue
    "",           // consumer tag (빈 문자열이면 서버가 자동 생성)
    false,        // auto-ack: false면 수동 확인 필요
    false,        // exclusive: consumer 하나가 Queue를 독점
    false,        // no-local
    false,        // no-wait
    nil,          // args
)

for d := range msgs {
    result, err := process(d.Body)
    if err != nil {
        d.Reject(false) // false = requeue 안 함
        continue
    }
    d.Ack(false) // false = 이 메시지만 확인 (multiple=false)
}
```

---

## 7. Acknowledgement와 QoS

### Ack / Reject / Nack

> `amqp.Delivery` 구조체의 메서드

| 메서드 | 동작 |
|-------|------|
| `d.Ack(multiple)` | 메시지 처리 완료. `multiple=true`면 이 메시지까지의 모든 미확인 메시지를 한번에 확인 |
| `d.Reject(requeue)` | 메시지 거부. `requeue=true`면 큐에 다시 넣고, `false`면 버리거나 DLX로 보낸다 |
| `d.Nack(multiple, requeue)` | `Reject`의 확장판. 여러 메시지를 한번에 거부할 수 있다 |

Queue는 Consumer에게 전달된 메시지가 잘 처리되었는지 확인하는 이유는 `at-least-once delivery`를 보장하기 위함이다.  
Consumer가 메시지를 받고난 직후 Consumer 프로세스가 죽을 수도 있고, 내부 로직에서 에러가 발생해 메시지가 처리되지 못하고 손실될 수도 있다.  
이를 방지하기 위해 RabbitMQ에서는 Ack를 받기 전까지 그 메시지를 **미확인(unacked)** 상태로 들고 있는다.

### QoS (Prefetch)

`Qos`는 Consumer가 한 번에 받아올 수 있는 미확인 메시지 수를 제한한다.

```go
ch.Qos(
    1,     // prefetch count: 한 번에 1개만 받음
    0,     // prefetch size: 제한 없음 (바이트 단위)
    false, // global: false면 이 channel의 consumer에만 적용
)
```

**`prefetch count = 1`**: Consumer가 이전 메시지의 Ack를 보내기 전까지 새 메시지를 받지 않는다. 이는 메시지를 순차적으로 하나씩 처리하게 만든다.

> **주의**: `Qos=1`인 상태에서 메시지 처리 중 `time.Sleep` 등으로 오래 블로킹하면, 다른 메시지들도 함께 대기하게 되는 문제가 발생한다. 이 문제의 해결책은 [10장](#10-dlx--ttl을-활용한-지연-재시도-패턴)에서 다룬다.

---

## 8. Dead Letter Exchange (DLX)

메시지가 **dead letter** 상태가 되면 RabbitMQ가 해당 메시지를 DLX로 라우팅한다. Dead letter가 되는 조건은 다음과 같다:

1. Consumer가 `Reject(requeue=false)` 또는 `Nack(requeue=false)`로 거부
2. 메시지의 TTL이 만료
3. 큐가 `x-max-length`를 초과하여 메시지가 drop됨

DLX는 큐 선언 시 `x-dead-letter-exchange` 인자로 지정한다.

```go
ch.QueueDeclare(
    "task_queue", true, false, false, false,
    amqp.Table{
        "x-dead-letter-exchange":    "dlx_exchange",
        "x-dead-letter-routing-key": "dead_letter_queue",
    },
)
```

### Default Exchange를 DLX로 사용하기

DLX에 빈 문자열(`""`)을 지정하면 **Default Exchange**가 DLX가 된다. Default Exchange에서는 routing key가 곧 큐 이름이므로, 별도의 Exchange 선언이나 Binding 없이 `x-dead-letter-routing-key`에 큐 이름만 적으면 된다.

```go
amqp.Table{
    "x-dead-letter-exchange":    "",            // Default Exchange
    "x-dead-letter-routing-key": "task_queue",  // 이 큐로 dead letter가 전달됨
}
```

이 방식은 dead letter의 목적지가 고정된 단순한 구조에서 유용하다.

공식 문서: [Dead Lettering — RabbitMQ](https://www.rabbitmq.com/docs/dlx)

---

## 9. TTL (Time-To-Live)

TTL은 메시지가 큐에 머무를 수 있는 최대 시간을 제한한다. TTL이 만료되면 메시지는 **dead letter** 상태가 된다.

### 큐 단위 TTL

큐 선언 시 `x-message-ttl`을 설정하면 해당 큐의 모든 메시지에 동일한 TTL이 적용된다.

```go
ch.QueueDeclare(
    "delay_60s", true, false, false, false,
    amqp.Table{
        "x-message-ttl": int32(60000), // 60초 후 만료 (밀리초 단위)
    },
)
```

### 메시지 단위 TTL

발행 시 `Expiration` 필드를 설정하면 개별 메시지에 TTL을 줄 수 있다.

```go
ch.PublishWithContext(ctx, "", "some_queue", false, false,
    amqp.Publishing{
        Expiration: "60000", // 문자열로 밀리초 지정
        Body:       body,
    },
)
```

두 TTL이 동시에 존재하면 **더 짧은 쪽**이 적용된다.

> **핵심**: TTL 자체는 "만료 후 메시지를 폐기"하는 기능이다. 하지만 DLX와 결합하면, **만료된 메시지가 폐기되지 않고 DLX를 통해 다른 큐로 전달**된다. 이 조합이 지연 재시도 패턴의 핵심이다.

공식 문서: [TTL — RabbitMQ](https://www.rabbitmq.com/docs/ttl)

---

## 10. DLX + TTL을 활용한 지연 재시도 패턴

> **참고**: 사실 RabbitMQ에는 [`rabbitmq_delayed_message_exchange`](https://github.com/rabbitmq/rabbitmq-delayed-message-exchange)라는 플러그인이 있었는데, 이걸 쓰면 이 섹션에서 다루는 패턴 자체가 필요 없었다. 그런데 이 플러그인은 현재 archived 상태다..!
>
> 오픈소스에서 공식적으로 권장하는 대안이 바로 DLX + TTL 조합이다. 다만 이는 단순한 지연/재시도를 상정한 것이고, 여러 큐를 사용하는 exponential backoff까지 공식적으로 권장하는 건 아니다(?). 이 섹션은 그 조합을 기반으로 backoff를 직접 구현하는 예제다.

### 문제 상황

외부 API 호출 실패 시 재시도가 필요하지만, Consumer 내에서 `time.Sleep`으로 대기하면:

- `Qos=1` 환경에서 해당 Consumer가 블로킹되어 다른 메시지 처리가 중단됨
- 재시도 대기 시간이 길수록(예: exponential backoff) 전체 처리량이 급감

```go
// 문제가 있는 코드: sleep 동안 Consumer가 멈춘다
case ActionRetry:
    d.Reject(false)
    sleepSeconds := min(MaxBackoff, tryCount*tryCount)
    time.Sleep(time.Duration(sleepSeconds) * time.Second)  // 블로킹!
    republish(ch, payload)
```

### 해결: TTL 기반 지연 큐

메시지를 TTL이 설정된 별도 큐에 넣으면, **RabbitMQ가 대기 시간을 관리**하고 만료 후 DLX를 통해 원래 큐로 돌려보낸다. Consumer는 블로킹 없이 즉시 다음 메시지를 처리할 수 있다.

```
Main Queue ←──────────────── [Default Exchange]
    │                              ↑
    │ (Retry 필요)                 │ (TTL 만료 → dead letter)
    ↓                              │
Retry Queue (TTL=3s)   ────────────┘
Retry Queue (TTL=9s)   ────────────┘
Retry Queue (TTL=27s)  ────────────┘
    ...
    ...
```

### 구현

#### 1단계: Retry Queue 정의

3^n exponential backoff 전략으로 단계별 지연 큐를 정의한다.

```go
const MaxBackoff = 3600 // 최대 대기시간 (초)

// tryCount → delay(3^n): 1→3s, 2→9s, 3→27s, 4→81s, 5→243s, 6→729s, 7→2187s, 8+→3600s
var RetryQueues = []struct {
    Name string
    TTL  int // milliseconds
}{
    {"retry_3s", 3_000},
    {"retry_9s", 9_000},
    {"retry_27s", 27_000},
    {"retry_81s", 81_000},
    {"retry_243s", 243_000},
    {"retry_729s", 729_000},
    {"retry_2187s", 2_187_000},
    {"retry_3600s", 3_600_000},
}

func retryQueueIndex(tryCount int) int {
    delays := []int{3, 9, 27, 81, 243, 729, 2187}
    if tryCount <= 0 {
        return 0
    }
    backoff := 1
    for i := 0; i < tryCount; i++ {
        backoff *= 3 // 3^tryCount
    }
    if backoff >= MaxBackoff {
        return len(RetryQueues) - 1
    }
    for i, d := range delays {
        if backoff <= d {
            return i
        }
    }
    return len(RetryQueues) - 1
}
```

#### 2단계: Retry 인프라 선언

각 retry 큐에 TTL과 DLX를 설정한다. TTL이 만료되면 Default Exchange를 통해 메인 큐로 돌아간다.

```go
const MainQueue = "task_queue"

func declareRetryInfra(ch *amqp.Channel) error {
    for _, rq := range RetryQueues {
        if _, err := ch.QueueDeclare(
            rq.Name,
            true, false, false, false,
            amqp.Table{
                "x-message-ttl":             int32(rq.TTL),
                "x-dead-letter-exchange":    "",         // Default Exchange
                "x-dead-letter-routing-key": MainQueue,  // 만료 후 메인 큐로
            },
        ); err != nil {
            return err
        }
    }
    return nil
}
```

- `x-message-ttl`: 이 큐에 들어온 메시지가 지정된 시간(ms) 후 dead letter가 된다
- `x-dead-letter-exchange: ""`: dead letter가 Default Exchange로 전달된다
- `x-dead-letter-routing-key: "task_queue"`: Default Exchange에서 routing key가 큐 이름이므로, 메인 큐로 라우팅된다

#### 3단계: Retry 메시지 발행

`tryCount`에 맞는 retry 큐로 메시지를 보낸다.

```go
func sendRetry(ch *amqp.Channel, payload TaskPayload) error {
    idx := retryQueueIndex(payload.TryCount)
    queueName := RetryQueues[idx].Name

    log.Printf("retry tryCount=%d → %s", payload.TryCount, queueName)

    ctx, cancel := context.WithTimeout(context.Background(), 4*time.Second)
    defer cancel()

    body, err := json.Marshal(payload)
    if err != nil {
        return err
    }

    return ch.PublishWithContext(ctx,
        "",        // Default Exchange
        queueName, // routing key = retry 큐 이름
        false, false,
        amqp.Publishing{
            DeliveryMode: amqp.Persistent,
            ContentType:  "application/json",
            Body:         body,
        },
    )
}
```

#### 4단계: Consumer에서 호출

기존의 `time.Sleep` 블로킹 코드를 `sendRetry` 호출로 대체한다.

```go
for d := range msgs {
    payload := parsePayload(d.Body)
    result := process(payload)

    switch result {
    case ActionOK:
        d.Ack(false)

    case ActionFailed:
        d.Reject(false) // 버림 (재시도 안 함)

    case ActionRetry:
        d.Reject(false)          // 현재 메시지를 큐에서 제거
        payload.TryCount++
        sendRetry(ch, payload)   // TTL 큐에 넣고 즉시 리턴 → 블로킹 없음
    }
}
```

### 메시지 흐름 전체 요약

```
1. Producer가 task_queue에 메시지 발행
2. Consumer가 메시지를 수신하여 처리
3. 처리 실패 (ActionRetry):
   a. d.Reject(false)로 원본 메시지 제거
   b. tryCount를 증가시키고 sendRetry 호출
   c. tryCount에 따라 적절한 retry 큐 선택 (예: retry_27s)
   d. Default Exchange를 통해 retry 큐에 메시지 발행
4. retry 큐에서 TTL동안 대기 (e.g. 27s)
5. TTL 만료 → dead letter 발생
6. x-dead-letter-exchange=""로 Default Exchange에 전달
7. x-dead-letter-routing-key="task_queue"로 메인 큐에 도착
8. Consumer가 다시 수신 → 2번으로 돌아감
```

---

## 11. Policy vs Queue Arguments

큐의 TTL, DLX 등을 설정하는 방법은 크게 두 가지다.

### Queue Arguments (코드에서 설정)

```go
amqp.Table{
    "x-message-ttl":          int32(60000),
    "x-dead-letter-exchange": "",
}
```

- 큐 선언 시 코드에서 직접 지정
- 큐가 이미 존재하고 속성이 다르면 에러 (큐를 삭제 후 재생성해야 변경 가능)
- 코드와 설정이 한 곳에 있어 관리가 쉬움

### Policy (RabbitMQ 서버에서 설정)

RabbitMQ Management UI나 CLI에서 패턴 매칭으로 여러 큐에 일괄 적용:

```bash
rabbitmqctl set_policy my-ttl "^retry_.*" \
  '{"message-ttl": 60000, "dead-letter-exchange": ""}' \
  --apply-to queues
```

- 코드 변경 없이 서버에서 런타임에 변경 가능
- 패턴으로 여러 큐에 동시 적용 가능
- Queue Arguments와 Policy가 둘 다 있으면 **둘 중 더 보수적인 값**이 적용됨

### 어떤 걸 사용해야 할까?

| 상황 | 추천 |
|------|------|
| 큐마다 TTL이 다르다 (재시도 큐 등) | **Queue Arguments** — 큐별로 다른 설정을 코드에서 한 곳에 관리 |
| 동일한 설정을 다수의 큐에 적용 | **Policy** — 패턴 하나로 일괄 적용 |
| 운영 중 설정을 자주 바꿔야 한다 | **Policy** — 재배포 없이 변경 가능 |

이 문서에서 다룬 지연 재시도 패턴처럼 각 큐의 TTL이 모두 다른 경우에는, Policy로 설정하면 관리 포인트가 코드와 서버 두 곳으로 분리되므로 Queue Arguments로 코드에서 통합 관리하는 편이 낫다.  
근데 공식 문서에는 Policy를 강력 추천하긴 한다.

---

## 12. 참고 자료

- [RabbitMQ Official Documentation](https://www.rabbitmq.com/docs)
- [Queues — Optional Arguments](https://www.rabbitmq.com/docs/queues#optional-arguments)
- [Dead Lettering](https://www.rabbitmq.com/docs/dlx)
- [TTL (Time-To-Live)](https://www.rabbitmq.com/docs/ttl)
- [Policies and Parameters](https://www.rabbitmq.com/docs/parameters#policies)
- [AMQP 0-9-1 Model Explained](https://www.rabbitmq.com/tutorials/amqp-concepts)
- [Go AMQP Client (amqp091-go)](https://github.com/rabbitmq/amqp091-go)
