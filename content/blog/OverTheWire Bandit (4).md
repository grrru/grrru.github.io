---
date: 2026-01-13
draft: false
title: OverTheWire Bandit (4)
categories: ["Linux"]
tags: ["linux", "overthewire", "bandit"]
author: "grrru"
---

## 1. level 28
There is a git repository at `ssh://bandit28-git@bandit.labs.overthewire.org/home/bandit28-git/repo` via the port `2220`. The password for the user `bandit28-git` is the same as for the user `bandit28`.

Clone the repository and find the password for the next level.

---

After `git clone`, I checked `README.md`.

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
There wasn't much in `README.md`.
I checked `git log` and found a commit titled `fix info leak`.

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

I reverted to the previous commit.
```bash
git reset --hard HEAD~1
cat README.md
```

## 2. level 29
There is a git repository at `ssh://bandit29-git@bandit.labs.overthewire.org/home/bandit29-git/repo` via the port `2220`. The password for the user `bandit29-git` is the same as for the user `bandit29`.

Clone the repository and find the password for the next level.

---

Similar to Level 28, this problem involves searching through `git`.
I found it by switching to the `dev` branch and digging through the `log`.
```bash
git switch dev
git log -p
```

The `-p` option in `git log` shows the `diff` in detail.
```text
What the -p option produces is slightly different from the traditional diff format:
```

---

## 3. level 30
There is a git repository at `ssh://bandit30-git@bandit.labs.overthewire.org/home/bandit30-git/repo` via the port `2220`. The password for the user `bandit30-git` is the same as for the user `bandit30`.

Clone the repository and find the password for the next level.

---

Running `git branch -rvv` showed only one branch, and `git log` showed nothing.

```bash
git --no-pager log
```
> Using `git --no-pager` outputs the commit ID directly without a `pager`.

Running `git tag` provided a clue.
```bash
git tag
secret
```

The password-like string appeared immediately!
```bash
git show secret
```

---

## 4. level 31
There is a git repository at `ssh://bandit31-git@bandit.labs.overthewire.org/home/bandit31-git/repo` via the port `2220`. The password for the user `bandit31-git` is the same as for the user `bandit31`.

Clone the repository and find the password for the next level.

---

After `git clone`, there is a `README.md`.

```text
This time your task is to push a file to the remote repository.

Details:
    File name: key.txt
    Content: 'May I come in?'
    Branch: master
```

The task was to push. I was a bit unsure, but I created `key.txt` as instructed, wrote `May I come in?`, and added it.
```bash
git add key.txt
The following paths are ignored by one of your .gitignore files:
key.txt
hint: Use -f if you really want to add them.
hint: Disable this message with "git config set advice.addIgnoredFile false"
```
Since `*.txt` is in `.gitignore`, I had to use `-f`.

```bash
git add -f key.txt
git commit -m "test"
git push

remote: Well done! Here is the password for the next level:
```
The push doesn't actually happen, but it gives you the password.

---

## 5. level 32
After all this `git` stuff, it’s time for another escape. Good luck!

---
The `git` problems are over!

```bash
ssh bandit32@bandit.labs.overthewire.org -p 2220

WELCOME TO THE UPPERCASE SHELL
>>
>>
```

Upon connecting, the `UPPERCASE SHELL` is executed. This shell converts every command you type into uppercase.

```bash
>> $SHELL
WELCOME TO THE UPPERCASE SHELL
```

> Reflections after solving:

Typing `$0` executes the current shell's path, restarting the shell.
Looking at the settings for this problem, the login shell is `uppershell`.
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

Executing `$0` runs `sh`, which means the shell executing this command was `sh`.
It seems that `uppershell` was executed immediately after login and it, in turn, executed `sh`.
Executing `/usr/bin/bash` from here starts the `bash` shell used in bandit.
```bash
$ /usr/bin/bash
bandit33@bandit:~$
```

> Solution:
```bash
$0
cat /etc/bandit_pass/bandit33
```

Even exiting is tricky.
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

## 6. level 33
**At this moment, level 34 does not exist yet.**

That’s it!
