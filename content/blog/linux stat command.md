---
date: 2026-08-05
draft: false
title: Linux stat command
categories: Linux
tags:
  - linux
author: grrru
---

간단하게 자주 쓸 것 같은 Linux machine stat 관련 커맨드 정리

## 1. OS / 커널

| 명령어                   | 용도                                       |
| --------------------- | ---------------------------------------- |
| `uname -a`            | 커널 버전, 아키텍처 한 줄 요약                       |
| `cat /etc/os-release` | 배포판 이름·버전                                |
| `hostnamectl`         | hostname, Machine ID, OS, Kernel, Arch 등 |
| `uptime`              | 부팅 후 경과 시간, load average                 |

## 2. CPU

| 명령어                 | 용도                                |
| ------------------- | --------------------------------- |
| `lscpu`             | Architecture, Caches 등의 CPU 상세 정보 |
| `nproc`             | 논리 코어 개수                          |
| `cat /proc/cpuinfo` | 코어별 raw 정보                        |
| `mpstat`            | CPU 사용률                           |

## 3. 메모리

| 명령어                           | 용도                            |
| ----------------------------- | ----------------------------- |
| `free -h`                     | 총량/사용/available               |
| `cat /proc/meminfo`           | 상세 (Dirty, Slab, HugePages 등) |
| `vmstat`                      | memory, swap, io 정보           |
| `ps aux --sort=-%mem \| head` | 메모리 많이 먹는 프로세스 top            |

## 4. 디스크 / 스토리지

| 명령어     | 용도            |
| ------- | ------------- |
| `df -h` | 마운트별 용량       |
| `lsblk` | 블록 디바이스 트리 구조 |


