---
date: 2026-06-06
draft: false
title: HMAC
categories: security
tags:
  - hmac
  - hash
  - security
author: grrru
---

## HMAC

HMAC은 메시지가 중간에 변조되지 않았는지 확인하기 위한 Hash-based Message Authentication Code다.

메시지 원문은 그대로 전송하고, 다만 송신/수신처만 알고 있는 secret key로 HMAC 검증값을 만들어서 메시지와 함께 보낸다.

따라서 메시지 자체를 암호화하는 것은 아니다.

```text
HMAC = hash(secret key + message)
```


### 동작 방식

1. 송신자와 수신자가 같은 비밀키 `K`를 공유한다.
2. 송신자는 메시지 `M`과 `K`로 HMAC 값을 만든다.
3. 송신자는 `M`과 HMAC 값을 함께 보낸다.
4. 수신자는 받은 메시지 `M'`과 자신의 `K`로 HMAC 값을 다시 계산한다.
5. 수신자가 만든 HMAC 값이 송신자로부터 온 HMAC값과 같으면 메시지가 변조되지 않았다고 판단한다.

## 키 교환 알고리즘

HMAC이나 대칭키 암호화 방식같이 서버-클라이언트가 동일한 secret key를 가져야 하는 경우, 안전하게 키 교환을 해야 하는데 이때 사용되는 방법이 키 교환 알고리즘이다.

### Diffie-Hellman

오래된 유명한 알고리즘이다. 두 사람이 각자 비밀값을 만들고 이걸로 상대방의 응답값을 받아서 해석하면 서로의 비밀키를 얻을 수 있다.



공개값 `g`, `p`는 누구나 알아도 되고, 각자의 비밀값 `a`, `b`는 자기만 가지고 있는다.

```text
A = g^a mod p
B = g^b mod p
K = B^a mod p = A^b mod p
```

서로 `A`, `B`만 교환한 뒤 각자의 비밀값으로 한 번 더 계산하면, 양쪽 모두 같은 최종 secret key `K`를 얻는다.
