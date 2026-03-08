---
date: 2026-01-11
draft: false
title: OverTheWire Bandit (3)
categories: Linux
tags:
  - linux
  - overthewire
  - bandit
author: grrru
---

### Level 21
A program is running automatically at regular intervals from **cron**, the time-based job scheduler. Look in **/etc/cron.d/** for the configuration and see what command is being executed.

---

주기적으로 실행되는 crontab이 힌트를 줄 것이다.  
`/etc/cron.d`를 보라니깐 거기로 가본다.  
```bash
cd /etc/cron.d/
ll

-rw-r--r--   1 root root   120 Oct 14 09:26 cronjob_bandit22
```

`cronjob_bandit22`를 까본다. (-644로 other이 읽을 수 있다.)

```bash
cat cronjob_bandit22
@reboot bandit22 /usr/bin/cronjob_bandit22.sh &> /dev/null
* * * * * bandit22 /usr/bin/cronjob_bandit22.sh &> /dev/null
```

```bash
cat /usr/bin/cronjob_bandit22.sh

#!/bin/bash
chmod 644 /tmp/t7O6lds9S0RqQh9aMcz6ShpAoZKF7fgv
cat /etc/bandit_pass/bandit22 > /tmp/t7O6lds9S0RqQh9aMcz6ShpAoZKF7fgv
```

sh 파일을 까보면 `/etc/bandit_pass/bandit22` 파일을 `/tmp/t7O6lds9S0RqQh9aMcz6ShpAoZKF7fgv`에 매 분마다 넣고 있음을 볼 수 있다.

```bash
cat /tmp/t7O6lds9S0RqQh9aMcz6ShpAoZKF7fgv
```

---
### Level 22
A program is running automatically at regular intervals from **cron**, the time-based job scheduler. Look in **/etc/cron.d/** for the configuration and see what command is being executed.

**NOTE:** Looking at shell scripts written by other people is a very useful skill. The script for this level is intentionally made easy to read. If you are having problems understanding what it does, try executing it to see the debug information it prints.

---

남이 쓴 sh를 읽는 건 useful skill이다!
```bash
cat /etc/cron.d/cronjob_bandit23
@reboot bandit23 /usr/bin/cronjob_bandit23.sh  &> /dev/null
* * * * * bandit23 /usr/bin/cronjob_bandit23.sh  &> /dev/null
```

```bash
cat /usr/bin/cronjob_bandit23.sh
#!/bin/bash

myname=$(whoami)
mytarget=$(echo I am user $myname | md5sum | cut -d ' ' -f 1)

echo "Copying passwordfile /etc/bandit_pass/$myname to /tmp/$mytarget"

cat /etc/bandit_pass/$myname > /tmp/$mytarget
```

그냥 shell 스크립트에 적힌대로 따라해서 비밀번호 위치를 알아내(면 안된다!)..
sh 내에서 실행한 `whoami`는 crontab으로 실행되고 있는데 crontab을 실행시키는 주체가 `bandit23`이다. (`* * * * * bandit23 /usr/bin/cronjob_bandit23.sh  &> /dev/null`)
따라서 myname=bandit23으로 넣어줘야 한다.

```bash
myname=bandit23
mytarget=$(echo I am user $myname | md5sum | cut -d ' ' -f 1)
cat /tmp/$mytarget
```


### Level 23
A program is running automatically at regular intervals from **cron**, the time-based job scheduler. Look in **/etc/cron.d/** for the configuration and see what command is being executed.

**NOTE:** This level requires you to create your own first shell-script. This is a very big step and you should be proud of yourself when you beat this level!

**NOTE 2:** Keep in mind that your shell script is removed once executed, so you may want to keep a copy around…

---

습관적으로 열어본다.
```bash
cat /etc/cron.d/cronjob_bandit24
@reboot bandit24 /usr/bin/cronjob_bandit24.sh &> /dev/null
* * * * * bandit24 /usr/bin/cronjob_bandit24.sh &> /dev/null
```

```bash
cat /usr/bin/cronjob_bandit24.sh
#!/bin/bash

myname=$(whoami)

cd /var/spool/$myname/foo
echo "Executing and deleting all scripts in /var/spool/$myname/foo:"
for i in * .*;
do
    if [ "$i" != "." -a "$i" != ".." ];
    then
        echo "Handling $i"
        owner="$(stat --format "%U" ./$i)"
        if [ "${owner}" = "bandit23" ]; then
            timeout -s 9 60 ./$i
        fi
        rm -f ./$i
    fi
done
```

`cronjob_bandit24.sh`를 열어 보면 긴 스크립트가 나오는데, `/var/spool/bandit24/foo` 디렉토리의 모든 파일(`*`, `.*`)을 순회하면서 `.`, `..`를 제외한 파일들에 대해 `owner`가 `bandit23`이면 timeout 60초를 걸고 `-s 9` (SIGKILL) 강제종료하고 그 파일을 실행시킨 후 강제 삭제한다.  
우리가 읽어야 할 파일이 `/etc/bandit_pass/bandit24`에 있는데 `bandit24`로 읽을 수 있다.  
crontab은 `bandit24`로 실행되고 있고 `/foo` 하위 모든 파일을 실행시키므로, `bandit24`이 실행 가능한 shell script를 만들고 `/foo` 하위에 넣어둔 뒤 password 파일을 우리가 원하는 파일로 쓰도록 하면 된다.  

```bash
drwxrwx-wt 5420 root root 10244096 Jan 10 07:31 tmp/
```
`/tmp` 디렉토리는 `other`의 권한이 `-wt`인데 여기서 `t`는 sticky bit로, `/tmp` 하위 파일들은 owner만이 삭제가 가능하다. `/tmp/grrru.sh`를 만든다.
```bash
vi /tmp/grrru.sh
```

```bash
#!/bin/bash

touch /tmp/asdfghjkl
cat /etc/bandit_pass/bandit24 > /tmp/asdfghjkl
```

대충 비밀번호 가져올 파일 하나 생성해서 넣어주는 식으로 만들었다. `grrru.sh`를 실행할 주체는 `bandit24`(cronjob이 실행하므로)이므로 `other`에 `x`권한을 줘야 한다.

```bash
chmod 665 /tmp/grrru.sh

ll grrru.sh
-rw-rw-r-x 1 bandit23 bandit23 127 Jan 10 07:41 grrru.sh*
```

crontab이 순회하는 디렉토리로 `grrru.sh`를 복사한다.
```bash
cp /tmp/grrru.sh /var/spool/bandit24/foo/
```

이러고 1분 기다리면 cronjob이 돌아서 `grrru.sh`를 실행해준 뒤 삭제한다.

```bash
cat /tmp/asdfghjkl
```

---

### Level 24
A daemon is listening on port 30002 and will give you the password for bandit25 if given the password for bandit24 and a secret numeric 4-digit pincode. There is no way to retrieve the pincode except by going through all of the 10000 combinations, called brute-forcing.  
You do not need to create new connections each time

---

`localhost:30002`로 `$PASSWORD 0000` 꼴의 데이터를 보내면 답을 주는데, 정답 pin을 찾아야 다음 비밀번호를 알려준다.
```bash
Wrong! Please enter the correct current password and pincode. Try again.

Correct!
The password of user bandit25 is iCi86ttT4KSNe1armKiwbQNmB3YJP3q4
```

0000 ~ 9999를 하나씩 보낼 수도 있지만, connection을 한 번 만들면 pin 하나 보낼 때마다 또 연결할 필요가 없다고 하니 script를 작성해서 한 번에 보내보자.
```bash
vi /tmp/grrru24.sh
```

`grrru24` 파일을 만들고 한 줄씩 전송할 문자열을 생성해둔다.

```bash
#!/bin/bash

rm -f /tmp/grrru24
touch /tmp/grrru24
chmod 600 /tmp/grrru24

PASSWORD=gb8KRRCsshuZXI0tUuR6ypOFjiZbf3G8


for ((i=0; i<10000; i++));do
        echo "$i"

        printf "%s %04d\n" "$PASSWORD" "$i" >> /tmp/grrru24
done
```

뭔가 중간에 `Correct!`가 나와서 못찾을 줄 알았는데 맨 아랫 줄에 나왔다. (사람마다 다를수도,,)
```bash
./grrru24.sh
```

---
### Level 25
Logging in to bandit26 from bandit25 should be fairly easy… The shell for user bandit26 is not **/bin/bash**, but something else. Find out what it is, how it works and how to break out of it.

> NOTE: if you’re a Windows user and typically use Powershell to `ssh` into bandit: Powershell is known to cause issues with the intended solution to this level. You should use command prompt instead.

---

`bandit26`의 기본 쉘은 `/bin/bash`가 아니다. 어떤 쉘을 기본으로 사용하는지 먼저 확인한다.

```bash
cat /etc/passwd | grep bandit26
bandit26:x:11026:11026:bandit level 26:/home/bandit26:/usr/bin/showtext
```
`/usr/bin/showtext`를 기본 쉘로 사용하고 있다.
```bash
cat /usr/bin/showtext
#!/bin/sh

export TERM=linux

exec more ~/text.txt
exit 0
```

> 머신에 로그인한 직후 실행되는 `기본 쉘(login shell)`은  
> `/bin/bash` 같은 쉘 프로그램뿐 아니라, 
> 실행 권한이 있는 임의의 실행 파일(ELF 바이너리 또는 `.sh` 스크립트)도 될 수 있다.
> ```bash
> file /usr/bin/showtext
> /usr/bin/showtext: POSIX shell script, ASCII text executable
> ```

`/usr/bin/showtext`에서는 `more ~/text.txt`를 실행 후 즉시 종료된다.

`bandit25`로 접속하면 HOME 디렉토리에 `bandit26.key`가 있는데 이걸로 Level 25를 풀어야 하므로 `scp`로 local에 가져오거나 `bandit25` 쉘에서 바로 ssh 접속하거나 해야 한다.

```bash
ssh bandit26@bandit.labs.overthewire.org -p 2220 -i bandit26.sshkey
```

위 `ssh` 접속을 하면 바로 나와지는데, `bandit26`이라는 아스키아트(?)를 보여주고 바로 종료된다. `more` 커맨드를 통해 출력된 그림인데, `more` 커맨드는 표준 출력이 `TTY(터미널)`인 경우에 화면 높이를 계산해서 출력해야 할 줄 수보다 화면 높이가 작다면 `--More--`이 뜨면서 pager 모드로 전환된다고 한다.  
그래서 화면 높이를 작게 줄여서 다시 접속한다. ASCII 아트 높이가 6이니깐 6보다 작으면 될 듯 하다.

```bash
  _                     _ _ _   ___   __
 | |                   | (_) | |__ \ / /
 | |__   __ _ _ __   __| |_| |_   ) / /_
--More--(50%)
```

`--More--`과 함꼐 Paging 모드로 들어왔다. `Enter`를 치면 한 줄씩 보여주고, `위 화살표`를 누르면 다시 올라간다.  
리눅스에서 `more` 명령어 실행 중 `v`를 누르면 현재 위치에서 `vi` 편집기를 실행하여 파일을 편집할 수 있다.  
```bash
v
```

`vi` 편집기에서 `:set shell?`를 하면 현재 쉘 설정을 볼 수 있다.
```bash
:set shell?
shell=/usr/bin/showtext
```

현재 접속 id가 `bandit26`이므로 `vi` 편집기 내에서 shell을 `/bin/bash`로 바꾸면 `:sh`를 통해 현재 `vi` 세션 내에서 새로운 쉘을 실행할 수 있다.

```bash
:set shell=/bin/bash
:sh
```

원하는 비밀번호를 가져온다.
```bash
bandit26@bandit:~$ cat /etc/bandit_pass/bandit26
s0773xxkk0MXfdqOfPRVr9L3jJBUOgCZ
```

> 여기서 나가지 않고 Level 26을 바로 할 수 있다.

---

### Level 26
Good job getting a shell! Now hurry and grab the password for bandit27!

---

`HOME`으로 가서 `ls`를 실행하면 `bandit27-do`가 보인다.
```bash
file ./bandit27-do
./bandit27-do: setuid ELF 32-bit LSB executable, Intel 80386, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux.so.2, BuildID[sha1]=35d353cf6d732f515a73f50ed205265fe1e68f90, for GNU/Linux 3.2.0, not stripped
```

저번에 봤던 `setuid`파일이다.
```bash
./bandit27-do id
uid=11026(bandit26) gid=11026(bandit26) euid=11027(bandit27) groups=11026(bandit26)
```

리눅스/유닉스 계열 운영체제에서 `setuid`같은 특정 권한이 설정된 파일을 실행하면 일시적으로 파일 소유자나 다른 사용자의 권한(EUID)를 획득해서 시스템 리소스에 접근할 수 있다.  
`euid=11027(bandit27)`로 되어있으므로 이 파일을 이용해서 `bandit27` 파일을 읽을 수 있다.
```bash
./bandit27-do cat /etc/bandit_pass/bandit27
```

---

### Level 27
There is a git repository at `ssh://bandit27-git@bandit.labs.overthewire.org/home/bandit27-git/repo` via the port `2220`. The password for the user `bandit27-git` is the same as for the user `bandit27`.

Clone the repository and find the password for the next level.

---

`bandit27`로 접속해서 `git clone`을 시도했다.

```bash
cd /tmp
git clone ssh://bandit27-git@bandit.labs.overthewire.org:2220/home/bandit27-git/repo
```

근데 이러니깐 localhost에서 localhost로 `ssh` 접속은 리소스 절약을 위해 차단되었다고 한다.
```text
!!! You are trying to log into this SSH server with a password on port 2220 from localhost.
!!! Connecting from localhost is blocked to conserve resources. 
!!! Please log out and log in again.
```

그래서 그냥 local 머신에서 바로 `git clone`해서 `README`를 읽었다.
