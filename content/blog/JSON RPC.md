---
date: 2026-01-30
draft: false
title: "JSON RPC"
categories: ["backend"]
tags: ["JSON-RPC"]
author: "grrru"
---

## 1. JSON

Stands for JavaScript Object Notation, a collection of `key-value` pairs.

```json
{
  "name": "Hong Gil-dong",
  "age": 25,
  "gender": "male",
  "job": "student",
  "hobbies": ["reading", "movies", "exercise"]
}
```

JSON has a concise syntax and is parsed faster than XML.

---

## 2. JSON RPC

`RPC` stands for Remote Procedure Call, a communication technology that allows calling programs (functions/procedures) on another computer connected via a network as if they were local functions, without separate remote control coding.

### How JSON RPC Works

- The client creates a JSON-formatted message and sends it to the server.
- The server processes the message and sends the result back to the client as a JSON-formatted message.

### JSON RPC Components

1. Request

- `jsonrpc`: Version (e.g., "2.0")
- `method`: Name of the remote procedure to be executed
- `params`: Parameters to be passed to the function
- `id`: A unique identifier set by the client

1. Response

- `jsonrpc`: Version (e.g., "2.0")
- `result`: Result data
- `error`: Error object in case of method failure
- `id`: The same identifier as in the request object

---

## 3. Advantages of JSON RPC

It is simple, intuitive, language-independent, efficient for network communication, highly scalable, and easy to handle errors.

---

## 4. Reference

- [# What is JSON RPC?](https://lab.wallarm.com/what/json-rpc%EB%9E%80-%EB%AC%B4%EC%97%87%EC%9D%B8%EA%B0%80/?lang=ko)

---
