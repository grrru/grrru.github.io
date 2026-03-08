---
date: 2025-12-28
draft: false
title: OverTheWire Bandit (1)
categories: ["Linux"]
tags: ["linux", "overthewire", "bandit"]
author: "grrru"
---

## 0. OverTheWire Bandit
[OverTheWire: Bandit](https://overthewire.org/wargames/bandit/)

Practice Linux!
> You can connect to the next level's user (e.g., `bandit1`) using the password obtained in each stage.

---
## 1. level 0
The password for the next level is stored in a file called **readme** located in the home directory. Use this password to log into bandit1 using SSH. Whenever you find a password for a level, use SSH (on port 2220) to log into that level and continue the game.

---

Connect to `bandit.labs.overthewire.org:2220` as the `bandit0` user via SSH.

``` bash
ssh bandit.labs.overthewire.org -p 2220 -l bandit0
ssh bandit10@bandit.labs.overthewire.org -p 2220 ## You can also use user@host format
```

Read the file named `readme` in the home directory to find the password for `bandit1`. Make sure to copy the found password to your local machine.
```bash
cat ~/readme
```

---
## 2. level 1
The password for the next level is stored in a file called **-** located in the home directory

---

You need to read the `-` file (dashed file) in the home directory.
(Check the files in the home directory using `ls -al`)

If you try to read a file named `-` using `cat -` directly, there is no response because `-` signifies standard input (`stdin`), causing it to wait for input.
```bash
bandit1@bandit:~$ cat -
hello
hello
```

You can read it like this:
```bash
cat < - ## Read the dashed file and connect it to stdin
cat ./- ## Read by specifying the file's location
```

---
## 3. level 2
The password for the next level is stored in a file called `--spaces in this filename--` located in the home directory

---

You need to read a file with spaces in its name. You must add `\` before spaces to read it.

```bash
cat ./--spaces\ in\ this\ filename--
```

---
## 4. level 3
The password for the next level is stored in a hidden file in the **inhere** directory.

---

You need to read a hidden file in the `~/inhere` directory. Since `ls` doesn't show hidden files, use `ls -a`.
```bash
ls -al ## a: all, l: long-listing
cat ./...Hiding-From-You
```

`ls -al` is commonly used as the `l` option provides permissions, owner, group, size, and time in a line-by-line format, making it easy to read.

---
## 5. level 4
The password for the next level is stored in the only human-readable file in the **inhere** directory. Tip: if your terminal is messed up, try the “reset” command.

---

You need to read a `human-readable` file.
The `file` command can provide information such as the file's MIME type.
```bash
cd ~/inhere
file -i ./*
```
Only one file will be `ASCII text`, which is human-readable.

---
## 6. level 5
The password for the next level is stored in a file somewhere under the **inhere** directory and has all of the following properties:

---

Find and read a file in the `inhere` directory that meets the following criteria:
```text
- human-readable
- 1033 bytes in size
- not executable
```
`find .` shows all files and directories under the current directory.

```bash
find . -type f -size 1033c ! -executable
```

`-type`: Specifies the type to search for.

| type  | Meaning          |
| ----- | ---------------- |
| `f`   | Regular file     |
| `d`   | Directory        |
| `l`   | Symbolic link    |
| `c`   | Character device |
| `b`   | Block device     |
| `p`   | Pipe (FIFO)      |
| `s`   | Socket           |

`-size`: Searches by size.

| size | Meaning            |
| ----- | ------------------ |
| `c`   | bytes              |
| `b`   | 512-byte blocks    |
| `k`   | kilobytes (1024B)  |
| `M`   | megabytes          |
| `G`   | gigabytes          |

`-executable`: Refers to executable items; adding `!` negates it.

---
## 7. level 6
The password for the next level is stored **somewhere on the server** and has all of the following properties:

---

Read a file located somewhere on the server that meets these conditions:
```text
owned by user bandit7
owned by group bandit6
33 bytes in size
```

```bash
find / -type f -size 33c -user bandit7 -group bandit6 2>/dev/null
```
You can search by owner using `-user` and `-group`.
Without `2>/dev/null`, the `find` command will output `Permission Denied` error messages to `stderr` (FD 2) when encountering directories/files without access.
`2>/dev/null` redirects `stderr` (2) to `/dev/null`, discarding the error output.

---
## 8. level 7
The password for the next level is stored in the file **data.txt** next to the word **millionth**

---

Find the password next to the word `millionth` within the very large `data.txt` file.
```bash
ls -lh ## h: human option makes size values easier to read.
cat data.txt | grep millionth
```

---
## 9. level 8
The password for the next level is stored in the file **data.txt** and is the only line of text that occurs only once

---

Find the unique line in `data.txt`.
```bash
sort data.txt | uniq -iu
```
`sort` arranges the lines of the file. You can use various additional options.
The `uniq` command removes duplicate lines and outputs the result. `-d` outputs only duplicates, `-u` outputs only unique content, and `-i` ignores case.

---
## 10. level 9
The password for the next level is stored in the file **data.txt** in one of the few human-readable strings, preceded by several ‘=’ characters.

---

Output only the readable strings in `data.txt` that are preceded by `=`.
```bash
file data.txt ## data.txt: data
strings data.txt | grep '='
```
`strings` extracts strings contained in a file.

---
## 11. level 10
The password for the next level is stored in the file **data.txt**, which contains base64 encoded data

---

`data.txt` contains a base64 encoded string.
```bash
cat data.txt | base64 -d
```
The `base64 -d` command decodes the string and outputs the original binary.

---
## 12. level 11
The password for the next level is stored in the file **data.txt**, where all lowercase (a-z) and uppercase (A-Z) letters have been rotated by 13 positions

---

You need to decrypt the `data.txt` file, which uses a [Caesar Cipher](https://en.wikipedia.org/wiki/Caesar_cipher). Since it's Rot13, substitute A → N and Z → M.

Note: These are not exactly regular expressions (just rules used in `tr`).
```bash
cat data.txt | tr '[A-Za-z]' '[N-ZA-Mn-za-m]'
```
