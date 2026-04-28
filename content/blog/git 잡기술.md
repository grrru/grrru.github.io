---
date: 2026-04-28
draft: false
title: git 잡기술
categories: git
tags:
  - git
author: grrru
---

> 일할 때 유용했던 git 잡기술 정리

## tag

```bash
git tag -l # tag list 보기

git tag v1.2.0 # tag 생성

git push origin v1.2.0 # 생성한 tag push
```


- `fetch prune-tags`는 remote에서 제거된 tag를 local에서 자동으로 제거해준다.

```bash
git fetch --prune-tags
```

local에만 있던 tag도 remote에 없으면 제거될 수 있으니 주의.


## rebase

`git rebase -i` 뒤에 뭐가 오는건지 항상 헷갈렸는데, 어떤 상태를 base로 할 건지를 적으면 된다.

```bash
git rebase -i origin/main

git rebase -i HEAD~3
```

origin/main이라면 로컬에 저장된 remote-tracking ref인 `origin/main`을 base로 하고 그 이후 커밋을 interactive rebase한다는 뜻이고,  
HEAD~3이라면 현재 HEAD의 3번째 조상 커밋을 base로 하고 그 이후 커밋 3개를 rebase하겠다는 뜻이다. `HEAD`가 0번째, `HEAD~1`이 1번째 이전 커밋이라고 생각하면 된다.


### fixup

n번째 이전 커밋에 현재 변경 내역을 집어넣고 force-push하고 싶을 때 유용하다.

```bash
git add .
git commit --fixup HEAD~3
```

`--fixup` 옵션으로 커밋하면 HEAD~3 번째 커밋 메시지에 `fixup!`이 붙은 형태로 commit된다. (ex. `fixup! commands 제거`)

```bash
git rebase -i HEAD~5
```

위처럼 `HEAD~5`까지 불러와서 rebase를 해도 된다. 
(`HEAD~3`에 fixup commit을 만들었다면, rebase할 때는 fixup commit이 `HEAD~0`이 되고 기존 commit이 `HEAD~4`가 될테니까 `HEAD~5`를 base로 해야 원하는 작업이 될듯..?)

```bash
pick a8f4c2e commands 제거
pick 9b1d6a3 test-actions@v1 actions 사용
pick c7e0f5b fixup! commands 제거
```

위처럼 나온 걸  아래처럼 fixup으로 바꾸고 `:wq`하면 rebase 완료

```bash
pick a8f4c2e commands 제거
fixup c7e0f5b fixup! commands 제거
pick 9b1d6a3 test-actions@v1 actions 사용
```

하지만 더 간단하게 하는 방법은, `commit --fixup`으로 생긴 커밋은 git이 자동으로 감지한다.

```bash
git rebase -i --autosquash HEAD~5
```

`autosquash` 옵션은 fixup 커밋을 자동으로 찾아서 대상 커밋 아래로 옮기고 `fixup`으로 바꿔준다.
