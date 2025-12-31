---
date: "2025-12-31"
draft: true
title: "OverTheWire Bandit(2)"
category: "Linux"
tag: 
  - "overthewire"
  - "bandit"
showAuthor: true
authors:
  - "grrru"
---

[OverTheWire: Bandit](https://overthewire.org/wargames/bandit/)

> Level 12부터 ~

### Level 12
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

### Level 13
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

`sshkey.private` 내용을 local 머신에 복사해와서 아무 파일에 저장해두고 `600`으로 바꾸고 `bandit14`에 접속해서 password를 획득한다!
```bash
vi key
~~~ key 적는 중 ~~~

ssh -i key bandit14@bandit.labs.overthewire.org -p 2220
cat /etc/bandit_pass/bandit14
```


