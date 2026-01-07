---
date: 2026-01-07
draft: false
title: OverTheWire Bandit(2)
categories: Linux
tags:
  - overthewire
  - bandit
author: grrru
---

> [OverTheWire: Bandit](https://overthewire.org/wargames/bandit/)  
> `Level 12`부터 ~

---
### Level 12
The password for the next level is stored in the file **data.txt**, which is a hexdump of a file that has been repeatedly compressed. For this level it may be useful to create a directory under /tmp in which you can work. Use mkdir with a hard to guess directory name. Or better, use the command “mktemp -d”. Then copy the datafile using cp, and rename it using mv (read the manpages!)

hexadump file을 압축 해제해가면서 원본 데이터 파일을 얻어야 한다.
```bash
mktemp -d
cp ~/data.txt /tmp/`위에서 만든 디렉토리`
```

`file *`로 얻은 파일이 어떤 방식으로 압축된 파일인지 확인 후 이에 맞는 압축 해제 방식을 사용해서 text 파일을 얻을 때까지 반복한다.

```sh
file *

xxd -r data.txt

gzip -dc data > data1
bzip2 -dc data1 > data2

mv data2 data2.tar
tar -xf data2.tar
```
위 3개만 반복해서 나왔던 듯.. 10번 정도 하면 text 파일이 나온다.

---
### Level 13
The password for the next level is stored in **/etc/bandit_pass/bandit14 and can only be read by user bandit14**. For this level, you don’t get the next password, but you get a private SSH key that can be used to log into the next level. Look at the commands that logged you into previous bandit levels, and find out how to use the key for this level.

`/etc/bandit_pass/bandit14`를 읽으면 되지만.. `bandit13`으로는 읽을 수 없다..
```bash
-r--------   1 bandit14 bandit14    33 Oct 14 09:25 bandit14
```

$HOME 디렉토리에 ssh key를 하나 주는데, 이걸로 `bandit14` 아이디로 접속할 수 있다.
```bash
cat ~/sshkey.private
```

근데 `sshkey.private`의 권한이 `640`으로 설정되어 있는데, private key를 ssh 접속에 사용하기 위해선 권한이 `600`이어야 한다!

```bash
-rw-r----- 1 bandit14 bandit13 1679 Oct 14 09:26 sshkey.private
```

`sshkey.private` 내용을 local 머신에 복사해와서 아무 파일에 저장해두고 `600`으로 바꾸고 `bandit14`에 접속해서 password를 획득한다.
```bash
vi key
~~~ key 적는 중 ~~~

ssh -i key bandit14@bandit.labs.overthewire.org -p 2220
cat /etc/bandit_pass/bandit14
```

---
### Level 14
The password for the next level can be retrieved by submitting the password of the current level to **port 30000 on localhost**.

`localhost:30000`으로 level 14의 passwd를 보내면 된다.

`nc`를 이용해서 30000번 포트로 비밀번호를 보내면 다음 레벨 비밀번호를 알려준다

```bash
echo MU4VWeTyJk8ROof1qqmcBPaLh7lDCPvS | nc localhost 30000
```

---
### Level 15
The password for the next level can be retrieved by submitting the password of the current level to **port 30001 on localhost** using SSL/TLS encryption.

**Helpful note: Getting “DONE”, “RENEGOTIATING” or “KEYUPDATE”? Read the “CONNECTED COMMANDS” section in the manpage.**

Level 14와 비슷하지만 이번 문제는 SSL/TLS encryption을 해서 30001포트에 보내야 한다.

`openssl`로 암호화 세션을 먼저 생성한다.
```bash
openssl s_client -connect localhost:30001
```
`s_client`는 SSL/TLS 세션을 연결하겠다는 뜻이다.  
세션이 연결되면 level14 password를 붙여넣는다.

---
### Level 16
The credentials for the next level can be retrieved by submitting the password of the current level to **a port on localhost in the range 31000 to 32000**. First find out which of these ports have a server listening on them. Then find out which of those speak SSL/TLS and which don’t. There is only 1 server that will give the next credentials, the others will simply send back to you whatever you send to it.

**Helpful note: Getting “DONE”, “RENEGOTIATING” or “KEYUPDATE”? Read the “CONNECTED COMMANDS” section in the manpage.**

31000 ~ 32000번 사이의 포트 중 `LISTENING` 상태이고 SSL/TLS 응답이 가능한 하나의 포트를 찾아야 한다. 이 중에 하나만 진짜인데, 나머지는 응답으로 내가 보낸 문자를 그대로 돌려준다.

```bash
ss -ltnp | grep -E ':31.*'
```

후보가 몇 개 없어서 하나하나 해봤다.
```bash
openssl s_client -connect localhost:31587 -quiet
```
`openssl s_client`는 보내는 문자열 시작이 `k`이면 데이터가 아니라 제어 명령으로 인식한다고 한다. level 16 password가 `k`로 시작해서 `KEYUPDATE`라는 응답을 받게 된다.  
이를 피하려면 `-quiet` 옵션을 붙여서 인터렉티브 모드로 들어가지 않도록 해야 한다.
`Correct!`가 나오면 RSA private key를 준다. (비밀번호가 아니라 credentials를 준다.)

---
### Level 17
There are 2 files in the homedirectory: **passwords.old and passwords.new**. The password for the next level is in **passwords.new** and is the only line that has been changed between **passwords.old and passwords.new**

**NOTE: if you have solved this level and see ‘Byebye!’ when trying to log into bandit18, this is related to the next level, bandit19**

`key`라는 파일을 만들고 안에 private key를 붙여넣고 `-i` 옵션을 이용해서 ssh 접속한다.
```bash
ssh bandit17@bandit.labs.overthewire.org -p 2220 -i key
```

`diff`로 두 파일을 한 line씩 비교해서 다른 라인을 찾는다. `password.new`에 있는 라인이 password다.
```bash
diff passwords.new passwords.old
```

---
### Level 18
The password for the next level is stored in a file **readme** in the homedirectory. Unfortunately, someone has modified **.bashrc** to log you out when you log in with SSH.

누군가 장난을 쳐서 로그인하자마자 로그아웃된다. `readme`를 읽으면 되므로 ssh 뒤에 command를 달아서 즉시 출력한다.  
command는 `;`로 여러 명렁을 구분할 수 있다.

```bash
ssh bandit18@bandit.labs.overthewire.org -p 2220 'ls -al;cat ~/readme'
```

---
### Level 19
To gain access to the next level, you should use the setuid binary in the homedirectory. Execute it without arguments to find out how to use it. The password for this level can be found in the usual place (/etc/bandit_pass), after you have used the setuid binary.

homedirectory에 있는 `setuid binary`를 이용하면 된다. 예시를 보려면 arguments 없이 써보라고 한다.

```bash
./bandit20-do
Run a command as another user.
  Example: ./bandit20-do whoami

./bandit20-do whoami
bandit20
```

`whoami`를 실행하니 다음 레벨 유저인 `bandit20`이 나온다.  `setuid binary`는 바이너리 파일의 소유자 권한으로 명령을 실행할 수 있는 파일이다. 위험하다.

```bash
./bandit20-do cat /etc/bandit_pass/bandit20
```

---
### Level 20
There is a setuid binary in the homedirectory that does the following: it makes a connection to localhost on the port you specify as a commandline argument. It then reads a line of text from the connection and compares it to the password in the previous level (bandit20). If the password is correct, it will transmit the password for the next level (bandit21).

**NOTE:** Try connecting to your own network daemon to see if it works as you think

`suconnect`라는 `setuid binary`는 임의 포트로 요청 시 요청받은 포트에서 `bandit20`의 password를 입력하면 다음 단계 password를 주는 파일이다.  
ssh 세션 두 개를 열어야 한다.
```bash
# 1번 세션
nc -l -p 1234

# 2번 세션
./suconnect 1234

# 1번 세션
[bandit20 passwd 입력 후 Enter]
```

