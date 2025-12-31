---
date: 2025-12-28
draft: false
title: scp
category: Linux
tag:
  - scp
showAuthor: true
authors:
  - grrru
---

## 현재 조건 정리
- server1 -> server2 : ssh private key O
- server2 -> server1 : ssh private key X
- 목표: server2의 파일을 server1로 이동

## scp
- server1에서 실행
```bash
scp user2@server2:/src/file /dst/   # file
scp -r user2@server2:/src/dir /dst/ # directory

rsync -av user2@server2:/src/ /dst/ # 대용량 -> test는 안해봄
```
