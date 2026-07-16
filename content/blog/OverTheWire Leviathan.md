---
date: 2026-07-16
draft: true
title: OverTheWire Leviathan (1)
categories: Linux
tags:
  - linux
  - overthewire
  - leviathan
author: grrru
---

> https://overthewire.org/wargames/leviathan/

To login to the first level use:

Username: leviathan0
Password: leviathan0

Leviathan은 Level0 password만 알려주고 그 뒤로는 아무런 정보를 주지 않는다.

## 1. Level 0

```bash
leviathan0@leviathan:~$ ll
total 24
drwxr-xr-x   3 root       root       4096 Jun 24 15:00 ./
drwxr-xr-x 150 root       root       4096 Jun 24 15:02 ../
drwxr-x---   2 leviathan1 leviathan0 4096 Jun 24 15:00 .backup/
-rw-r--r--   1 root       root        220 Feb 13 12:16 .bash_logout
-rw-r--r--   1 root       root       3851 Jun 24 14:50 .bashrc
-rw-r--r--   1 root       root        807 Feb 13 12:16 .profile
```

`.backup`이라는 dir이 있다. group이 leviathan0이어서 읽을 수 있다.


```bash
leviathan0@leviathan:~/.backup$ ll
total 140
drwxr-x--- 2 leviathan1 leviathan0   4096 Jun 24 15:00 ./
drwxr-xr-x 3 root       root         4096 Jun 24 15:00 ../
-rw-r----- 1 leviathan1 leviathan0 133259 Jun 24 15:00 bookmarks.html
```

`bookmarks.html`이라는 수상한 파일이 있다. 출력해보면 엄청 길게 나온다.
대충 `grep leviathan`해보니 leviathan1 password가 나왔다!

```bash
leviathan0@leviathan:~/.backup$ cat bookmarks.html | grep leviathan
<DT><A HREF="http://leviathan.labs.overthewire.org/passwordus.html | This will be fixed later, the password for leviathan1 is PiXaSWQqHq" ADD_DATE="1155384634" LAST_CHARSET="ISO-8859-1" ID="rdf:#$2wIU71">password to leviathan1</A>
```

## 2. Level 1


## 3. Level 2

## 4. Level 3

## 5. Level 4

## 6. Level 5

## 7. Level 6
