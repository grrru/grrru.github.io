---
date: 2025-12-28
draft: false
title: "scp"
categories: ["Linux"]
tags: ["scp"]
author: "grrru"
---

## Current Situation
- server1 -> server2: SSH private key available
- server2 -> server1: SSH private key NOT available
- Goal: Move files from server2 to server1

## scp
- Run from server1
```bash
scp user2@server2:/src/file /dst/   # file
scp -r user2@server2:/src/dir /dst/ # directory

rsync -av user2@server2:/src/ /dst/ # For large volumes -> haven't tested this yet
```
