---
date: 2026-01-07
draft: false
title: OverTheWire Bandit (2)
categories: ["Linux"]
tags: ["linux", "overthewire", "bandit"]
author: "grrru"
---

> [OverTheWire: Bandit](https://overthewire.org/wargames/bandit/)  
> Starting from `Level 12`~

---
### Level 12
The password for the next level is stored in the file **data.txt**, which is a hexdump of a file that has been repeatedly compressed. For this level it may be useful to create a directory under /tmp in which you can work. Use mkdir with a hard to guess directory name. Or better, use the command “mktemp -d”. Then copy the datafile using cp, and rename it using mv (read the manpages!)

---

You need to obtain the original data file by repeatedly decompressing the hexdump file.
```bash
mktemp -d
cp ~/data.txt /tmp/`directory_created_above`
```

Check what kind of compression is used for the file obtained with `file *`, then use the appropriate decompression method repeatedly until you get a text file.

```sh
file *

xxd -r data.txt

gzip -dc data > data1
bzip2 -dc data1 > data2

mv data2 data2.tar
tar -xf data2.tar
```
It usually involves repeating these three... after about 10 times, the text file appears.

---
### Level 13
The password for the next level is stored in **/etc/bandit_pass/bandit14 and can only be read by user bandit14**. For this level, you don’t get the next password, but you get a private SSH key that can be used to log into the next level. Look at the commands that logged you into previous bandit levels, and find out how to use the key for this level.

---

You need to read `/etc/bandit_pass/bandit14`... but it cannot be read as `bandit13`..
```bash
-r--------   1 bandit14 bandit14    33 Oct 14 09:25 bandit14
```

A private SSH key is provided in the $HOME directory, which can be used to log in as `bandit14`.
```bash
cat ~/sshkey.private
```

However, the permissions for `sshkey.private` are set to `640`, but for a private key to be used for SSH login, the permissions must be `600`!

```bash
-rw-r----- 1 bandit14 bandit13 1679 Oct 14 09:26 sshkey.private
```

Copy the contents of `sshkey.private` to your local machine, save it to any file, change its permissions to `600`, and log in to `bandit14` to obtain the password.
```bash
vi key
~~~ writing the key ~~~

ssh -i key bandit14@bandit.labs.overthewire.org -p 2220
cat /etc/bandit_pass/bandit14
```

---
### Level 14
The password for the next level can be retrieved by submitting the password of the current level to **port 30000 on localhost**.

---

Submit the password for level 14 to `localhost:30000`.

Send the password to port 30000 using `nc`, and it will provide the password for the next level.

```bash
echo MU4VWeTyJk8ROof1qqmcBPaLh7lDCPvS | nc localhost 30000
```

---
### Level 15
The password for the next level can be retrieved by submitting the password of the current level to **port 30001 on localhost** using SSL/TLS encryption.

**Helpful note: Getting “DONE”, “RENEGOTIATING” or “KEYUPDATE”? Read the “CONNECTED COMMANDS” section in the manpage.**

---

Similar to Level 14, but this time you must use SSL/TLS encryption and send it to port 30001.

First, create an encrypted session using `openssl`.
```bash
openssl s_client -connect localhost:30001
```
`s_client` indicates connecting to an SSL/TLS session.
Once the session is connected, paste the level 14 password.

---
### Level 16
The credentials for the next level can be retrieved by submitting the password of the current level to **a port on localhost in the range 31000 to 32000**. First find out which of these ports have a server listening on them. Then find out which of those speak SSL/TLS and which don’t. There is only 1 server that will give the next credentials, the others will simply send back to you whatever you send to it.

---

**Helpful note: Getting “DONE”, “RENEGOTIATING” or “KEYUPDATE”? Read the “CONNECTED COMMANDS” section in the manpage.**

Find a port between 31000 and 32000 that is in the `LISTENING` state and capable of SSL/TLS responses. Only one of these is genuine; the others simply echo back whatever characters you send.

```bash
ss -ltnp | grep -E ':31.*'
```

Since there were only a few candidates, I tried them one by one.
```bash
openssl s_client -connect localhost:31587 -quiet
```
`openssl s_client` recognizes a string starting with `k` as a control command rather than data. Since the level 16 password starts with `k`, you might receive a `KEYUPDATE` response.
To avoid this, add the `-quiet` option to prevent entering interactive mode.
When `Correct!` appears, it provides an RSA private key (it gives credentials, not a password).

---
### Level 17
There are 2 files in the homedirectory: **passwords.old and passwords.new**. The password for the next level is in **passwords.new** and is the only line that has been changed between **passwords.old and passwords.new**

**NOTE: if you have solved this level and see ‘Byebye!’ when trying to log into bandit18, this is related to the next level, bandit19**

---

Create a file named `key`, paste the private key inside, and log in via SSH using the `-i` option.
```bash
ssh bandit17@bandit.labs.overthewire.org -p 2220 -i key
```

Compare the two files line by line using `diff` to find the differing line. The line in `passwords.new` is the password.
```bash
diff passwords.new passwords.old
```

---
### Level 18
The password for the next level is stored in a file **readme** in the homedirectory. Unfortunately, someone has modified **.bashrc** to log you out when you log in with SSH.

---

Someone played a prank so you get logged out immediately upon logging in. Since you just need to read `readme`, append the command after the ssh command to output it immediately.
Multiple commands can be separated by `;`.

```bash
ssh bandit18@bandit.labs.overthewire.org -p 2220 'ls -al;cat ~/readme'
```

---
### Level 19
To gain access to the next level, you should use the setuid binary in the homedirectory. Execute it without arguments to find out how to use it. The password for this level can be found in the usual place (/etc/bandit_pass), after you have used the setuid binary.

---

Use the `setuid binary` in the home directory. It suggests running it without arguments to see examples.

```bash
./bandit20-do
Run a command as another user.
  Example: ./bandit20-do whoami

./bandit20-do whoami
bandit20
```

Running `whoami` outputs the next level's user, `bandit20`. A `setuid binary` is a file that allows executing commands with the permissions of the file's owner. It can be dangerous.

```bash
./bandit20-do cat /etc/bandit_pass/bandit20
```

---
### Level 20
There is a setuid binary in the homedirectory that does the following: it makes a connection to localhost on the port you specify as a commandline argument. It then reads a line of text from the connection and compares it to the password in the previous level (bandit20). If the password is correct, it will transmit the password for the next level (bandit21).

---

**NOTE:** Try connecting to your own network daemon to see if it works as you think

The `setuid binary` named `suconnect` is a file that, when requested via an arbitrary port, provides the password for the next stage if you enter the `bandit20` password on that port.
You need to open two SSH sessions.
```bash
# Session 1
nc -l 1234

# Session 2
./suconnect 1234

# Session 1
[Enter bandit20 passwd and press Enter]
```
