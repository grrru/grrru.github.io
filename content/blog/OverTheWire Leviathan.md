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

대충 `grep leviathan`를 찍어보니 leviathan1 password가 나왔다!

```bash
leviathan0@leviathan:~/.backup$ cat bookmarks.html | grep leviathan
<DT><A HREF="http://leviathan.labs.overthewire.org/passwordus.html | This will be fixed later, the password for leviathan1 is PiXaSWQqHq" ADD_DATE="1155384634" LAST_CHARSET="ISO-8859-1" ID="rdf:#$2wIU71">password to leviathan1</A>
```

## 2. Level 1

```bash
leviathan1@leviathan:~$ ls -lh
total 16K
-r-sr-x--- 1 leviathan2 leviathan1 15K Jun 24 15:00 check
leviathan1@leviathan:~$ ./check
password: PiXaSWQqHq
Wrong password, Good Bye ...
```

check라는 executable 파일이 있다. group 권한으로 실행 가능해서 실행해봤다. leviathan1의 password를 입력하면 실패한다.

check 파일의 owner의 모드가 `r-s`인데, 여기서 `s`는 `Set ID`를 뜻한다. user permissions의 `x` 자리에 `s`가 있으므로 이 파일을 실행하면 user permissions으로 실행하도록 해준다는 뜻이다.

> ltrace는 리눅스 환경에서 프로그램이 실행되는 동안 호출하는 동적 라이브러리(Shared Library) 함수를 추적하고 분석하는 디버깅 유틸리티입니다.  
> 주로 소스 코드가 없는 프로그램의 동작을 파악하거나 성능 문제를 진단할 때 사용됩니다.

ltrace를 사용하면 executable 파일 등 소스코드를 볼 수 없는 프로그램을 디버깅할 수 있다.

```bash
leviathan1@leviathan:~$ ltrace -C ./check
__libc_start_main(["./check"] <unfinished ...>
printf("password: ")                                                                                             = 10
getchar(0xf7fc5310, 0xf7fc3000, 0x786573, 0x646f67password: test
)                                                              = 116
getchar(0xf7fc5310, 0xf7fc3074, 0x786573, 0x646f67)                                                              = 101
getchar(0xf7fc5310, 0xf7fc6574, 0x786573, 0x646f67)                                                              = 115
strcmp("tes", "sex")                                                                                             = 1
puts("Wrong password, Good Bye ..."Wrong password, Good Bye ...
)                                                                             = 29
+++ exited (status 0) +++
 ``` 

여기서 `-C`는 decode low-level symbol names into user-level names.

대충 `test`를 password로 입력해봤다. `strcmp("tes", "sex")`라는 함수를 사용한 걸 보니 세 자리까지만 입력을 받고 뒤의 단어와 비교해서 일치하는지 보는 것 같다.

```bash
leviathan1@leviathan:~$ ./check
password: sex
$ whoami && pwd
leviathan2
/home/leviathan1
 ```

`leviathan2`로 접속하는 데 성공했다.

```bash
$ cd /etc/leviathan_pass
$ cat leviathan2
ERJ9jTYWXE
```

## 3. Level 2

## 4. Level 3

## 5. Level 4

## 6. Level 5

## 7. Level 6
