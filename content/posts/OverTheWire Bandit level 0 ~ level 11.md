---
date: "2025-12-28"
draft: false
title: "OverTheWire Bandit(1)"
category: "Linux"
tag: 
  - "overthewire"
  - "bandit"
showAuthor: true
authors:
  - "grrru"
---

### OverTheWire Bandit
[OverTheWire: Bandit](https://overthewire.org/wargames/bandit/)

리눅스 연습!


> 각 단계에서 얻은 password로 다음 레벨의 아이디(e.g. `bandit1`)에 접속할 수 있다.

### level 0
ssh를 이용해서 `bandit0` 유저로`bandit.labs.overthewire.org:2220`에 접속하면 된다.

``` bash
ssh bandit.labs.overthewire.org -p 2220 -l bandit0
ssh bandit10@bandit.labs.overthewire.org -p 2220 ## host 앞에 user@를 붙이는 것도 가능하다
```

home directory에 있는 `readme`라는 파일을 읽어 `bandit1`의 password를 찾아낸다. 찾아낸 password는 로컬 머신에 복사해둬야 한다.
```bash
cat ~/readme
```

### level 1
home directory의  `-` 파일(dashed file)을 읽어야 한다.
(`ls -al`로 home directory의 파일들을 확인)

`-`라는 이름의 파일은 `cat -`로 바로 읽게 되면 아무 반응이 없는데, `-`가 표준 입력 `stdin`을 의미해서 입력을 기다리는 상태가 되기 때문이다.
```bash
bandit1@bandit:~$ cat -
hello
hello
```

아래와 같이 읽을 수 있다.
```bash
cat < - ## dashed file을 읽어 stdin으로 연결
cat ./- ## dashed file의 위치를 지정하여 읽음
```

### level 2
파일명에 공백이 있는 파일을 읽어야 한다. 공백 앞에 `\`를 붙여야 읽을 수 있다.

```bash
cat ./--spaces\ in\ this\ filename--
```

### level 3
`~/inhere` 디렉토리의 숨은 파일을 읽어야 한다. `ls`는 숨은 파일은 알려주지 않으므로 `ls -a`를 사용해야 한다.
```bash
ls -al ## a: all l: long-listing
cat ./...Hiding-From-You
```

나는 주로 `ls -al`을 사용하는데, `l` 옵션은 권한, 소유자, 그룹, 크기, 시간 등을 한 줄씩 출력해줘서 읽기 편한듯,,

### level 4
`human-readable` 파일을 읽어야 한다.
`file` 커맨드로 파일의 MIME 타입 등의 정보를 알 수 있다.
```bash
cd ~/inhere
file -i ./*
```
파일 하나만 `ASCII text`으로 사람이 읽을 수 있다.

### level 5
`inhere` 디렉토리에서 아래 조건을 만족하는 파일을 찾아서 읽어야 한다.
```text
- human-readable
- 1033 bytes in size
- not executable
```
`find .`는 현재 디렉토리 하위의 모든 파일과 디렉토리들을 보여준다.

```bash
find . -type f -size 1033c ! -executable
```

`-type`: 검색할 타입을 지정한다.

| type | 의미        |
| ----- | --------- |
| `f`   | 일반 파일     |
| `d`   | 디렉토리      |
| `l`   | 심볼릭 링크    |
| `c`   | 문자 디바이스   |
| `b`   | 블록 디바이스   |
| `p`   | 파이프(FIFO) |
| `s`   | 소켓        |

`-size`: 사이즈로 검색한다. 

| size | 의미                |
| ----- | ----------------- |
| `c`   | bytes             |
| `b`   | 512-byte blocks   |
| `k`   | kilobytes (1024B) |
| `M`   | megabytes         |
| `G`   | gigabytes         |
`-executable`: 실행 가능한 것을 의미하며 앞에 `!`을 붙여 부정으로 바꿀 수 있다.

### level 6
server 내의 어딘가에 있는 파일 중 아래 조건을 만족하는 파일을 읽어야 한다.
```text
owned by user bandit7
owned by group bandit6
33 bytes in size
```

```bash
find / -type f -size 33c -user bandit7 -group bandit6 2>/dev/null
```
`-user`, `-group`로 owner 검색이 가능하다.
`2>/dev/null`를 쓰지 않으면 `find` 커맨드 실행 중 권한이 없는 디렉토리/파일을 만날 때 에러 메시지 `Permission Denied`를 `stderr`(FD 2)로 출력한다.
`2>/dev/null`은 sderr 2를 `/dev/null`로 리다이렉션(`>`)하여 에러 출력이 버려지도록 한다.

### level 7
겁나 큰 용량의 `data.txt` 파일 내에서 `millionth`라는 단어의 옆에 써있는 password를 읽어야 한다.
```bash
ls -lh ## h: human 옵션으로 용량 값을 읽기 쉽도록 바꿔준다.
cat data.txt | grep millionth
```
### level 8
`data.txt` 에서 유일한 line을 찾아야 한다.
```bash
sort data.txt | uniq -iu
```
`sort`로 파일의 line들을 정렬한다. 여러 옵션을 추가로 사용할 수 있다.
`uniq` 커맨드는 중복되는 line을 제거하고 출력해준다. `-d`는 중복된 내용만 출력, `-u`는 고유한 내용만 출력, `-i`는 대소문자 구분 무시 옵션이다.

### level 9
`data.txt`에서 읽을 수 있는, `=`가 앞에 있는 문자열만을 출력해야 한다.
```bash
file data.txt ## data.txt: data
strings data.txt | grep '='
```
`strings`는 파일에 포함된 string을 뽑아낼 수 있다.

### level 10
base64 인코딩된 문자열이 `data.txt`에 들어있다.
```bash
cat data.txt | base64 -d
```
`base64 -d` 커맨드로 문자열을 디코딩하여 원래 바이너리를 출력한다.

### level 11
[시저 암호](https://www.acmicpc.net/problem/1893)가 적용된 `data.txt` 파일을 해석해야 한다. Rot13이므로 A → N Z→ M으로 치환한다.

정규식은 아니라고 한다.. (`tr`에서 쓰인 규칙일 뿐)
```bash
cat data.txt | tr '[A-Za-z]' '[N-ZA-Mn-za-m]'
```

