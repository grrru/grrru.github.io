---
date: 2026-03-14
draft: false
title: RabbitMQ
categories: rabbitmq
tags: ["message broker","queue"]
author: grrru
---

# RabbitMQ Concept Overview

## 1. What is RabbitMQ?

RabbitMQ is an open-source **message broker** based on the Advanced Message Queuing Protocol (AMQP).
When a **Producer** sends a message, RabbitMQ stores it in a queue, and a **Consumer** retrieves and processes it.

```
Producer → [Exchange] → [Queue] → Consumer
```

By placing a message broker between services, the Producer and Consumer do not communicate directly.
This reduces coupling between systems and enables asynchronous processing.

---

## 2. Core Components

| Component       | Description                                                                                              |
| --------------- | -------------------------------------------------------------------------------------------------------- |
| **Connection**  | TCP connection between the application and the RabbitMQ server                                           |
| **Channel**     | Virtual connection on top of a Connection. Multiple channels can exist within one connection             |
| **Exchange**    | Target where Producers send messages. It routes messages to queues according to routing rules            |
| **Queue**       | Buffer where messages are stored. Consumers retrieve messages from here                                  |
| **Binding**     | Rule that connects an Exchange and a Queue, usually based on a routing key                               |
| **Routing Key** | Key specified when publishing a message. The Exchange uses it to decide which queue receives the message |

### Connection vs Channel

A **Connection** is a TCP socket and relatively expensive to create.
A **Channel** is a lightweight logical stream inside a connection. Actual operations such as queue declaration and message publishing happen through channels.

```go
// Dial accepts a string in the AMQP URI format and returns a new Connection
// over TCP using PlainAuth.
conn, _ := amqp.Dial("amqp://user:pass@localhost:5672")
defer conn.Close()

ch, _ := conn.Channel()
defer ch.Close()
```

---

## 3. Exchange Types

### 3.1 Default Exchange (Nameless Exchange)

A special exchange with an empty name (`""`).
Every queue is automatically bound to the Default Exchange using **its queue name as the routing key**.

This allows publishing messages directly to a queue without explicitly declaring an exchange.

```go
// Send a message directly to "task_queue" via Default Exchange
ch.PublishWithContext(ctx,
    "",           // exchange: empty string = Default Exchange
    "task_queue", // routing key = queue name
    false, false,
    amqp.Publishing{Body: []byte("hello")},
)
```

---

### 3.2 Direct Exchange

Routes messages only to queues whose **binding key exactly matches the routing key**.

```
Exchange(direct) --[routing_key="error"]--> error_queue
                 --[routing_key="info"]---> info_queue
```

---

### 3.3 Fanout Exchange

Ignores routing keys and delivers messages to **all bound queues**.

Commonly used for **broadcast scenarios**.

---

### 3.4 Topic Exchange

Supports **pattern-based routing** using wildcards.

* `*` → exactly one word
* `#` → zero or more words

Examples:

```
routing_key="order.created" → matches "order.*"
routing_key="order.item.shipped" → matches "order.#"
```

---

### 3.5 Headers Exchange

Routes messages based on **header key-value pairs** instead of routing keys.
This type is rarely used.

---

## 4. Binding

A **Binding** defines the routing rule between an Exchange and a Queue.

When an Exchange receives a message, it checks its bindings to determine where the message should be routed.

---

### Binding Required for Non-Default Exchanges

The Default Exchange automatically binds every queue using:

```
routing_key = queue_name
```

However, for any other exchange type, you must explicitly configure:

1. Exchange declaration
2. Queue declaration
3. Binding

```go
// 1. Declare Exchange
ch.ExchangeDeclare(
    "log_exchange",
    "direct",
    true,
    false,
    false,
    false,
    nil,
)

// 2. Declare Queues
ch.QueueDeclare("error_queue", true, false, false, false, nil)
ch.QueueDeclare("info_queue", true, false, false, false, nil)

// 3. Bind Queues to Exchange
ch.QueueBind("error_queue", "error", "log_exchange", false, nil)
ch.QueueBind("info_queue", "info", "log_exchange", false, nil)
```

Result:

```
Publisher --[routing_key="error"]--> log_exchange → error_queue
Publisher --[routing_key="info"]--> log_exchange → info_queue
```

---

### QueueBind Parameters

```go
ch.QueueBind(
    "error_queue",  // queue: queue name for binding
    "error",        // key: binding key for routing
    "log_exchange", // exchange: exchange name for binding
    false,          // noWait
    nil,            // args
)
```

Meaning of **binding key** depends on exchange type:

| Exchange Type | Binding Key Role                      |
| ------------- | ------------------------------------- |
| Direct        | Must match routing key exactly        |
| Topic         | Pattern matching (`order.*`, `log.#`) |
| Fanout        | Ignored                               |
| Headers       | Ignored                               |

---

### Multiple Bindings for a Single Queue

A queue can have multiple bindings.

```go
ch.QueueBind("all_logs", "error", "log_exchange", false, nil)
ch.QueueBind("all_logs", "warn", "log_exchange", false, nil)
ch.QueueBind("all_logs", "info", "log_exchange", false, nil)
```

`all_logs` receives messages with routing keys `"error"`, `"warn"`, and `"info"`.

---

## 5. Queue Declaration

`QueueDeclare` is **idempotent**.

Calling it multiple times with the same name and attributes returns the existing queue.
However, if attributes differ, RabbitMQ throws an error.

```go
q, err := ch.QueueDeclare(
    "task_queue", // name: Queue name
    true,         // durable: survives broker restart
    false,        // autoDelete: delete when last consumer disconnects
    false,        // exclusive: accessible only by the declaring connection
    false,        // noWait: return immediately without waiting for server confirmation
    nil,          // args: optional arguments (amqp.Table)
)
```

---

### Important Properties

| Property     | Description                                         |
| ------------ | --------------------------------------------------- |
| `durable`    | Queue survives broker restart                       |
| `autoDelete` | Queue is deleted when the last consumer disconnects |
| `exclusive`  | Queue accessible only by the declaring connection   |

---

### Queue Arguments (`amqp.Table`)

Optional features can be set via `amqp.Table`.

```go
amqp.Table{
    "x-message-ttl":             int32(60000),
    "x-dead-letter-exchange":    "",
    "x-dead-letter-routing-key": "main_queue",
    "x-max-length":              int32(10000),
}
```

Keys prefixed with `x-` are **RabbitMQ extension arguments**.

---

## 6. Message Publishing and Consumption

### Publishing

```go
ctx, cancel := context.WithTimeout(context.Background(), 4*time.Second)
defer cancel()

body, _ := json.Marshal(payload)

err := ch.PublishWithContext(ctx,
    "",           // exchange
    "task_queue", // routing key
    false,        // mandatory: return error if no queue matches
    false,        // immediate: return error if no consumer available (deprecated)
    amqp.Publishing{
        DeliveryMode: amqp.Persistent, // persist message to disk
        ContentType:  "application/json",
        Body:         body,
    },
)
```

Setting `DeliveryMode = Persistent` stores messages on disk.

This only guarantees durability if the queue itself is **durable**.

---

### Consuming

```go
msgs, _ := ch.Consume(
    "task_queue", // queue
    "",           // consumer tag (auto-generated if empty)
    false,        // auto-ack: false requires manual acknowledgement
    false,        // exclusive: only one consumer on this queue
    false,        // no-local
    false,        // no-wait
    nil,          // args
)

for d := range msgs {
    result, err := process(d.Body)
    if err != nil {
        d.Reject(false) // false = do not requeue
        continue
    }
    d.Ack(false) // false = acknowledge only this message (multiple=false)
}
```

---

## 7. Acknowledgement and QoS

### Ack / Reject / Nack

> Method of `amqp.Delivery`

| Method                      | Behavior                                                                                          |
| --------------------------- | ------------------------------------------------------------------------------------------------- |
| `d.Ack(multiple)`           | Confirm successful processing. If `multiple=true`, acknowledges all unacked messages up to this one |
| `d.Reject(requeue)`         | Reject message. If `requeue=true`, puts it back in the queue. If `false`, discards it or routes to DLX |
| `d.Nack(multiple, requeue)` | Extended version of `Reject`. Supports rejecting multiple messages at once                        |

RabbitMQ needs to know whether a delivered message was successfully processed in order to guarantee **at-least-once delivery**.

A consumer process may crash immediately after receiving a message, or an internal error may occur before processing completes — in either case the message would be silently lost.

To prevent this, RabbitMQ holds the message in an **unacknowledged (unacked)** state until it receives an Ack. If the consumer's connection drops before an Ack is sent, RabbitMQ re-queues the message.

---

### QoS (Prefetch)

`Qos` limits the number of unacked messages a consumer can hold at a time.

```go
ch.Qos(
    1,     // prefetch count: receive only 1 message at a time
    0,     // prefetch size: no limit (in bytes)
    false, // global: if false, applies only to consumers on this channel
)
```

**`prefetch count = 1`**: the consumer will not receive a new message until it sends an Ack for the previous one. This enforces sequential, one-at-a-time processing.

> **Note**: With `Qos=1`, blocking operations like `time.Sleep` inside the consumer will stall all message processing. See [Section 10](#10-delayed-retry-pattern-using-dlx--ttl) for the solution.

---

## 8. Dead Letter Exchange (DLX)

A message becomes **dead letter** when:

1. Consumer rejects with `requeue=false` or `Nack(requeue=false)`
2. Message TTL expires
3. Queue exceeds `x-max-length`

RabbitMQ then routes the message to a **Dead Letter Exchange(DLX)**.

DLX is configured via the `x-dead-letter-exchange` argument when declaring a queue.

```go
ch.QueueDeclare(
    "task_queue", true, false, false, false,
    amqp.Table{
        "x-dead-letter-exchange":    "dlx_exchange",
        "x-dead-letter-routing-key": "dead_letter_queue",
    },
)
```

---

### Using Default Exchange as DLX

Setting `x-dead-letter-exchange` to an empty string (`""`) uses the **Default Exchange** as the DLX.

Since the Default Exchange routes messages using the queue name as the routing key, no explicit Exchange declaration or Binding is needed — just set `x-dead-letter-routing-key` to the target queue name.

```go
amqp.Table{
    "x-dead-letter-exchange":    "",           // Default Exchange
    "x-dead-letter-routing-key": "task_queue", // dead letters are delivered to this queue
}
```

This approach is useful for simple structures where the dead letter destination is fixed.

Official docs: [Dead Lettering — RabbitMQ](https://www.rabbitmq.com/docs/dlx)

---

## 9. TTL (Time To Live)

TTL limits how long a message can stay in a queue. When TTL expires, the message becomes a **dead letter**.

### Queue-Level TTL

Setting `x-message-ttl` when declaring a queue applies the same TTL to all messages in that queue.

```go
ch.QueueDeclare(
    "delay_60s", true, false, false, false,
    amqp.Table{
        "x-message-ttl": int32(60000), // expires after 60s (milliseconds)
    },
)
```

### Message-Level TTL

Setting the `Expiration` field at publish time applies a TTL to that individual message.

```go
ch.PublishWithContext(ctx, "", "some_queue", false, false,
    amqp.Publishing{
        Expiration: "60000", // milliseconds, specified as a string
        Body:       body,
    },
)
```

If both queue-level and message-level TTL are set, **the shorter one applies**.

> **Key insight**: TTL alone discards expired messages. But combined with DLX, **expired messages are not discarded — they are forwarded to another queue via DLX**. This combination is the foundation of the delayed retry pattern.

Official docs: [TTL — RabbitMQ](https://www.rabbitmq.com/docs/ttl)

---

## 10. Delayed Retry Pattern Using DLX + TTL

> **Note**: Before diving in — RabbitMQ used to have a [`rabbitmq_delayed_message_exchange`](https://github.com/rabbitmq/rabbitmq-delayed-message-exchange) plugin that handled delayed messaging natively, which would have made this whole pattern unnecessary. Unfortunately, it has been archived.
>
> The officially suggested open-source alternative is exactly the DLX + TTL combination — though that's for basic delays and retries, not specifically for exponential backoff with multiple queues(?). What follows is an implementation that builds on that foundation.

### Problem

When an external API call fails and a retry is needed, using `time.Sleep` inside the consumer causes:

* With `Qos=1`, the consumer blocks and all other message processing halts
* The longer the retry delay (e.g. exponential backoff), the more throughput degrades

```go
// problematic code: consumer stalls during sleep
case ActionRetry:
    d.Reject(false)
    sleepSeconds := min(MaxBackoff, tryCount*tryCount)
    time.Sleep(time.Duration(sleepSeconds) * time.Second) // blocking!
    republish(ch, payload)
```

### Solution

Place the message into a separate queue with a TTL. **RabbitMQ manages the wait**, and once the TTL expires, the message is returned to the main queue via DLX. The consumer returns immediately with no blocking.

```
Main Queue ←──────────────── [Default Exchange]
    │                              ↑
    │ (retry needed)               │ (TTL expired → dead letter)
    ↓                              │
Retry Queue (TTL=3s)   ────────────┘
Retry Queue (TTL=9s)   ────────────┘
Retry Queue (TTL=27s)  ────────────┘
    ...
```

---

### Implementation

#### Step 1: Define Retry Queues

Define delay queues using 3^n exponential backoff.

```go
const MaxBackoff = 3600 // max delay in seconds

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

#### Step 2: Declare Retry Infrastructure

Configure TTL and DLX on each retry queue. When TTL expires, the message returns to the main queue via Default Exchange.

```go
const MainQueue = "task_queue"

func declareRetryInfra(ch *amqp.Channel) error {
    for _, rq := range RetryQueues {
        if _, err := ch.QueueDeclare(
            rq.Name,
            true, false, false, false,
            amqp.Table{
                "x-message-ttl":             int32(rq.TTL),
                "x-dead-letter-exchange":    "",        // Default Exchange
                "x-dead-letter-routing-key": MainQueue, // route back to main queue on expiry
            },
        ); err != nil {
            return err
        }
    }
    return nil
}
```

* `x-message-ttl`: message becomes dead letter after this duration (ms)
* `x-dead-letter-exchange: ""`: dead letter is forwarded to Default Exchange
* `x-dead-letter-routing-key: "task_queue"`: Default Exchange uses routing key as queue name, so message lands in the main queue

#### Step 3: Publish Retry Message

Send the message to the appropriate retry queue based on `tryCount`.

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
        queueName, // routing key = retry queue name
        false, false,
        amqp.Publishing{
            DeliveryMode: amqp.Persistent,
            ContentType:  "application/json",
            Body:         body,
        },
    )
}
```

#### Step 4: Call from Consumer

Replace the blocking `time.Sleep` with a `sendRetry` call.

```go
for d := range msgs {
    payload := parsePayload(d.Body)
    result := process(payload)

    switch result {
    case ActionOK:
        d.Ack(false)

    case ActionFailed:
        d.Reject(false) // discard, no retry

    case ActionRetry:
        d.Reject(false)        // remove current message from queue
        payload.TryCount++
        sendRetry(ch, payload) // enqueue to TTL queue and return immediately — no blocking
    }
}
```

### Full Message Flow

```
1. Producer publishes message to task_queue
2. Consumer receives and processes message
3. Failure (ActionRetry):
   a. d.Reject(false) removes the original message
   b. Increment tryCount and call sendRetry
   c. Select retry queue based on tryCount (e.g. retry_27s)
   d. Publish message to retry queue via Default Exchange
4. Message waits in retry queue for TTL (e.g. 27s)
5. TTL expires → dead letter triggered
6. Forwarded to Default Exchange via x-dead-letter-exchange=""
7. Routed to main queue via x-dead-letter-routing-key="task_queue"
8. Consumer receives again → back to step 2
```

---

## 11. Policy vs Queue Arguments

There are two ways to configure queue settings like TTL and DLX.

### Queue Arguments (configured in code)

```go
amqp.Table{
    "x-message-ttl":          int32(60000),
    "x-dead-letter-exchange": "",
}
```

* Defined directly in code at queue declaration time
* If the queue already exists with different arguments, RabbitMQ returns an error (the queue must be deleted and recreated to change arguments)
* Configuration lives in one place alongside the code

### Policy (configured on the server)

Apply settings to multiple queues at once via pattern matching, using the RabbitMQ Management UI or CLI:

```bash
rabbitmqctl set_policy my-ttl "^retry_.*" \
  '{"message-ttl": 60000, "dead-letter-exchange": ""}' \
  --apply-to queues
```

* Can be changed at runtime without redeployment
* A single pattern applies to multiple queues at once
* If both Queue Arguments and Policy are set, **the more conservative value wins**

### Which One to Use?

| Situation | Recommendation |
|-----------|---------------|
| Different TTL per queue (e.g. retry queues) | **Queue Arguments** — manage per-queue config in one place in code |
| Same settings across many queues | **Policy** — apply with a single pattern |
| Settings change frequently in production | **Policy** — no redeployment needed |

For patterns like the delayed retry covered in this document — where each queue has a different TTL — using Policy splits configuration across code and server, making it harder to manage. Queue Arguments are the better fit here.

That said, the official RabbitMQ docs strongly recommend Policy for production use.

For retry queues with different TTL values, **Queue Arguments are usually simpler to manage in code**, even though RabbitMQ documentation strongly recommends policies

---

## 12. References

* [RabbitMQ Official Documentation](https://www.rabbitmq.com/docs)
* [Queues — Optional Arguments](https://www.rabbitmq.com/docs/queues#optional-arguments)
* [Dead Lettering](https://www.rabbitmq.com/docs/dlx)
* [TTL (Time-To-Live)](https://www.rabbitmq.com/docs/ttl)
* [Policies and Parameters](https://www.rabbitmq.com/docs/parameters#policies)
* [AMQP 0-9-1 Model Explained](https://www.rabbitmq.com/tutorials/amqp-concepts)
* [Go AMQP Client (amqp091-go)](https://github.com/rabbitmq/amqp091-go)
