---
date: 2026-01-11
draft: false
title: OverTheWire Bandit (3)
categories: ["Linux"]
tags: ["linux", "overthewire", "bandit"]
author: "grrru"
---

### Level 21
A program is running automatically at regular intervals from **cron**, the time-based job scheduler. Look in **/etc/cron.d/** for the configuration and see what command is being executed.

---

A periodically running crontab will provide a hint.
It says to look in `/etc/cron.d/`, so let's go there.
```bash
cd /etc/cron.d/
ll

-rw-r--r--   1 root root   120 Oct 14 09:26 cronjob_bandit22
```

Inspect `cronjob_bandit22` (it's readable by others with 644 permissions).

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

Examining the `.sh` file shows that the contents of `/etc/bandit_pass/bandit22` are being placed into `/tmp/t7O6lds9S0RqQh9aMcz6ShpAoZKF7fgv` every minute.

```bash
cat /tmp/t7O6lds9S0RqQh9aMcz6ShpAoZKF7fgv
```

---
### Level 22
A program is running automatically at regular intervals from **cron**, the time-based job scheduler. Look in **/etc/cron.d/** for the configuration and see what command is being executed.

**NOTE:** Looking at shell scripts written by other people is a very useful skill. The script for this level is intentionally made easy to read. If you are having problems understanding what it does, try executing it to see the debug information it prints.

---

Reading shell scripts written by others is a useful skill!
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

You can find the password location by following the script... but wait!
The `whoami` command in the script is being run by a cronjob, and the entity running the cronjob is `bandit23`. (`* * * * * bandit23 /usr/bin/cronjob_bandit23.sh &> /dev/null`)
Therefore, you must use `myname=bandit23`.

```bash
myname=bandit23
mytarget=$(echo I am user $myname | md5sum | cut -d ' ' -f 1)
cat /tmp/$mytarget
```


### Level 23
A program is running automatically at regular intervals from **cron**, the time-based job scheduler. Look in **/etc/cron.d/** for the configuration and see what command is being executed.

**NOTE:** This level requires you to create your own first shell-script. This is a very big step and you should be proud of yourself when you beat this level!

**NOTE 2:** Keep in mind that your shell script is removed once executed, so you may want to keep a copy around…

---

Open it out of habit.
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

Examining `cronjob_bandit24.sh` reveals a script that iterates through all files (`*`, `.*`) in the `/var/spool/bandit24/foo` directory. For files other than `.` and `..`, if the `owner` is `bandit23`, it runs the file with a 60-second timeout using `-s 9` (SIGKILL) and then deletes the file.
The file we need to read is in `/etc/bandit_pass/bandit24`, which can be read by `bandit24`.
Since the crontab is running as `bandit24` and executes all files under `/foo`, we can create a shell script that `bandit24` can execute, place it under `/foo`, and have it write the password file to a file of our choice.

```bash
drwxrwx-wt 5420 root root 10244096 Jan 10 07:31 tmp/
```
The `/tmp` directory has `-wt` permissions for `others`, where `t` is the sticky bit, meaning only the owner can delete files under `/tmp`. Create `/tmp/grrru.sh`.
```bash
vi /tmp/grrru.sh
```

```bash
#!/bin/bash

touch /tmp/asdfghjkl
cat /etc/bandit_pass/bandit24 > /tmp/asdfghjkl
```

I created a script that simply copies the password to a file I created. Since the entity executing `grrru.sh` will be `bandit24` (via the cronjob), I need to give `others` the `x` (execute) permission.

```bash
chmod 665 /tmp/grrru.sh

ll grrru.sh
-rw-rw-r-x 1 bandit23 bandit23 127 Jan 10 07:41 grrru.sh*
```

Copy `grrru.sh` to the directory scanned by the crontab.
```bash
cp /tmp/grrru.sh /var/spool/bandit24/foo/
```

After waiting for about a minute, the cronjob will run, execute `grrru.sh`, and then delete it.

```bash
cat /tmp/asdfghjkl
```

---

### Level 24
A daemon is listening on port 30002 and will give you the password for bandit25 if given the password for bandit24 and a secret numeric 4-digit pincode. There is no way to retrieve the pincode except by going through all of the 10000 combinations, called brute-forcing.
You do not need to create new connections each time

---

Sending data in the format `$PASSWORD 0000` to `localhost:30002` will return a response, and you must find the correct PIN to get the next password.
```bash
Wrong! Please enter the correct current password and pincode. Try again.

Correct!
The password of user bandit25 is iCi86ttT4KSNe1armKiwbQNmB3YJP3q4
```

While you could send 0000 to 9999 one by one, since you don't need to reconnect for each PIN once a connection is established, let's write a script to send them all at once.
```bash
vi /tmp/grrru24.sh
```

Create the `grrru24.sh` file and generate the strings to be sent line by line.

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

I thought I might miss `Correct!` if it appeared in the middle, but it showed up at the very end (it might vary for each person).
```bash
./grrru24.sh
```

---
### Level 25
Logging in to bandit26 from bandit25 should be fairly easy… The shell for user bandit26 is not **/bin/bash**, but something else. Find out what it is, how it works and how to break out of it.

> NOTE: if you’re a Windows user and typically use Powershell to `ssh` into bandit: Powershell is known to cause issues with the intended solution to this level. You should use command prompt instead.

---

The default shell for `bandit26` is not `/bin/bash`. First, check which shell is being used.

```bash
cat /etc/passwd | grep bandit26
bandit26:x:11026:11026:bandit level 26:/home/bandit26:/usr/bin/showtext
```
It is using `/usr/bin/showtext` as the default shell.
```bash
cat /usr/bin/showtext
#!/bin/sh

export TERM=linux

exec more ~/text.txt
exit 0
```

> The `login shell` executed immediately after logging into a machine can be any executable file (ELF binary or `.sh` script) with execution permissions, not just shell programs like `/bin/bash`.
> ```bash
> file /usr/bin/showtext
> /usr/bin/showtext: POSIX shell script, ASCII text executable
> ```

In `/usr/bin/showtext`, it executes `more ~/text.txt` and then exits immediately.

When connecting as `bandit25`, there is a `bandit26.sshkey` in the HOME directory. Since you need to solve Level 25 with this, you should either fetch it to your local machine via `scp` or connect via SSH directly from the `bandit25` shell.

```bash
ssh bandit26@bandit.labs.overthewire.org -p 2220 -i bandit26.sshkey
```

Logging in via the `ssh` command above exits immediately after showing some ASCII art for `bandit26`. This is output via the `more` command. When the standard output is a `TTY (terminal)`, the `more` command calculates the screen height; if the screen height is smaller than the number of lines to output, it enters pager mode with a `--More--` prompt.
So, reconnect after reducing the screen height. Since the ASCII art is about 6 lines high, setting it to something smaller than 6 should work.

```bash
  _                     _ _ _   ___   __
 | |                   | (_) | |__ \ / /
 | |__   __ _ _ __   __| |_| |_   ) / /_
--More--(50%)
```

It entered Paging mode with `--More--`. Pressing `Enter` shows one line at a time, and pressing the `Up Arrow` goes back up.
While the `more` command is running in Linux, pressing `v` opens the `vi` editor at the current position to edit the file.
```bash
v
```

In the `vi` editor, typing `:set shell?` shows the current shell setting.
```bash
:set shell?
shell=/usr/bin/showtext
```

Since the current logged-in ID is `bandit26`, if you change the shell to `/bin/bash` within the `vi` editor, you can execute a new shell within the current `vi` session using `:sh`.

```bash
:set shell=/bin/bash
:sh
```

Retrieve the desired password.
```bash
bandit26@bandit:~$ cat /etc/bandit_pass/bandit26
s0773xxkk0MXfdqOfPRVr9L3jJBUOgCZ
```

> You can proceed to Level 26 directly from here without exiting.

---

### Level 26
Good job getting a shell! Now hurry and grab the password for bandit27!

---

Go to `HOME` and run `ls` to see `bandit27-do`.
```bash
file ./bandit27-do
./bandit27-do: setuid ELF 32-bit LSB executable, Intel 80386, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux.so.2, BuildID[sha1]=35d353cf6d732f515a73f50ed205265fe1e68f90, for GNU/Linux 3.2.0, not stripped
```

It's the `setuid` file we saw before.
```bash
./bandit27-do id
uid=11026(bandit26) gid=11026(bandit26) euid=11027(bandit27) groups=11026(bandit26)
```

In Linux/Unix-like operating systems, executing a file with specific permissions like `setuid` allows temporarily gaining the permissions (EUID) of the file owner or another user to access system resources.
Since it's set to `euid=11027(bandit27)`, you can use this file to read the `bandit27` password file.
```bash
./bandit27-do cat /etc/bandit_pass/bandit27
```

---

### Level 27
There is a git repository at `ssh://bandit27-git@bandit.labs.overthewire.org/home/bandit27-git/repo` via the port `2220`. The password for the user `bandit27-git` is the same as for the user `bandit27`.

Clone the repository and find the password for the next level.

---

I attempted `git clone` after connecting as `bandit27`.

```bash
cd /tmp
git clone ssh://bandit27-git@bandit.labs.overthewire.org:2220/home/bandit27-git/repo
```

However, it said that SSH connection from localhost to localhost is blocked to conserve resources.
```text
!!! You are trying to log into this SSH server with a password on port 2220 from localhost.
!!! Connecting from localhost is blocked to conserve resources. 
!!! Please log out and log in again.
```

So I just performed the `git clone` directly from my local machine and read the `README`.
