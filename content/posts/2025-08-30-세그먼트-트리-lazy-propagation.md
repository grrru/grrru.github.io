---
title: 세그먼트 트리와 lazy propagtion
date: "2025-08-30T16:28:00+09:00"
categories:
  - algorithm
tags:
  - segment tree
  - lazy propagation
pin: false
---
## ✅ 1. 세그먼트 트리
### 1.1 기본 개념
- 배열 구간의 정보를 빠르게 관리하기 위한 트리 기반 자료구조
- 구간 합, 구간 최솟값 및 최댓값 등 구간 질의(Query)를 `O(logN)`에 처리 가능하다
- 세그먼트 트리의 크기는 `4 * N` 정도로 잡으면 충분하다
	- N보다 크거나 같은 2^(k-1) 를 찾아서 2^K 길이의 트리를 만들면 되는데 이게 `4N`보다 작아서 괜찮다

### 1.2 동작
- 세그먼트 트리는 트리의 1번 인덱스부터 순차적으로 자식 노드를 탐색한다
- 1번 인덱스는 1 ~ N까지 배열 범위의 정보를 가지고 있고 왼쪽 자식`idx*2`는 왼쪽 범위, 오른쪽 자식 `idx2+1`은 오르른쪽 범위 정보를 가지게 된다

1. 쿼리(Query)
	- 검색을 원하는 구간 `[l, r]`과 현재 노드 `[s, e]` 범위를 비교한다
	- 완전 불일치 `r < s || e < l`인 경우
		- 검색 범위에 속하지 않으므로 무시한다
	- 완전 포함 `l <= s && e <= r`인 경우
		- 현재 노드 정보가 검색 범위에 완전히 포함되므로 현재 노드 값을 반환한다
	- 부분 겹침 (나머지 케이스)
		- 왼쪽/오른쪽 자식으로 재귀 호출한 후 두 자식의 결과를 합친다
2. 업데이트
	1. 특정 원소 하나를 변경하는 경우 리프 노드까지 쭉 전파해서 업데이트한다
	2. 특정 구간을 업데이트하는 경우 `Lazy Propagation`을 통해 효율화한다

## 2. ✅ Lazy Propagation
- 지연 전파라고 하며 구간 업데이트 시 매번 자식까지 내려가며 갱신하면 O(N)에 가까워지므로 자식까지 업데이트를 즉시 반영하지 않고 나중에 필요할 때 반영하는 기법

### 2.1 예시 BOJ 1395. 스위치
[1395. 스위치](https://www.acmicpc.net/problem/1395)

1. Propagation
```go
// lazy의 값을 tree에 반영하고 한 단계 아래의 자식 lazy 노드에 전파하는 함수
func propagate(s, e, idx int) {
	if lazy[idx]%2 == 1 {
		tree[idx] = e - s + 1 - tree[idx]
		if s != e {
			lazy[idx*2] += lazy[idx]
			lazy[idx*2+1] += lazy[idx]
		}

		lazy[idx] = 0
	}
}
```

2. Update
```go
func updateTree(l, r, s, e, idx int) {
	propagate(s, e, idx)

	if e < l || r < s {
		return
	}

	if l <= s && e <= r {
		lazy[idx]++
		propagate(s, e, idx)
		return
	}

	mid := (s + e) / 2

	updateTree(l, r, s, mid, idx*2)
	updateTree(l, r, mid+1, e, idx*2+1)
	tree[idx] = tree[idx*2] + tree[idx*2+1]
}
```

- 일반적인 전파 방식과의 차이점은 완전 포함인 케이스 `l <= s && e <= r`에서 `tree`에만 반영하는 것이 아닌 `propagation`을 통해서 `lazy`의 값을 자식 노드에게 전파하는 과정이 있다는 점이다
- update 시에는 처음에 `propagation`을 한 번 수행해줘야 뒤늦은 전파가 꼬이지 않는다

3. Query
```go
func query(l, r, s, e, idx int) int {
	propagate(s, e, idx)

	if e < l || r < s {
		return 0
	}

	if l <= s && e <= r {
		return tree[idx]
	}

	mid := (s + e) / 2
	return query(l, r, s, mid, idx*2) + query(l, r, mid+1, e, idx*2+1)
}
```

- 현재 위치의 값을 정확히 파악하기 위해서는 `lazy`에 있던 값을 원본 트리 `tree`에 업데이트해주는 `propagtion`을 한 번 진행해야 한다

4. 최종 코드

```go
package main

import (
	"bufio"
	"fmt"
	"os"
)

var (
	n    int
	m    int
	tree []int
	lazy []int
)

var (
	rb = bufio.NewReader(os.Stdin)
	wb = bufio.NewWriter(os.Stdout)
)

func main() {
	defer wb.Flush()

	fmt.Fscan(rb, &n, &m)
	initTree()

	var cmd, l, r int
	for m > 0 {
		m--
		fmt.Fscan(rb, &cmd, &l, &r)
		command(cmd, l, r)
	}
}

func initTree() {
	size := 4 * (n + 1)
	tree = make([]int, size)
	lazy = make([]int, size)
}

func command(cmd, l, r int) {
	if cmd == 0 {
		clickSwitch(l, r)
	} else {
		checkSwitch(l, r)
	}
}

func clickSwitch(l, r int) {
	updateTree(l, r, 1, n, 1)
}

func checkSwitch(l, r int) {
	fmt.Fprintln(wb, query(l, r, 1, n, 1))
}

func query(l, r, s, e, idx int) int {
	propagate(s, e, idx)

	if e < l || r < s {
		return 0
	}

	if l <= s && e <= r {
		return tree[idx]
	}

	mid := (s + e) / 2
	return query(l, r, s, mid, idx*2) + query(l, r, mid+1, e, idx*2+1)
}

func updateTree(l, r, s, e, idx int) {
	propagate(s, e, idx)

	if e < l || r < s {
		return
	}

	if l <= s && e <= r {
		lazy[idx]++
		propagate(s, e, idx)
		return
	}

	mid := (s + e) / 2

	updateTree(l, r, s, mid, idx*2)
	updateTree(l, r, mid+1, e, idx*2+1)
	tree[idx] = tree[idx*2] + tree[idx*2+1]
}

// lazy의 값을 tree에 반영하고 한 단계 아래의 자식 lazy 노드에 전파하는 함수
func propagate(s, e, idx int) {
	if lazy[idx]%2 == 1 {
		tree[idx] = e - s + 1 - tree[idx]
		if s != e {
			lazy[idx*2] += lazy[idx]
			lazy[idx*2+1] += lazy[idx]
		}

		lazy[idx] = 0
	}
}
```
