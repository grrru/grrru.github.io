---
date: 2026-01-13
draft: false
title: OverTheWire Bandit (4)
categories: Linux
tags:
  - linux
  - overthewire
  - bandit
author: grrru
---

### Level 28
There is a git repository at `ssh://bandit28-git@bandit.labs.overthewire.org/home/bandit28-git/repo` via the port `2220`. The password for the user `bandit28-git` is the same as for the user `bandit28`.

Clone the repository and find the password for the next level.

---

`git clone` 후 `README.md`를 까봤다.

```bash
git clone ssh://bandit28-git@bandit.labs.overthewire.org:2220/home/bandit28-git/repo

cd repo
cat README.md
```

```text
# Bandit Notes
Some notes for level29 of bandit.

## credentials

- username: bandit29
- password: xxxxxxxxxx
```
`README.md`에는 별 내용이 없다.  
`git log`를 확인했더니 `fix info leak`라는 커밋이 있다.

```text
* commit b0354c7be30f500854c5fc971c57e9cbe632fef6 (HEAD -> master, origin/master, origin/HEAD)
| Author: Morla Porla <morla@overthewire.org>
| Date:   Tue Oct 14 09:26:19 2025 +0000
|
|     fix info leak
|
* commit d0cf2ab7dd7ebc6075b59102a980155268f0fe8f
| Author: Morla Porla <morla@overthewire.org>
| Date:   Tue Oct 14 09:26:19 2025 +0000
|
|     add missing data
|
* commit bd6bc3a57f81518bb2ce63f5816607a754ba730d
  Author: Ben Dover <noone@overthewire.org>
  Date:   Tue Oct 14 09:26:18 2025 +0000

      initial commit of README.md
```

이전 커밋으로 되돌려 본다.
```bash
git reset --hard HEAD~1
cat README.md
```

### Level 29
There is a git repository at `ssh://bandit29-git@bandit.labs.overthewire.org/home/bandit29-git/repo` via the port `2220`. The password for the user `bandit29-git` is the same as for the user `bandit29`.

Clone the repository and find the password for the next level.

---

Level 28과 똑같이 `git`을 뒤져가며 찾는 문제다.  
`dev` branch로 바꾼 후에 `log`를 뒤져서 찾아냈다.
```bash
git switch dev
git log -p
```

`git log`에서 `-p` 옵션은 `diff`를 상세하게 보여주는 옵션이다.
```text
What the -p option produces is slightly different from the traditional diff format:
```

---

### Level 30
There is a git repository at `ssh://bandit30-git@bandit.labs.overthewire.org/home/bandit30-git/repo` via the port `2220`. The password for the user `bandit30-git` is the same as for the user `bandit30`.

Clone the repository and find the password for the next level.

---

`git branch -rvv`해도 branch는 하나밖에 없고 `git log`를 봐도 아무것도 없다.

```bash
git --no-pager log
```
> `git --no-pager`로 보면 commit id를 `pager` 없이 바로 출력할 수 있다.

`git tag`를 하니 단서가 나온다.
```bash
git tag
secret
```

그냥 바로 password같은 문자열이 나온다..!
```bash
git show secret
```

---

### Level 31
There is a git repository at `ssh://bandit31-git@bandit.labs.overthewire.org/home/bandit31-git/repo` via the port `2220`. The password for the user `bandit31-git` is the same as for the user `bandit31`.

Clone the repository and find the password for the next level.

---

`git clone`해오면 `README.md`가 있다.

```text
This time your task is to push a file to the remote repository.

Details:
    File name: key.txt
    Content: 'May I come in?'
    Branch: master
```

push를 하라는데, 이게 맞나 긴가민가했지만 써있는대로 `key.txt` 만들고 `May I come in?`이라고 쓰고 add했다.
```bash
git add key.txt
The following paths are ignored by one of your .gitignore files:
key.txt
hint: Use -f if you really want to add them.
hint: Disable this message with "git config set advice.addIgnoredFile false"
```
`.gitignore`에서 `*.txt`가 있어서 `-f`를 써야 한다.

```bash
git add -f key.txt
git commit -m "test"
git push

remote: Well done! Here is the password for the next level:
```
push는 안되지만 password를 알려준다.

---

### Level 32
After all this `git` stuff, it’s time for another escape. Good luck!

---
`git` 문제는 끝났다!

```bash
ssh bandit32@bandit.labs.overthewire.org -p 2220

WELCOME TO THE UPPERCASE SHELL
>>
>>
```

접속하면 `UPPERCASE SHELL`라는 쉘이 실행된다. 입력하는 모든 command를 대문자로 치환하는 쉘이다.

```bash
>> $SHELL
WELCOME TO THE UPPERCASE SHELL
```

> 문제 해결 후 회상  

`$0`을 입력하면 현재 실행 중인 쉘의 실행 경로가 입력되어 쉘이 재실행된다.  
이 문제의 세팅을 보면 login shell은 `uppershell`이다. 
```bash
cat /etc/passwd | grep bandit32
bandit32:x:11032:11032:bandit level 32:/home/bandit32:/home/bandit32/uppershell

echo $SHELL
/home/bandit32/uppershell
```

```bash
$ $0
$ echo $0
sh
```

`$0`을 실행하면 `sh`가 실행되는데, 이는 이 명령을 실행하던 shell이 `sh`였다는 뜻이다.  
로그인 직후 `uppershell`가 실행되고 얘가 `sh`를 실행했다는 뜻(?)인 듯 하다.  
여기서 `/usr/bin/bash`를 실행하면 bandit에서 보던 `bash` shell이 실행된다.
```bash
$ /usr/bin/bash
bandit33@bandit:~$
```

> 해결 방법
```bash
$0
cat /etc/bandit_pass/bandit33
```

exit하는 것도 어렵다
```bash
ps aux

USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1  0.0  0.0  14952  2928 ?        S    13:18   0:00 sshd: bandit32 [priv]
bandit32       2  0.0  0.1  14952  6948 ?        S    13:18   0:00 sshd: bandit32@pts/0
bandit33       3  0.0  0.0   2820  1508 pts/0    Ss   13:18   0:00 -uppershell
```

```bash
$ kill -term 3
Connection to bandit.labs.overthewire.org closed.
```

---

### Level 33
**At this moment, level 34 does not exist yet.**

That’s it!