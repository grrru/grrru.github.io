---
date: 2026-01-13
draft: true
title: drafted
categories: Linux
tags:
author: grrru
---


# 개발자가 쓴 Go 프로그램이 빌드·실행되기까지

> 기준: **Go 1.25.3** (`/home1/irteam/sdk/go1.25.3/src`), linux/amd64
> 아래 모든 경로는 `$GOROOT/src` 기준 상대경로. `file.go:123` 형식은 실제 확인한 줄 번호.
> 작성: 2026-07-29

---

## 목차

- [0. 단계를 어떻게 나눌 것인가](#0-단계를-어떻게-나눌-것인가)
- [축 A — cmd/go: 계획과 캐시](#축-a--cmdgo-계획과-캐시)
- [축 B — cmd/compile: 패키지 하나를 .a로](#축-b--cmdcompile-패키지-하나를-a로)
- [축 C — cmd/link: .a 여럿을 ELF 하나로](#축-c--cmdlink-a-여럿을-elf-하나로)
- [축 D — 실행: execve부터 GMP 루프까지](#축-d--실행-execve부터-gmp-루프까지)
- [축 E — 관통 계약: 컴파일러·링커·런타임](#축-e--관통-계약-컴파일러가-심고-링커가-조립하고-런타임이-읽는다)
- [오해 정정 모음](#요약-go-125-기준-오해-정정-모음)
- [학습 경로](#학습-경로-이-순서로-파세요)

---

## 0. 단계를 어떻게 나눌 것인가

"빌드 계획 → 패키지 컴파일 → 링크 → 실행"의 4단계 구분은 **프로세스 경계** 기준으로는 정확하다. 다만 소스를 따라가는 목적에서는 두 가지가 빠진다.

1. **"패키지 컴파일" 단계는 대부분의 빌드에서 실행되지 않는다.** `cmd/go`의 본질은 계획이 아니라 *캐시 판정*이다. 판정에서 히트하면 `compile`은 exec조차 되지 않는다 (`cmd/go/internal/work/exec.go:484`).
2. **실행 단계에서 GMP가 돌 수 있는 이유는 앞 단계들이 심어 둔 메타데이터다.** "컴파일러가 심고 → 링커가 조립하고 → 런타임이 읽는" 3자 계약은 어느 단계에도 속하지 않으면서 전 단계를 관통한다. 이걸 단계 목록에 끼워 넣으면 안 보인다.

그래서 **4개 축 + 1개 관통 레이어**로 나눈다.

| 축 | 실행 주체 | 실행 횟수 | 입력 → 출력 | 진입 소스 |
|---|---|---|---|---|
| **A. 계획·캐시** | `go` 프로세스 1개 | 1회 | 소스 트리 + go.mod → Action DAG + exec 커맨드라인 | `cmd/go/main.go:99` |
| **B. 번역** | `compile`/`asm` 프로세스 **N개(병렬)** | 패키지당 1회 (캐시 미스 시에만) | `.go` → `.a` | `cmd/compile/internal/gc/main.go:61` |
| **C. 통합** | `link` 프로세스 1개 | 1회 | `.a` × N → ELF | `cmd/link/internal/ld/main.go:161` |
| **D. 실행** | 커널 + 내 바이너리 | 프로세스 수명 | ELF → 살아 있는 GMP 상태 | `runtime/rt0_linux_amd64.s:7` |
| **E. 관통 계약** | A~D 전부 | — | 컴파일러 산출 메타데이터 → 런타임 기능 | `runtime/symtab.go:394` |

### 표현(representation)의 연쇄 — 이게 진짜 척추

단계 이름보다 이 사슬을 외우는 게 소스 탐색에 훨씬 유용하다. 각 화살표가 곧 하나의 패키지 경계다.

```
.go 텍스트
  ↓ cmd/compile/internal/syntax        (파서 전용 AST, go/ast 아님)
syntax.File
  ↓ cmd/compile/internal/types2        (타입체크)
types2.Info
  ↓ noder/writer.go + internal/pkgbits  ★ 직렬화
pkgbits 비트스트림 ("package stub")
  ↓ noder/reader.go                     ★ 역직렬화 — 여기서 IR이 태어난다
ir.Func + types.Type
  ↓ ssagen/ssa.go buildssa
ssa.Func (Value / Block 그래프)
  ↓ ssa/compile.go 52개 pass → ssagen genssa
obj.Prog (어셈블리 수준 명령 링크드리스트)
  ↓ cmd/internal/obj/x86 preprocess + span6
obj.LSym.P (바이트) + LSym.R (relocation)
  ↓ cmd/internal/obj/objfile.go
goobj(_go_.o) + UIR export data(__.PKGDEF)  →  .a 아카이브
  ↓ cmd/link — 심볼 병합 · 데드코드 · 주소 확정 · relocation 적용
ELF 실행 파일
  ↓ execve → runtime 부트스트랩
프로세스 메모리 (allp/allgs/mheap_/pollDesc)
```

**핵심 관찰**: 이 사슬에서 유일하게 "왕복"하는 지점이 pkgbits다. types2 결과를 바이트로 굽고 즉시 다시 읽는다. 왜 그러는지가 Go 컴파일러 프론트엔드 설계의 전부다 (§B-1).

`make`는 이 사슬에 없다. `make`는 축 A를 시작하는 wrapper일 뿐이다.

---

# 축 A — cmd/go: 계획과 캐시

`go build` 한 번의 실제 흐름:

```
main()                          cmd/go/main.go:99
├─ counter.Open()
├─ handleChdirFlag()            (-C)
├─ toolchain.Select()           ★ 107줄 — flag.Parse보다 먼저!
├─ flag.Parse()                 113줄
├─ lookupCmd(args)              185줄 → base.Go.Commands 트리 탐색
└─ invoke(cmd, args)            291줄 → CmdBuild.Run = runBuild

runBuild                        cmd/go/internal/work/build.go:460
├─ modload.InitWorkfile()
├─ work.BuildInit()             work/init.go:53
├─ b := NewBuilder("")          work/action.go:274 → $WORK 임시디렉터리
├─ load.PackagesAndErrors(...)  load/pkg.go:2902  ← modload + import 그래프
├─ a := &Action{Mode:"go build"} build.go:551
│    └─ b.AutoAction(...)       action.go:443 → CompileAction / LinkAction
└─ b.Do(ctx, a)                 build.go:558 → exec.go:73
```

## A-1. GOTOOLCHAIN 스위칭이 flag.Parse보다 먼저다

`toolchain.Select()` (`cmd/go/internal/toolchain/select.go:97`)가 `flag.Parse()`보다 먼저 불린다. go.mod의 `go`/`toolchain` 줄이 더 높은 버전을 요구하면 **현재 프로세스는 `syscall.Exec`으로 다른 `go` 바이너리로 대체되어 사라진다** (`toolchain/exec.go:23`). PATH에 없으면 `golang.org/toolchain@v0.0.1-<ver>.<goos>-<goarch>` 모듈을 다운로드해 실행한다.

무한 스위칭 방지: `GOTOOLCHAIN_INTERNAL_SWITCH_COUNT`(상한 100, `select.go:72`)와 `GOTOOLCHAIN_INTERNAL_SWITCH_VERSION`(자식의 자기검증).

> 디버깅: `GODEBUG=#toolchaintrace=1` (`select.go:90`)

## A-2. modload → load: import 그래프 만들기

`load.PackagesAndErrors`가 먼저 `modload.LoadPackages`를 부른다 (`modload/load.go:253`). 그 안의 `loadFromRoots`(`load.go:1082`)는 **수렴할 때까지 도는 for 루프**다:

```
for {
    ld.reset()
    ld.listRoots()          → 루트 패키지
    ld.pkg() 재귀           → import 폐포 로딩 (par.Queue 병렬)
    <-ld.work.Idle()
    if !ld.updateRequirements().changed { break }
}
```

**왜 루프인가**: "어떤 패키지를 로드할 수 있는가"는 빌드 리스트에 의존하고, 빌드 리스트는 로드된 패키지에 의존한다. `load.go:1131~1134` 주석이 이 순환을 명시한다. 버전 선택 자체는 MVS(`mvs/mvs.go:90 BuildList`)가 담당한다.

그 위에서 `load.loadImport`(`load/pkg.go:706`)가 재귀적으로 `p.Internal.Imports []*Package`를 채운다 — `load/pkg.go:2046`의 한 줄이 import 그래프의 간선이 연결되는 지점이다.

main 패키지에는 `LinkerDeps`(`load/pkg.go:2638`)가 암묵 import로 추가된다: 항상 `runtime`, 외부 링킹이면 `runtime/cgo`, `-race`면 `runtime/race` 등.

## A-3. Action DAG — import 그래프의 1:1 변환

```go
// cmd/go/internal/work/action.go:82
type Action struct {
    Mode    string      // "build" / "link" / "vet" / "nop" / "built-in package"
    Actor   Actor       // 실제 수행 함수 (Act 메서드 1개짜리 인터페이스, :70)
    Deps    []*Action
    Objdir  string      // $WORK/bNNN/
    actionID, buildID string  // 캐시 키
    pending int; triggers []*Action; priority int
}
```

`CompileAction`(`action.go:544`)이 `cacheAction`(`:433`)으로 `cacheKey{mode, *Package}` 메모이제이션을 걸어 **패키지당 액션이 정확히 하나**만 생기게 한다.

`LinkAction`(`:690`)에 미묘한 트릭이 하나 있다 (`action.go:734`): main 패키지 컴파일 액션의 deps에 `&Action{Mode:"nop", Deps: a.Deps[1:]}`를 끼워 **main 컴파일이 다른 모든 링크 입력보다 나중에 오도록 강제**한다. 링크 ActionID를 계산하려면 다른 의존들의 build ID가 이미 확정돼 있어야 하기 때문이다.

실행은 `b.Do`(`exec.go:73`):
- `actionList(root)`(`:54`)가 DFS 후위 순회로 평탄화하고 그 인덱스를 `a.priority`로 부여
- `a.pending = len(a.Deps)`, 역방향 간선 `a1.triggers` 구성
- `par := cfg.BuildP`(기본 `GOMAXPROCS`) 개 고루틴이 priority 최소힙(`action.go:142`)에서 pop → `handle`(`exec.go:136`) → 끝나면 trigger의 pending 감소

## A-4. ★ 이 단계의 심장: content-based 캐시

**`go build`는 mtime을 보지 않는다.** `buildActionID`(`exec.go:241`)가 해시에 넣는 것 전부:

```
"compile" 태그, p.Dir(또는 trimpath면 module@version), 모듈 go 버전,
GOOS/GOARCH, import 경로, omitdebug/standard/local/prefix,
b.toolID("compile")      = `compile -V=full` 출력      buildid.go:146
forcedGcflags + p.Internal.Gcflags
(.s 있으면) asm 툴 ID, GOARM 등, GOEXPERIMENT, modinfo
모든 입력 파일의 내용 해시   b.fileHash              buildid.go:388
각 의존 액션의 contentID(a1.buildID)
```

이 ActionID로 `b.useCache`(`buildid.go:416`)가 판정하고, 히트면 `a.built`만 세우고 **컴파일러를 exec하지 않는다**.

세 개의 ID를 구분하는 게 중요하다:

| 이름 | 정의 | 위치 |
|---|---|---|
| **ActionID** | "이 계산의 완전한 서술"의 SHA256 = 캐시 키 | `cache/cache.go:31` |
| **OutputID** | 산출 파일 내용의 SHA256 = 캐시 값 주소 | `cache/cache.go:34` |
| **build ID** | 파일 안에 박아 넣는 `actionID/contentID` 문자열 | `work/buildid.go:99` |

**왜 분리하나**: 자기 ActionID를 자기 출력에 넣으면 절대 수렴하지 않는다. contentID는 "build ID 자리를 제외한 나머지 내용"의 해시라서, 컴파일러가 자기 자신을 컴파일해도 build ID가 수렴한다. `work/buildid.go` 상단 60~97줄 주석이 이 설계를 직접 설명한다.

빌드 끝에 `updateBuildID`(`buildid.go:641`)가 `FindAndHash`(`cmd/internal/buildid/rewrite.go:23`)로 content ID를 계산하고 `Rewrite`(`:102`)로 파일 안의 build ID를 덮어쓴 뒤 캐시에 `Put`한다.

모든 ActionID 해시는 `hashSalt`(`cache/hash.go:46`) = `runtime.Version()`으로 시작한다. 그래서 Go 버전이 다르면 캐시가 갈린다.

## A-5. 컴파일러로 넘어가는 것 = 커맨드라인 하나

`gcToolchain.gc`(`work/gc.go:57`)가 조립하는 것:

```
compile -o $WORK/bNNN/_pkg_.a -trimpath ... -p <패키지경로> -lang=go1.x
        [-std] [-complete] [-buildid <actionID/contentID>] [-goversion ...]
        [-pgoprofile ...] [-symabis $WORK/bNNN/symabis] [-c=N] <gcflags...>
        -importcfg $WORK/bNNN/importcfg [-embedcfg ...] [-pack]
        [-asmhdr $WORK/bNNN/go_asm.h] <소스파일 절대경로들...>
```

동반 파일 3종:

- **importcfg** (`exec.go:819`) — `packagefile <import경로>=<.a 절대경로>` / `importmap <원본>=<실제>`. **이 파일 때문에 `cmd/compile`은 GOPATH나 모듈 캐시를 전혀 탐색하지 않는다.** 경로 해석 책임이 100% `cmd/go`에 있다.
- **embedcfg** (`exec.go:836`) — `//go:embed`용 JSON
- **symabis** (`gc.go:406`) — `asm -gensymabis` 출력. 어셈블리 심볼의 ABI

### 실습

```bash
go build -work -x            # $WORK 유지 + 실제 커맨드라인 출력
go build -debug-actiongraph=/tmp/dag.json ./...   # Action DAG를 JSON으로
go build -a -x 2>&1 | head   # 캐시 무시하고 전부 재빌드
```

### 오해 정정 (축 A)

- **`$GOROOT/pkg`에 표준 라이브러리 `.a`가 미리 있다** → Go 1.20부터 사전 컴파일 아카이브를 배포하지 않는다. `exec.go:266~270` 주석에 명시 (go.dev/issue/47257). 표준 라이브러리도 빌드 캐시로 다룬다.
- **`Package.Stale`이 재빌드 판정에 쓰인다** → `load/pkg.go:88~90` 주석: "remain here *only* for the list command."
- **`-p`는 컴파일러 병렬도** → 아니고 "동시 실행 액션(프로세스) 수"다. 컴파일러 내부 백엔드 동시성은 별도 `gcBackendConcurrency`(`work/gc.go:182`)가 `-c=N`으로 넘긴다.
- **`go tool pack`이 별도 프로세스로 돈다** → `-x` 출력에만 `# internal` 주석과 함께 찍히고 실제로는 in-process `packInternal`(`gc.go:497`)이다. 게다가 순수 Go 패키지는 컴파일러가 `-pack`으로 `.a`를 직접 쓰므로 pack 단계 자체가 실행되지 않는다 (`exec.go:964`의 `if len(objects) > 0`).
- **실행 파일도 캐시된다** → 기본은 아니다. `a.CacheExecutable`이 켜지고 캐시가 `*cache.DiskCache`일 때만 `PutExecutable`(`buildid.go:736`). 보통은 링커 stdout만 `link-stdout` 서브키에 남는다.

---

# 축 B — cmd/compile: 패키지 하나를 .a로

`gc.Main`(`cmd/compile/internal/gc/main.go:61`) 한 함수에 전 단계가 선형으로 적혀 있다. **이 목차를 그대로 읽는 게 가장 빠르다.**

| 줄 | 호출 | 하는 일 |
|---|---|---|
| 62 | `Timer.Start("fe","init")` | 플래그, 유사패키지, universe |
| 208 | `noder.LoadPackage` | **파싱 + types2 + UIR 왕복 전부** |
| 222 | `ssagen.InitConfig` | 백엔드 설정 (미들엔드가 타입 크기 필요) |
| 228 | `pgoir.New` | `-pgoprofile` 로드 |
| 240 | `interleaved.DevirtualizeAndInlinePackage` | ★ devirt + inline 교차 고정점 |
| 242 | `noder.MakeWrappers` | 메서드 wrapper (인라인 후여야 함) |
| 247 | `loopvar.ForCapture` | Go 1.22 per-iteration 루프 변수 |
| 252 | `pkginit.MakeTask` | `p..inittask` 심볼 생성 |
| 256 | `symABIs.GenABIWrappers` | ABI wrapper (escape 전이어야 함) |
| 258 | `deadlocals.Funcs` | 안 쓰는 지역변수 대입 제거 |
| 269 | `escape.Funcs` | escape 분석 |
| 289~336 | `enqueueFunc` → `compileFunctions` | walk + SSA + 기계어 (병렬) |
| 351~354 | `dumpdata` / `dumpobj` | `.a` 쓰기 |

## B-1. 프론트엔드 — 왜 직렬화했다가 다시 읽는가

`noder.LoadPackage`(`noder/noder.go:27`) 안에서 네 단계가 다 일어난다. (그래서 `Timer` 구간은 전부 `fe/parse`로 뭉쳐 보인다.)

**① 파싱** — `syntax.Parse`(`syntax/syntax.go:66`)를 `GOMAXPROCS+10` 세마포어로 파일별 병렬 실행. `go/ast`가 아니라 전용 `syntax` 패키지를 쓰는 이유: 손으로 쓴 렉서가 더 빠르고, `//go:` 지시자를 스캔 중 `PragmaHandler`로 콜백하고(`noder.go:221`), `CheckBranches` 모드로 label/goto 검사까지 파서가 끝내고, API 하위호환 의무가 없다.

**② types2 타입체크** — `checkFiles`(`noder/irgen.go:26`)가 `types2.Config`를 구성해 `conf.Check`. `Checker.checkFiles`(`types2/check.go:468`)의 490~518줄이 그대로 목차다: `initFiles → collectObjects → packageObjects → processDelayed → cleanup → initOrder → unusedImports → recordUntyped → monomorph`. 마지막 `monomorph`(`types2/mono.go:82`)는 타입 파라미터 흐름 그래프에서 양의 가중치 사이클을 찾아 **정적 인스턴스화가 종료되지 않는 재귀 제네릭을 거부**한다.

`types2`와 `go/types`가 두 벌인 이유는 다루는 구문 트리가 다르기 때문이다. `go/types`는 표준 라이브러리라 API 하위호환에 묶여 있고, `types2`는 internal이라 자유롭다. 자동 동기화되지 않으니 양쪽에 반영해야 한다.

**③ UIR writer** — `writePkgStub`(`noder/unified.go:318`)이 (syntax + types2.Info)를 `internal/pkgbits` 비트스트림으로 굽는다. 섹션은 10개(`internal/pkgbits/reloc.go:13`): `SectionString/Meta/PosBase/Pkg/Name/Type/Obj/ObjExt/ObjDict/Body`.

**④ UIR reader** — `unified.go:199`가 방금 만든 문자열을 그대로 `pkgbits.NewPkgDecoder`에 물린다. `readPackage`(`:407`) → `reader.pkgInit`(`reader.go:3290`) → `pkgDecls`(`:3357`)가 `ir.Func`/`types.Type`을 만든다.

### ★ 이 왕복이 왜 존재하는가

`unified.go:148~188`의 긴 주석이 근거를 설명한다. **같은 직렬화 포맷 한 벌이 네 가지 일을 동시에 해내기 때문이다:**

1. 로컬 패키지 IR 생성
2. export data (다른 패키지가 읽을 것)
3. 인라인 바디 전달
4. **제네릭 인스턴스화의 재료** ← 이게 결정적

제네릭 함수를 import해 새 타입 인자로 인스턴스화하려면 "타입 파라미터가 아직 살아 있는" 형태를 보관해야 한다. UIR이 정확히 그 형태다.

부수 설계: 모든 원소 앞에 **참조 테이블**(`RefTableEntry`, `pkgbits/reloc.go:105`)이 붙는다. 원소 본문은 다른 원소를 직접 가리키지 않고 테이블 인덱스만 적는다. 덕분에 UIR "링커"(`noder/linker.go:39` — `cmd/link`와 무관, 파일 상단 20~34줄이 이 혼동을 직접 경고한다)가 **원소 내용을 해석하지 않고** 의존 원소를 깊이 우선으로 복사하며 인덱스만 갈아끼울 수 있다.

### 제네릭: 완전 모노모피제이션이 아니다

`shapify`(`noder/reader.go:902`)가 타입 인자의 underlying을 보고 `types.ShapePkg`(`types/type.go:2019`, = `go.shape`)의 named 타입으로 정규화한다. 메모리 레이아웃이 같은 타입들이 **코드 한 벌을 공유**한다 (GC shape stenciling). 기본 인터페이스 제약에 not-in-heap 아닌 포인터가 오면 `*uint8`로 뭉갠다.

shape로 지워진 정보(구체 타입 rtype, itab, 부속 딕셔너리, 타입 파라미터 메서드 표현식)는 **런타임 딕셔너리**로 넘긴다: `dictNameOf`(`reader.go:1439`)가 `objabi.GlobalDictPrefix`(`.dict`) 접두 심볼을 RODATA로 방출한다. 구체 인스턴스 `F[int]`는 자기 딕셔너리 주소를 추가 인자로 붙여 shaped 변형으로 tail call 하는 껍데기다 (`callShaped`, `reader.go:1375`).

### 오해 정정 (프론트엔드)

- **`gc/typecheck`가 소스를 타입체크한다** → 아니다. 소스 타입체크는 전부 `types2`가 한다. `typecheck` 패키지는 (a) `InitUniverse`/`InitRuntime` 전역 테이블, (b) reader가 만든 IR 노드에 `typecheck.Expr/Stmt`로 타입을 확정하고 `OINDEX→OINDEXMAP` 변환하는 축소된 역할만 남았다. `unified.go:168~183`에 "소스는 두 번 타입체크된다"고 명시돼 있고 장기적으로 후자를 없앨 계획이라고 적혀 있다.
- **`cmd/internal/pkgbits`** → Go 1.25에 없다. `src/internal/pkgbits`다.
- **`RelocString`/`RelocObj`** → `SectionString`/`SectionObj`로 개명됐다. 다만 `writer.go:779~800` 주석은 아직 옛 이름을 쓴다 — **코드가 맞다**.
- **export data는 iexport 포맷** → UIR이다. `$$B` 뒤 첫 바이트 `'u'`가 표식 (`noder/export.go:19`).
- **`GOEXPERIMENT=unified` 스위치가 있다** → 없다. 유일한 경로다.

## B-2. 미들엔드 — 인라인·escape·walk

### devirtualization과 inlining은 한 덩어리다

`gc.Main:240`이 부르는 `interleaved.DevirtualizeAndInlinePackage`(`inline/interleaved/interleaved.go:22`)의 구조:

```
1. profile 있으면 devirtualize.ProfileGuided  (PGO 선행 1회)   :23~31
2. inline.CanInlineFuncs                     (SCC 바텀업 일괄) :43
3. parenthesize()  — 모든 호출을 ir.ParenExpr로 감싼다        :307
4. ir.VisitFuncsBottomUp으로 SCC마다 고정점 루프:
     resolve(i): devirtualize.StaticCall + InlineCallTarget   :191
     edit(i):    inline.TryInlineCall                          :216
   ← 인라인 결과로 새 호출이 드러나면 mark로 다시 paren
5. unparenthesize()                                            :311
```

**왜 교차하는가**: devirt → 직접 호출 → 인라인 가능 → 인라인 후 새 호출 노출 → 다시 devirt. `devirtualize/pgo.go:103~104` 주석이 못을 박는다 — *"The primary benefit of this transformation is enabling inlining of the direct call."* devirt는 목적이 아니라 인라인을 위한 수단이다.

**ParenExpr 트릭**(`interleaved.go:238`): `f(g())`에서 바깥 `f`를 먼저 치환하면 안쪽 `g()`의 위치를 잃는다. 그래서 모든 호출을 `ir.ParenExpr`로 감싸 두고 `paren.X = 새노드` 한 줄로 안정 치환한다. typecheck이 진짜 괄호를 이미 다 제거해 놨으므로 재활용이 안전하다.

### 인라인 비용 모델 (실측 상수)

`hairyVisitor`(`inl.go:406`)가 예산을 깎아 나간다. `inl.go:50~61` const 블록에 전부 모여 있다:

| 상수 | 값 | 의미 |
|---|---|---|
| `inlineMaxBudget` | **80** | 기본 예산 |
| `inlineExtraCallCost` | **57** | 호출 하나당 (issue #19348 벤치 결과) |
| `inlineParamCallCost` | 17 | 파라미터 호출은 완화 |
| `inlineExtraThrowCost` | 80 | `runtime.throw` = 사실상 금지 |
| `inlineBigFunctionNodes` | **5000** | 이 이상이면 big caller |
| `inlineBigFunctionMaxCost` | 20 | big caller에는 20 이하만 |
| `inlineClosureCalledOnceCost` | 800 | 1회 호출 클로저 특례 |
| `inlineHotMaxBudget` | 2000 | PGO hot 함수 |

절대 불가 조건은 `InlineImpossible`(`inl.go:304`): `//go:noinline`, `//go:uintptrescapes`, 본문 없음 등. op 기준 거부: `OGO`/`ODEFER`/`OTAILCALL`(`inl.go:629`), `recover`(`:609`).

**실제 본문 복제는 inline 패키지가 하지 않는다.** `inline.InlineCall`은 `var` 함수 포인터(`inl.go:888`)이고, 실체는 `noder.unifiedInlineCall`(`reader.go:3461`)이 `unified.go:190`에서 주입된다. UIR을 다시 읽어 본문을 재구성하는 방식이다 — 옛 "IR 트리 딥카피" 모델이 아니다.

### escape 분석 — 왜 그래프 문제인가

`escape.Funcs`(`escape/escape.go:124`) → `Batch`(`:137`). `escape.go:20~68` 주석이 모델을 직접 설명한다.

- **location** (`graph.go:43`) = 정점 (변수 / 할당 표현식)
- **hole** (`graph.go:149`) = "지금 평가 중인 표현식의 값이 어디로(dst), 몇 번 역참조되어(derefs) 흘러가는가"
- **엣지 가중치 = 역참조 횟수 − 주소연산 횟수**: `p=&q`는 **-1**, `p=q`는 0, `p=*q`는 1, `p=**q`는 2

음수 엣지가 있으므로 최소 역참조 수 계산에 **Bellman-Ford**를 쓴다 (`solve.go:70 walkOne`, derefs를 0에서 하한 클램프해 음의 사이클 회피). `outlives`(`solve.go:282`)가 heap 결정의 실질 기준이다 — 루프 깊이가 더 얕으면 참 → **그래서 for 루프 안의 `new(int)`가 heap으로 간다.**

데이터플로우와 무관하게 무조건 heap인 경우는 `HeapAllocReason`(`utils.go:173`): `ir.MaxStackVarSize`=128KB 초과, `MaxImplicitStackVarSize`=64KB 초과 등 (`ir/cfg.go:11`).

**인터프로시저 정밀도**: `paramTag`(`escape.go:404`)가 각 파라미터의 leak 요약을 `leaks [8]uint8`(`leaks.go:16`)로 인코딩해 `types.Field.Note`에 넣고 export data에 싣는다. 호출 측은 `tagHole`(`call.go:361`)이 `parseLeaks`로 복원한다. `//go:noescape`가 본문 없는 함수에 동작하는 것도 이 경로의 특별 처리다 (`escape.go:441`).

**클로저 캡처 결정도 여기서 난다** (walk가 아니다). `flowClosure`(`escape.go:253`)의 판정은 한 줄:

```go
// escape.go:262
n.SetByval(!loc.addrtaken && !loc.reassigned && n.Type().Size() <= 128)
```

주소를 취한 적 없고, 재대입된 적 없고, 128바이트 이하일 때만 값 캡처. `-m=2`의 "capturing by value/ref"가 이 단계 출력이다.

**인라인 → escape 순서가 최적화를 만든다**: 인라인되면 callee 본문이 caller 프레임 안으로 들어와 스택에 남을 수 있다. 인라인이 할당을 줄이는 주된 메커니즘이다.

### walk — 고수준 구문의 desugar

`prepareFunc`(`gc/compile.go:92`) → `walk.Walk`(`walk/walk.go:25`) → `order(fn)`(`order.go:52`) → `walkStmtList`.

**order가 따로 있는 이유** (`order.go:24~39` 주석): `mapaccess`는 키를 **주소로** 받으므로 키가 주소 가능해야 하고, map 인덱스는 `x = m[k]` 형태로만 나타나야 한다. order가 임시변수를 도입해 이 전제를 미리 만족시킨다 (`mapKeyTemp`, `order.go:294`).

구체적인 desugar 예:

| 원본 | 변환 결과 | 위치 |
|---|---|---|
| `m[k]` | `*mapaccess1(maptype, m, &k)` / 대입이면 `*mapassign(...)`. 키 타입별 `_fast32/64/str` 특수화 | `walk/expr.go:855`, `walk/walk.go:194` |
| `range` | `ir.RangeStmt` → `ir.ForStmt`. 슬라이스는 `hu`(uintptr)/`hp`(*T) 이중 포인터로 GC 안전하게 순회 | `walk/range.go:42`, 변환식이 181~230줄 주석에 그대로 |
| `for k := range m { delete(m,k) }` | map clear 한 번으로 접음 | `walk/range.go:436 isMapClear` |
| `a+b+c` | ≤5개면 `concatstringN`, 6개↑면 `concatstrings`. `EscNone`이면 스택 버퍼 | `walk/expr.go:469` |
| type switch (구체 타입) | type hash 완전해시 점프테이블, 실패하면 이진탐색(최소 4케이스) | `walk/switch.go:388`, `:859` |
| type switch (인터페이스) | `abi.InterfaceSwitch` 디스크립터 + `runtime.interfaceSwitch` **1회 호출** + 캐시 | `walk/switch.go:528~554` |

**`append`는 walk에서 runtime 호출로 바뀌지 않는다.** `builtin.go:75~79`가 그대로 SSA에 넘긴다 — 계측 빌드(`-race`)일 때만 풀어쓴다. 단 `append(s, t...)`와 `append(s, make([]T,n)...)`는 항상 별도 처리(`assign.go:85~99`).

**`go`/`defer`의 인자 평가는 walk가 아니라 타입체크가 처리한다.** `normalizeGoDeferCall`(`typecheck/stmt.go:220`)이 인자 있는 go/defer를 "인자를 미리 평가해 캡처한 0-인자 클로저 호출"로 정규화한다. 그래서 `walkGoDefer`(`walk/stmt.go:206`)는 `call.Fun`만 walk하면 된다.

### open-coded defer — 판정이 두 군데로 나뉜다

- **walk 쪽**(`walk/stmt.go:105`): defer가 `maxOpenDefers`=**8**(`walk/walk.go:287`)을 넘거나, `DeferAt != nil`이거나, `n.Esc() != EscNever`(= 루프 안)이면 `SetOpenCodedDeferDisallowed(true)`. 8인 이유는 활성 defer를 1바이트 비트마스크(`deferBits`)로 추적하기 때문이다.
- **ssagen 쪽 최종 판정**(`ssagen/ssa.go:414~450`): `-N` 아님 && `!OpenCodedDeferDisallowed` && `-d=nodeferopen` 아님 && race 계측 아님 && heap result 파라미터 없음 && `NumReturns*NumDefers <= 15`(`:443`).

## B-3. 백엔드 — SSA에서 바이트까지

```
compileFunctions          gc/compile.go:124   ← -c=N 워커 고루틴 풀
  └ ssagen.Compile        ssagen/pgen.go:303  ← 본문이 딱 3단계
      ├ buildssa          ssagen/ssa.go:312
      │   ├ (IR 순회로 Value/Block 생성)
      │   ├ s.insertPhis()     ssa.go:608
      │   ├ ssa.Compile(s.f)   ssa.go:611  ← ★ 52개 pass가 여기서 돈다
      │   └ fe.AllocFrame      ssa.go:613  ← 프레임 오프셋 확정
      ├ genssa            ssagen/ssa.go:6603 → obj.Prog 링크드리스트
      └ pp.Flush          objw/prog.go:110 → obj.Flushplist
```

**`ssa.Compile`이 `pgen.go`가 아니라 `buildssa` 안에서 불린다.** "SSA 최적화가 어디서 시작되나"를 `pgen.go`에서 찾으면 안 보인다.

### SSA의 두 가지 핵심 아이디어

**① memory value로 순서를 표현한다.** SSA는 원래 순서 개념이 없는 데이터흐름 그래프인데, load/store/call은 순서가 중요하다. Go는 `mem`이라는 가짜 타입 값을 만들어 해결한다 — Store는 mem을 인자로 받고 새 mem을 낳으므로 두 Store 사이에 데이터 의존이 생겨 재정렬이 불가능해진다. 시작점이 `OpInitMem`(`ssagen/ssa.go:412`)이고, `memVar = ssaMarker("mem")`(`ssa.go:1099`)를 키로 `s.vars[memVar]`에 계속 갱신된다. 함수 반환 블록의 control value도 mem이어야 한다 (`ssa/README.md:95`).

**② AuxInt/Aux 두 슬롯.** `AuxInt`(int64)는 상수·오프셋·크기, `Aux`(인터페이스)는 심볼·타입·`ir.Name`. 룰 DSL의 `[c]`가 AuxInt, `{s}`가 Aux다. 이 둘 덕분에 opcode를 폭발시키지 않고 `MOVQload`처럼 심볼+오프셋 명령을 하나의 Op으로 표현한다.

### 52개 pass (`ssa/compile.go:457~511`)

실측: **52개 엔트리, 그중 `deadcode`가 8회**. 순서를 임의로 못 바꾼다 — `passOrder`(`:521`)가 제약을 명시하고 `init()`(`:588`)이 실행 시 검증해 어기면 `log.Panicf`다.

머신 독립 구간의 요점만:

- `decompose user`(462) — 문자열/슬라이스/인터페이스/복소수를 필드 Value로 분해
- `opt`(464) — `generic.rules` 기반 재작성 (상수 폴딩, 강도 감소)
- `prove`(471) — 부분순서집합(poset)으로 값 관계를 증명해 **경계검사 제거**
- `expand calls`(473) — **ABIInternal에 맞춰 호출 인자/결과를 레지스터·스택 조각으로 분해**
- `writebarrier`(485, required) — 포인터 store를 GC 배리어 분기로 확장 ← §E
- `lower`(488, required) — 여기서 generic op이 머신 op으로

`lower` 이후: `addressing modes` → `late lower` → `pair` → `lowered cse` → `checkLower`(generic op이 남아 있으면 컴파일러 크래시). 그 뒤 `critical`(임계 간선 제거) → `layout`(블록 순서) → `schedule`(블록 내 Value 순서) → `flagalloc` → **`regalloc`** → `loop rotate` → `trim`.

### 룰 DSL과 코드 생성

최적화 규칙은 S-식 DSL로 쓴다 (`ssa/_gen/*.rules`):

```
// ssa/_gen/AMD64.rules:244
(Load <t> ptr mem) && (is64BitInt(t) || isPtr(t)) => (MOVQload ptr mem)
```

`ssa/_gen/rulegen.go`(문법 정의가 35~60줄 주석)가 이를 Go 코드로 번역한다 → `ssa/rewriteAMD64.go:26131 rewriteValueAMD64_OpLoad`. 각 규칙은 `for { ...실패시 break...; v.reset(새Op); v.AddArg2(...); return true }`로 펼쳐지고 **파일 순서가 곧 우선순위**다. 생성 명령은 `ssa/generate.go:9`의 `go run -C=_gen .` — 디렉터리가 `gen`이 아니라 **`_gen`**(언더스코어, 별도 go.mod)이다.

### regalloc과 stackalloc

`regalloc.go` 상단 5~111줄 설계 주석을 반드시 읽어야 한다. 특히 `:92`:

> Note: regalloc generates a not-quite-SSA output. … **don't run deadcode after regalloc!**

정의가 사용을 지배하지 않게 되므로 이후에 `deadcode`를 돌리면 안 된다. 그래서 passes 배열에서 regalloc 뒤에 `loop rotate`와 `trim`만 남는다.

`stackalloc`은 **독립 pass가 아니다** — `regalloc` 내부(`regalloc.go:2049`)에서 불린다. `passes` 배열에서 찾다가 헤매기 쉽다.

### genssa → Prog → 바이트

`genssa`(`ssagen/ssa.go:6603`)는 **기계어를 만들지 않는다.** `obj.Prog` 링크드리스트(어셈블리 수준)만 만든다. `:6731`의 switch가 코드 안 나오는 op(`OpPhi`, `OpVarDef`, `OpSP`...)을 걸러내고 나머지는 `Arch.SSAGenValue(&s, v)`(`:6776`)로 아키텍처 백엔드에 넘긴다 (amd64는 `cmd/compile/internal/amd64/ssa.go:202`).

실제 바이트는 `pp.Flush()` → `obj.Flushplist`(`cmd/internal/obj/plist.go:24`)의 160~176줄 루프에서 나온다:

```
mkfwd → linkpatch → Arch.Preprocess(:167) → Arch.Assemble(:168) → linkpcln(:172) → populateDWARF(:173)
```

**여기가 중요하다**: `preprocess`(`obj/x86/obj6.go:602`)가 프레임 포인터 저장, `AADJSP`로 프레임 할당(`:717`), 그리고 `stacksplit`(`:1033`)으로 **morestack 프롤로그**를 넣는다. 프레임 크기가 `abi.StackSmall` 이하면 `CMPQ SP, stackguard` 한 방(`:1094`), `StackBig` 이하면 다른 코드, 그보다 크면 또 다른 시퀀스 — 3갈래다.

`Assemble`은 `span6`(`obj/x86/asm6.go:2057`)이고, 진짜 인코딩은 `ab.asmins(ctxt, s, p)`(`:2188`) 한 줄이다. 짧은 분기로 가정했다가 오프셋이 안 맞으면 전체 재인코딩을 반복하며, 1000회를 넘으면 `"span must be looping"`으로 죽는다(`:2209`).

> **SSA 덤프(`GOSSAFUNC`)에는 morestack 프롤로그가 전혀 안 보인다.** SSA/genssa가 만드는 게 아니기 때문이다.

### 어셈블러와 cgo는 같은 인프라를 쓴다

`cmd/asm/main.go`가 `obj.Linknew` → `Parse` → **`obj.Flushplist`(`:107`)** → **`obj.WriteObjFile`(`:117`)**. 컴파일러의 `pp.Flush()`와 **똑같은 함수**를 부른다. 그래서 `.s`로 쓴 함수도 자동으로 morestack 프롤로그와 PC-value 테이블을 받는다(NOSPLIT 아니면).

Go asm의 의사 레지스터는 음수 상수다: `RFP=-1, RSB=-2, RSP=-3, RPC=-4` (`cmd/asm/internal/arch/arch.go:25`). 파서가 이를 `obj.Addr.Name` 필드(`NAME_PARAM`/`NAME_AUTO`/`NAME_EXTERN`, `cmd/internal/obj/link.go:220`)로 번역하므로, `foo+8(FP)`는 물리 레지스터가 아니라 "프레임 기준 심볼 오프셋"으로 인코딩된다.

cgo는 `_cgo_gotypes.go`/`xxx.cgo1.go`/`xxx.cgo2.c`를 생성하고(`cmd/cgo/out.go:34`, `:664`), `_Cfunc_` 래퍼가 `_cgo_runtime_cgocall`(`out.go:637`)을 부르는데 이건 `//go:linkname`으로 `runtime.cgocall`에 연결된다(`out.go:1666`).

### 산출물: .a 아카이브

`dumpobj1`(`gc/obj.go:53`)이 **언제나** `!<arch>\n`(`:60`)로 시작하는 ar 아카이브를 쓰고 두 엔트리를 넣는다:

| 엔트리 | 내용 | 누가 읽는가 |
|---|---|---|
| `__.PKGDEF` | 헤더 + `\n$$B\n` + `'u'` + UIR export data + `\n$$\n` | **다음 `cmd/compile`** (링커는 무시) |
| `_go_.o` | 헤더 + (cgo pragma JSON) + `\n!\n` + goobj 바이너리 | **`cmd/link`** (컴파일러는 무시) |

`gc/obj.go:26` 주석: *"the compiler and linker read nearly disjoint sections of that file."*

goobj 포맷(`cmd/internal/goobj/objfile.go:29`의 주석에 레이아웃 그림이 있다)의 특징:
- 매직 `"\x00go120ld"`(`:218`), `Header.Offsets[NBlk]`가 블록별 오프셋 → mmap 후 필요한 블록만 읽기
- **심볼 참조가 문자열이 아니라 `SymRef{PkgIdx, SymIdx}` 32비트 쌍**(`:364`) → 링커가 해시 없이 O(1) 인덱싱
- `Sym`이 `[SymSize]byte` 고정 크기 + 접근자 메서드 → zero-copy
- content-addressable 블록(`BlkHashed64def`/`BlkHasheddef`)으로 중복 타입 서술자 제거

> **`-pack`은 아카이브를 쓸지 결정하지 않는다.** `-o`가 생략됐을 때 기본 출력 확장자를 `.o`→`.a`로 바꿀 뿐이다 (`base/flag.go:329`).

### 오해 정정 (축 B)

- **`cmd/compile/internal/deadcode` 패키지** → Go 1.25 트리에 **없다**. IR 레벨 dead code 제거는 사라졌고 SSA의 8개 `deadcode` pass가 담당한다. IR 레벨에 남은 건 `deadlocals`뿐이다.
- **`inline.InlineCalls`** → 없다. `CanInlineFuncs` + `InlineCallTarget`/`TryInlineCall`이고 묶는 쪽은 `interleaved` 패키지다.
- **호출 규약은 전부 스택** → Go 1.17+는 `ABIInternal`(레지스터)이 기본이다. amd64 정수 인자 9개(RAX,RBX,RCX,RDI,RSI,R8~R11), 부동소수 X0–X14 (`cmd/compile/abi-internal.md:390`). ABI0는 어셈블리 경계에만 남고 `makeABIWrapper`(`ssagen/abi.go:237`)가 이어 준다.
- **write barrier는 walk가 넣는다** → SSA pass다 (`ssa/compile.go:485`, `memcombine` 뒤 `lower` 앞).
- **dead store elimination pass 이름이 `deadstore`** → 파일은 `deadstore.go`지만 pass 이름과 함수는 **`dse`**다.
- **`-N`이면 모든 pass가 꺼진다** → `required: true`인 것들(`decompose user`, `opt`, `expand calls`, `writebarrier`, `lower`, `regalloc` 등)은 정확성에 필요해 항상 돈다.

---

# 축 C — cmd/link: .a 여럿을 ELF 하나로

**`ld.Main`(`cmd/link/internal/ld/main.go:161`) 아래의 `bench.Start("...")` 문자열이 공식 목차다.** 321줄부터 순서대로:

```
libinit → computeTLSOffset → Archinit → loadlib → inittasks → deadcode
→ linksetup → dostrdata → dwarfGenerateDebugInfo → callgraph → doStackCheck
→ mangleTypeSym → doelf → textbuildid → addexport → Gentext
→ textaddress → typelink → buildinfo → pclntab → findfunctab
→ dwarfGenerateDebugSyms → symtab → dodata → address → dwarfcompress → layout
→ Asmb → GenSymsLate → Asmb2 → Munmap → hostlink → Flush → archive
```

## C-1. loader — 인덱스 기반 심볼 데이터베이스

옛 링커의 `*sym.Symbol` 힙 객체와 `ctxt.Syms.Lookup`은 **없다**. 현재 `cmd/link/internal/sym`에는 `Symbol` 타입 자체가 존재하지 않는다.

```go
// cmd/link/internal/loader/loader.go:30
type Sym = sym.LoaderSym   // 실체는 uint32. 0은 무효
```

- `objSyms[i]`(`loader.go:99`) = (오브젝트 인덱스, 로컬 인덱스) 튜플 → 심볼당 8바이트
- 심볼 속성은 전부 `Bitmap`(`:109`) → **심볼당 1비트**
- 심볼 데이터는 힙에 복사되지 않는다. `Preload`(`:2139`)가 goobj를 mmap해 두고 필요할 때 원본에서 읽는다. 힙 페이로드(`extSymPayload`, `:289`)는 링커가 직접 만든 심볼이나 `cloneToExternal`로 승격한 것에만 붙는다.

`loadobjfile`(`ld/lib.go:1078`) 주석(1109~1117줄)이 중요하다: **Go 링커는 아카이브 안 오브젝트를 전부 읽는다.** 전통적 C 아카이브의 "미해결 심볼을 채우는 멤버만 꺼내기" 모델이 아니고, 안 쓰는 건 나중에 데드코드로 버린다 — *"it breaks the usual C archive model, but this is Go, not C."*

**링크 모드(internal/external)는 `loadlib` 한가운데**(`lib.go:582`)에서 확정된다. 오브젝트를 preload해서 host object 존재 여부를 봐야 판단할 수 있기 때문이다. 이 결정이 이후 거의 모든 단계에 영향을 준다 (`*FlagTextAddr`, ELF 타입, 엔트리 심볼).

## C-2. inittasks가 deadcode보다 먼저 돈다

`main.go:367`(inittasks) vs `:370`(deadcode) — 순서가 반대라고 알고 있으면 코드가 이해되지 않는다.

컴파일러(`pkginit.MakeTask`)가 패키지 p마다 `p..inittask` 심볼을 만들고, p가 q를 import하면 `R_INITORDER` relocation으로 p→q 간선을 남긴다. 링커의 `inittaskSym`(`ld/inittask.go:82`)이 루트(`main..inittask`)에서 간선을 따라가며 **Kahn 알고리즘으로 위상정렬**하되, 동률은 `lexHeap`(`:107`)으로 사전순 → **결과가 결정적이다.**

`SymSize > 8`(`:161`) 검사로 **실행할 함수가 하나도 없는 inittask는 목록에서 아예 뺀다** — 표준 라이브러리의 약 절반이 여기 해당한다고 주석에 적혀 있다.

스케줄이 끝나면 `R_INITORDER`는 의미가 없어져서 deadcode의 flood가 그냥 무시한다(`deadcode.go:255`).

> **init 순서 계산이 런타임에서 링커로 옮겨졌다.** 런타임의 `runtime.main`은 `moduledata.inittasks`를 순서대로 실행할 뿐이다.

## C-3. deadcode — 그리고 리플렉션이 바이너리를 키우는 이유

`deadcode`(`ld/deadcode.go:443`)는 루트에서 시작하는 도달성 flood fill이다. 루트(`:38 init`, `:80`): 엔트리 심볼(`_rt0_amd64_linux`, 외부 링크 exe/pie면 `main`), `runtime.unreachableMethod`, `ctxt.dynexp`, `ctxt.mainInittasks`.

**어려운 부분은 메서드다.** 메서드는 정적 호출 / 인터페이스 경유 / 리플렉션 세 경로로 불릴 수 있다 (`deadcode.go:402~442` 주석). 그래서:

1. 타입 디스크립터의 메서드마다 붙은 `R_METHODOFF` 3연속 relocation을 **곧바로 따라가지 않고** `methodref`로 보류해 `d.markableMethods`에 쌓는다 (`:184`)
2. 도달한 인터페이스 호출 지점의 `R_USEIFACEMETHOD`를 디코드해 `methodsig{name, typ}`를 `d.ifaceMethod`에 모은다 (`:232`)
3. 마지막 루프에서 시그니처가 일치하는 것만 살린다 (`:462`)

`R_USEIFACE`(`:211`)는 "이 타입이 인터페이스로 변환됐다"는 마커로 `UsedInIface`를 켜는데, 이미 방문한 타입이면 **Reachable을 일부러 끄고 다시 큐에 넣어** 자식 타입까지 전파한다 — `[]chan T`에서 리플렉션으로 `T`를 얻을 수 있기 때문이다.

**그리고 결정적인 한 줄** (`deadcode.go:143`):

```go
d.reflectSeen = d.reflectSeen || d.ldr.IsReflectMethod(symIdx)
```

`reflect.Value.Method`/`Type.Method`를 부르거나 `MethodByName`을 **상수 아닌 인자로** 부르는 함수가 하나라도 도달하면, 링커는 어떤 메서드가 불릴지 알 수 없다고 판단하고 **도달 가능한 모든 타입의 exported 메서드 전부**를 살린다. 리플렉션 한 줄이 바이너리를 키우는 메커니즘이 정확히 이것이다. 반대로 인자가 컴파일타임 상수면 컴파일러가 메서드 이름 relocation을 내보내 해당 메서드만 유지된다.

## C-4. 배치 → 주소 → relocation → ELF

`linksetup`(`lib.go:804`)에서 두 가지가 결정적이다:

- `runtime.firstmoduledata` 심볼(`:877`)의 크기를 **0으로 잘라 버린다**(`:886 mdsb.SetSize(0)`). runtime이 정의한 내용을 버리고 나중에 `symtab()`이 전부 다시 쓴다. → runtime 소스에서 초기값을 찾아봐야 아무것도 없다 (`runtime/symtab.go:483`: `var firstmoduledata moduledata // linker symbol`).
- `AssignTextSymbolOrder`(`:952`)로 `ctxt.Textp` 확정 → 이 순서가 `.text` 배치 순서이자 **pclntab 함수 테이블 순서**다.

섹션 분류는 심볼 이름이 아니라 `sym.SymKind` 기준이고, 축이 두 개다 — **포인터를 포함하는가**(GC가 스캔해야 하는가)와 **초기값이 있는가**(파일에 실을 것인가):

| SymKind | 섹션 | 파일에 실림 | GC 스캔 |
|---|---|---|---|
| `SDATA` | `.data` | ✓ | ✓ (`gcdata`) |
| `SNOPTRDATA` | `.noptrdata` | ✓ | ✗ |
| `SBSS` | `.bss` | ✗ | ✓ (`gcbss`) |
| `SNOPTRBSS` | `.noptrbss` | ✗ | ✗ |
| `sym.ReadOnly` 그룹 | `.rodata` | ✓ | ✗ |

`.data`/`.bss` 배치 **직후** 주소가 확정된 상태에서 `GCProg`(`data.go:1327`)가 포인터 위치 비트맵을 만들어 `runtime.gcdata`/`runtime.gcbss`에 쓴다 (`data.go:1984`).

**relocation은 별도 패스가 아니다.** `writeBlock`(`data.go:1098`)이 심볼 바이트를 출력 파일 mmap에 복사한 **바로 그 자리에서** `relocsym(s, P)`(`data.go:194`)을 호출해 버퍼 위에 값을 박는다. 그래서 relocation 오류가 링킹 거의 마지막(Asmb)에 튀어나온다.

ELF 출력(`elf.go:1795 asmbElf`)의 마지막 결정:

```
LinkExternal  → ET_REL   (:2339)  → hostlink(gcc/clang)가 마무리
BuildModePIE  → ET_DYN   (:2341)
그 외         → ET_EXEC  (:2343)
eh.Entry = Entryvalue(ctxt)  (:2347) ← internal link일 때만
```

동적 의존이 하나도 없으면 `linksetup`에서 `*FlagD = true`(`lib.go:840`)가 되어 `PT_INTERP`도 `.dynamic`도 생성되지 않는다 → 커널이 ld.so 없이 바로 엔트리로 점프하는 **완전 정적 바이너리**다.

---

# 축 D — 실행: execve부터 GMP 루프까지

## D-1. TLS가 서기 전과 후

```asm
_rt0_amd64_linux        rt0_linux_amd64.s:7    → JMP _rt0_amd64
_rt0_amd64              asm_amd64.s:15
    MOVQ 0(SP), DI      // argc  ← 커널이 만든 초기 스택
    LEAQ 8(SP), SI      // argv
    JMP  runtime·rt0_go
```

**함수 호출이 아니라 점프**다. 리턴 주소가 쌓이지 않고 SP는 여전히 커널이 준 원본 스택이다.

`runtime·rt0_go`(`asm_amd64.s:159`)에서 일어나는 일의 **순서가 전부**다:

| 줄 | 하는 일 | 왜 이 순서인가 |
|---|---|---|
| 161–166 | SP 16바이트 정렬, argc/argv를 24(SP)/32(SP)에 대피 | |
| **170–175** | **OS 스택을 `runtime·g0`의 스택으로 등록**: `stack.hi=SP`, `stack.lo=SP-64KB` | 힙이 없으므로 g0는 BSS 전역(`proc.go:119`), 스택은 커널 스택을 빌린다 |
| 178–195 | CPUID → `isIntel`, `processorVersionInfo` | |
| 222–227 | `_cgo_init` 있으면 호출 + stackguard 정정 | |
| **258–259** | `settls(&m0.tls)` → `arch_prctl(ARCH_SET_FS, &m0.tls[0]+8)` (`sys_linux_amd64.s:637`) | ELF 관례가 `-8(FS)`라서 `+8` 보정 (`:642`) |
| 262–267 | g 슬롯에 0x123 써 넣고 되읽어 검증, 다르면 abort | |
| **268–278** | `ok:` — g 레지스터=g0, `m0.g0=&g0`, `g0.m=&m0` | **이 시점부터 `getg()`가 동작 → Go 코드 호출 가능** |
| 282–339 | GOAMD64 v2/v3/v4 요구사항 검사 | 실패 시 메시지를 출력해야 하므로 TLS 뒤에 배치 (issue #49586) |
| **341** | `CALL runtime·check` | Go 코드로 진입하는 첫 호출 |
| 343–347 | argc/argv를 0(SP)/8(SP)로 옮겨 `CALL runtime·args` | |
| 348 | `CALL runtime·osinit` | |
| **349** | `CALL runtime·schedinit` | |
| 352–355 | `MOVQ $runtime·mainPC, AX; PUSHQ AX; CALL runtime·newproc` | 첫 goroutine |
| **358** | `CALL runtime·mstart` | 돌아오지 않는다 (`:360`이 abort) |

**auxv 파싱**: `args`(`runtime1.go:67`) → `sysargs`(`os_linux.go:240`)가 argv 뒤 envp를 NULL까지 건너뛰어 auxv 시작을 계산하고, `sysauxv`(`:301`)가 `AT_RANDOM`(→startupRand), `AT_PAGESZ`(→physPageSize), `AT_SECURE`를 뽑는다. Go는 libc 없이 도니 `getauxval(3)`을 못 쓴다. `physPageSize`가 0이면 `mallocinit`이 throw하므로 **이 단계는 힙 초기화의 전제조건**이다.

## D-2. schedinit — 순서가 곧 의존관계

`schedinit`(`proc.go:832`)은 함수 바로 위 824~831줄 주석에 부트스트랩 순서를 명시해 뒀다. 주요 지점:

| 줄 | 호출 | 왜 여기인가 |
|---|---|---|
| 868 | `getGodebugEarly()` (`:794`) | envp를 직접 훑어 GODEBUG만 먼저 꺼낸다 — cpuinit이 `cpu.*` 옵션을 필요로 함 |
| 873 | `moduledataverify()` | pclntab 매직·minLC·ptrSize·ftab 정렬 검증 |
| 874 | `stackinit()` | `malg`보다 먼저여야 함 |
| 875 | `mallocinit()` | 힙 |
| 876 | `cpuinit(godebug)` | `alginit` 전 |
| 877 | `randinit()` | AT_RANDOM 시드 |
| 878 | `alginit()` | **이 호출 전에는 맵/해시/rand 사용 금지** |
| 879 | `mcommoninit(gp.m, -1)` | m0에 id 부여, allm 등록 |
| **880–883** | `modulesinit` / `typelinksinit` / `itabsinit` / `stkobjinit` | ★ 링커 산출물 소비 → §E |
| 888–889 | `goargs()` / `goenvs()` | 맵·힙이 준비된 뒤여야 문자열 슬라이스를 만들 수 있다 |
| 898 | `gcinit()` | GOGC/GOMEMLIMIT |
| 916–934 | GOMAXPROCS 결정 | ↓ |
| 935 | `procresize(procs)` | allp 확장, allp[0]을 m0에 붙임 |

**`mallocinit`은 힙 메모리를 실제로 매핑하지 않는다** (`malloc.go:375`). 64비트에서는 `for i := 0x7f; i >= 0; i--` 루프로 arenaHint 128개만 만들고(주소는 `uintptr(i)<<40 | 0x00c0<<32`, `:520~555`), 절반(i > 0x3f)은 `userArena.arenaHints`로 간다. 실제 예약은 나중에 `mheap.sysAlloc`이 힌트를 따라간다.

**mcache0 부트스트랩 트릭**: P가 없는데 할당이 필요하므로 `mallocinit`이 `mcache0 = allocmcache()`(`malloc.go:464`)를 만들고, `procresize`에서 id==0인 P만 이걸 물려받은 뒤(`proc.go:5757`) `mcache0 = nil`로 비운다(`:5966`).

### Go 1.25: GOMAXPROCS가 컨테이너를 인식한다

```go
// proc.go:921~934
GOMAXPROCS 환경변수가 양수 → 그대로 + sched.customGOMAXPROCS = true
아니면 → defaultGOMAXPROCS(numCPUStartup)
```

`defaultGOMAXPROCS`(`cgroup_linux.go:85`)가 **`sched_getaffinity` CPU 수와 cgroup의 quota/period 처리량 상한 중 작은 쪽**을 취한다. 상한은 ceil로 올림하고 최소 2로 클램프(`:109~117`). 게다가 `runtime.main`이 `defaultGOMAXPROCSUpdateEnable`(`proc.go:6691`)로 감시 goroutine을 띄워 cgroup 한도가 바뀌면 갱신한다.

끄는 방법: `GODEBUG=containermaxprocs=0`(초기값 반영), `updatemaxprocs=0`(자동 갱신). GOMAXPROCS를 명시하면 둘 다 무력화된다.

## D-3. 첫 goroutine과 goexit 트릭

`newproc1`(`proc.go:5176`)에서 gobuf 세팅이 핵심이다:

```go
// proc.go:5210~5215
memclrNoHeapPointers(&newg.sched, ...)
newg.sched.sp = newg.stack.hi - totalSize
newg.sched.pc = abi.FuncPCABI0(goexit) + sys.PCQuantum   // ★
newg.sched.g  = guintptr(unsafe.Pointer(newg))
gostartcallfn(&newg.sched, fn)
```

`gostartcallfn`(`stack.go:1183`) → `gostartcall`(`sys_x86.go:16`)이 sp를 한 칸 내려 **기존 pc(`goexit+PCQuantum`)를 리턴 주소로 밀어 넣고** pc를 `fn`으로 바꾼다.

**결과**: goroutine 함수가 평범하게 `RET`하면 자연스럽게 `runtime·goexit`(`asm_amd64.s:1692`)으로 돌아가 `goexit1`→`goexit0`로 정리된다. 마치 goexit이 함수를 호출한 것처럼 스택을 조작하는 것이다. `+PCQuantum`은 "리턴 주소 - 1"이 goexit 범위 안에 들어오게 해 traceback이 깨지지 않게 하는 보정이다.

`mainPC`(`asm_amd64.s:383`)는 `runtime.main<ABIInternal>` 주소를 담은 8바이트 RODATA다. **ABI0 래퍼가 아니라 ABIInternal 심볼**이어야 하는데(`:380~382` 주석), newproc이 만든 gobuf가 래퍼를 거치지 않고 직접 점프하기 때문이다. (반대로 어셈블리에서 `newproc`을 부를 때 `PUSHQ`로 인자를 넘기는 건 링커가 ABI0 래퍼를 경유시키므로 정상이다.)

## D-4. mstart → schedule → gogo

```
runtime·mstart      asm_amd64.s:394   TOPFRAME|NOFRAME 스텁 (proc.go:1858은 본문 없는 선언!)
└ mstart0           proc.go:1869      OS 스택 경계 추정, stackguard0 = stack.lo + stackGuard
  └ mstart1         proc.go:1911
      ├ save(pc, sp) → g0.sched      :1924~1926  ★ M의 랜딩 포인트
      ├ asminit / minit               (시그널 스택, sigmask)
      ├ mstartm0()                    m0만: initsig(시그널 핸들러 설치)
      └ schedule()                    :1949 — 돌아오지 않는다
```

`mstart1:1924~1926`이 자기 호출자의 pc/sp를 `g0.sched`에 저장하는 게 중요하다. 이후 모든 `mcall`/`goexit0`가 `gogo(&g0.sched)`로 **이 지점에 되돌아와** `mexit`로 스레드를 정리한다.

`schedule`(`proc.go:4123`) → `findRunnable`(`:3377`) → `execute`(`:3336`) → `gogo(&gp.sched)`(`:3370`). `gogo`(`asm_amd64.s:404`)는 gobuf에서 g/sp/bp/ctxt/pc를 복원하고 JMP한다 — **리턴이 아니라 longjmp**. 이 순간 실행 컨텍스트가 g0 스택에서 사용자 goroutine 스택으로 갈아탄다.

## D-5. runtime.main → main.main

`runtime.main`(`proc.go:148`)의 순서:

```
159  maxstacksize = 1e9 (1GB), maxstackceiling = 2배
170  mainStarted = true            ← 이 전에는 newproc이 wakep을 안 해 M이 늘지 않는다
174  newm(sysmon, nil, -1)         ← P 없이 도는 감시 스레드 (haveSysmon일 때만)
184  lockOSThread()                ← init 동안 main goroutine을 m0에 고정
202  doInit(runtime_inittasks)     ← ★ defer보다도 먼저. runtime 자신의 init이 최우선
212  gcenable()                    ← bgsweep/bgscavenge 2개 기동 + enablegc = true
213  defaultGOMAXPROCSUpdateEnable()
255  for m := &firstmoduledata; ...; { doInit(m.inittasks) }   ← 사용자 패키지 init
263  close(main_init_done)
266  unlockOSThread()
284  fn := main_main; fn()         ← ★ 간접 호출
324  runExitHooks(0)
327  exit(0)                       ← 다른 goroutine을 기다리지 않는다
```

**`main.main`과의 연결은 `//go:linkname main_main main.main`**(`proc.go:135`) 한 줄이다. 직접 `CALL`이 아니라 변수 경유인 이유는 링커가 runtime을 배치할 때 main 패키지 주소를 모르기 때문이다.

`doInit1`(`proc.go:7641`)은 state를 0→1→2로 옮기며 실행하고, **실행 중(state==1)에 재진입하면 `"linker skew"`로 throw**한다 — 링커가 이미 순환을 제거했어야 하니까.

## D-6. main.main이 도는 동안

여기서부터가 GMP의 본편이다. HTTP 서버를 예로 잡는다.

### findRunnable의 탐색 우선순위 (`proc.go:3377`)

이 순서가 스케줄러의 정체다:

| # | 소스 | 줄 |
|---|---|---|
| 1 | gcwaiting이면 `gcstopm` | 3391 |
| 2 | 트레이스 리더 | 3407 |
| 3 | GC 마크 워커 (`findRunnableGCWorker`) | 3421 |
| 4 | **61번마다 전역 큐 먼저** (`schedtick%61==0`) | 3431 |
| 5 | 로컬 런큐 `runqget` | 3457 |
| 6 | 전역 런큐에서 **배치로 절반**(128개) `globrunqgetbatch` | 3464 |
| 7 | non-blocking `netpoll(0)` | 3484 |
| 8 | **work stealing** `stealWork` (4회 시도) | 3510 |
| 9 | idle 마크 워커 | 3533 |
| 10 | P 반납(`releasep`→`pidleput`) 후 **모든 소스 재확인** | 3604~3714 |
| 11 | blocking `netpoll(delay)` — 서버가 idle이면 대부분 스레드가 여기 | 3720~3742 |
| 12 | `stopm()` — M을 재운다 | 3784 |

④의 61은 로컬 큐의 두 G가 서로 되살리며 전역 큐를 굶기는 걸 막는 공정성 장치다.

⑩의 `3610~3645` **"Delicate dance"** 주석을 반드시 읽어야 한다. `nmspinning`을 먼저 내리고 모든 소스를 재확인해야 하는 이유를 설명한다 — 순서를 뒤집으면 **일감이 있는데 아무도 깨지 않는** work-conservation 위반이 생긴다. 짝이 되는 계약이 `handoffp`(`:3136`)의 3137~3138 주석이다: *"findrunnable이 G를 리턴할 상황이면 handoffp는 반드시 M을 시작해야 한다."* **이 두 함수는 항상 나란히 놓고 봐야 한다.**

### 블로킹의 종착지는 언제나 gopark/ready 한 쌍

```
gopark          proc.go:443
├ m.waitlock / m.waitunlockf에 인자를 얹는다   :453~457
│   (G 스택을 떠나면 못 쓰니까. runtime2.go:585~586 "That is their sole purpose")
└ mcall(park_m)                                :460
    park_m      proc.go:4229
    ├ casgstatus(_Grunning → _Gwaiting)        :4251  ★ 락 해제보다 먼저
    ├ dropg()                                  :4256
    ├ unlockf()                                :4258
    └ schedule()                               :4280  ← M은 놀지 않는다
```

`:4251`이 `unlockf` **앞**에 오는 게 중요하다. 먼저 락을 풀면 다른 스레드가 아직 `_Grunning`인 G를 ready하려 들 수 있다 (`gopark` 423~427 주석).

| 무엇이 막히면 | 어디서 gopark | 누가 깨우나 |
|---|---|---|
| 채널 송신 | `chan.go:283` | `chan.go:745 goready` (recv) |
| 채널 수신 | `chan.go:667` | `chan.go:350 goready` (send) |
| `sync.Mutex` 경합 | `sema.go:192 goparkunlock` | `sema.go:263 readyWithTime` |
| 네트워크 I/O | `netpoll.go:575` | `netpoll.go:494 netpollready` |

### netpoll — Accept가 goroutine park으로 바뀌는 실제 경로

```
(*Server).Serve                  net/http/server.go:3433
├ l.Accept()                     :3463
│   → net/tcpsock.go:376 → tcpsock_posix.go:158 → net/fd_unix.go:160
│   → internal/poll/fd_unix.go:594 (*FD).Accept
│       accept4() = EAGAIN → fd.pd.waitRead(:613)
│       → fd_poll_runtime.go:88 → :80 wait → :84 runtime_pollWait
│           (본문 없는 선언, :25)
│         ★ //go:linkname 경계
│       → runtime/netpoll.go:342 poll_runtime_pollWait
│         → netpollblock (:548)
│             gpp.CAS(pdReady, pdNil)  :557  ← 이미 온 알림 먼저 소비
│             gopark(netpollblockcommit, ...) :575  ★ 여기서 잠든다
└ go c.serve(connCtx)             :3493
```

커널 쪽: `netpollinit`(`netpoll_epoll.go:21`)이 `epoll_create1` + netpollBreak용 eventfd, `netpollopen`(`:49`)이 **`EPOLLET`(엣지 트리거)**로 등록하며 `ev.Data`에 `taggedPointer(pd, fdseq)`(`:52`)를 넣는다 — fd 재사용 시 stale 이벤트를 거르는 태그다.

깨우기: `netpoll(delay)`(`:99`) → `epoll_wait`(`:119`) → `netpollready`(`:171`) → `netpollunblock`(`netpoll.go:591`)이 `pd.rg`에서 G를 꺼내 `gList`에 push → `findRunnable`로 돌아가 하나는 즉시 실행, 나머지는 `injectglist`(`proc.go:4033`)로 뿌린다.

`pd.rg`/`wg`는 `pdNil`/`pdReady`/`pdWait`/`*g` **4상태 원자 변수**다. netpollblock은 park 전에 pdReady를 소비해 보고, netpollunblock은 pdReady를 먼저 심고 G를 꺼낸다 — 이 비대칭 순서가 "막 park하려는데 이벤트 도착" 경쟁에서 알림을 잃지 않게 한다.

### syscall — netpoll을 못 쓸 때

`reentersyscall`(`proc.go:4574`):

```
4586  gp.stackguard0 = stackPreempt; throwsplit = true   ← 스택 성장 금지
4590  save(pc, sp, bp) → g.sched                          ← GC/traceback이 읽을 수 있게
4594  casgstatus(_Grunning → _Gsyscall)
4636~4640  pp.m = 0; gp.m.oldp = pp; gp.m.p = 0; pp.status = _Psyscall
           ← M과 P를 느슨하게 끊는다
```

짧게 끝나면 `exitsyscallfast`(`:4887`)가 `oldp.status`를 `_Psyscall→_Pidle`로 CAS(`:4895`)해 **원래 P를 되찾는다 — 락도 스케줄러도 안 거친다.**

길어지면 sysmon의 `retake`(`:6392`)가 개입한다. `_Psyscall`이고 `syscalltick`이 안 변한 채 1 tick(≥20us) 지났고, (로컬 큐에 일감 있음 ‖ 여유 M 없음 ‖ 10ms 경과)이면 → CAS(`:6448`) → `handoffp`(`:6455`)로 P를 다른 M에게 넘긴다.

처음부터 오래 걸릴 걸 아는 호출은 `entersyscallblock`(`:4724`)이 `handoffp(releasep())`(`:4778`)로 즉시 넘긴다.

### sysmon — P 없이 도는 감시 스레드

`sysmon`(`proc.go:6228`)은 20us에서 시작해 idle 50회를 넘기면 두 배씩 늘어 최대 10ms까지 가는 적응형 주기로 돈다(`:6240~6248`). 하는 일 넷:

1. 마지막 netpoll이 10ms를 넘었으면 직접 `netpoll(0)` → `injectglist` (`:6311~6327`)
2. `retake(now)`(`:6359`) — 10ms 넘게 도는 G 선점 + syscall P 회수
3. 2분(`forcegcperiod`, `:6214`) GC가 없었으면 forcegc goroutine 깨우기 (`:6365`)
4. `GODEBUG=schedtrace` 출력 (`:6373`)

### 선점 — 두 가지가 동시에 걸린다

`preemptone`(`proc.go:6495`):

**① 협조적** (`:6505`, `:6511`)
```go
gp.preempt = true
gp.stackguard0 = stackPreempt   // 아주 큰 값
```
`stackPreempt`가 커서 컴파일러가 모든 non-nosplit 함수 프롤로그에 넣은 `SP vs stackguard0` 비교가 **반드시 실패**하고 `morestack`(`asm_amd64.s:579`)으로 빠진다. `newstack`(`stack.go:1015`)이 `stackguard0 == stackPreempt`인지 확인해(`:1074`) 성장 요청과 선점 요청을 구분한다.

→ **한계**: 함수 호출이 없는 타이트 루프는 프롤로그가 안 돌아 영원히 선점되지 않는다.

**② 비동기** (Go 1.14+, `:6516`)
```
preemptM              signal_unix.go:368   signalPending CAS로 중복 방지
└ signalM(mp, sigPreempt)   :385          sigPreempt = _SIGURG (:73), tgkill
    → sighandler          :685
      └ doSigPreempt      :341
          └ ctxt.pushCall(abi.FuncPCABI0(asyncPreempt), newpc)   :347
            ★ 시그널 컨텍스트의 PC를 조작해 함수 호출을 "주입"한다
    시그널 복귀 → asyncPreempt (preempt_amd64.s:7, 모든 레지스터 스필)
      → asyncPreempt2 (preempt.go:302) → mcall(preemptPark 또는 gopreempt_m)
```

`isAsyncSafePoint`(`preempt.go:363`)가 M 상태(`canPreemptM`)·스택 여유(`asyncPreemptStack`)·unsafe-point 여부를 검사한다. `asyncPreempt` 프레임은 정확한 포인터 맵이 없으므로 **GC가 그 프레임과 부모 프레임을 보수적으로 스캔한다** (`preempt.go:295~296`).

`GODEBUG=asyncpreemptoff=1`로 끌 수 있다.

### 스택 성장 — 왜 스택을 옮길 수 있는가

goroutine 스택은 `stackMin`=**2048바이트**(`stack.go:76`)에서 시작한다.

```
newstack        stack.go:1015
├ newsize = oldsize * 2                          :1131
├ funcMaxSPDelta(f)로 필요 프레임이 들어갈 때까지 더 늘림   :1136~1143
├ newsize > maxstacksize(1GB) → "stack overflow"  :1152
├ casgstatus(_Grunning → _Gcopystack)             :1164  ← 이 동안 GC가 스캔하지 않는다
└ copystack                                       :899
    ├ stackalloc(newsize)                         :915
    ├ adjinfo.delta = new.hi - old.hi             :926
    ├ adjustsudogs / syncadjustsudogs             :938, :951  ← 채널이 스택을 가리킬 수 있다
    ├ memmove                                     :955  ← 주소가 전부 바뀐다
    └ unwinder로 프레임 순회 → adjustframe         :976
        └ frame.getStackMap(true)                 :733  ★★★
```

**`:733`이 답이다.** `getStackMap`(`stkframe.go:157`)이 읽는 것:

- `FUNCDATA_LocalsPointerMaps` (`stkframe.go:192`) — 지역변수 포인터 비트맵
- `FUNCDATA_ArgsPointerMaps` (`:219`) — 인자/반환값 포인터 비트맵
- `FUNCDATA_StackObjects` (`:245`) — 주소가 잡힌 스택 오브젝트

**이 FUNCDATA는 전부 컴파일러가 각 함수에 붙여 둔 메타데이터다.** "어느 스택 슬롯이 포인터인지"를 컴파일러가 정확히 알려주기 때문에, 런타임이 스택을 통째로 다른 주소로 옮기고도 내부 포인터를 전부 고쳐 쓸 수 있다 (`adjustpointers`, `stack.go:652`). 이게 §E의 핵심이다.

### 할당과 동시 GC

```
mallocgc            malloc.go:1014
├ gcBlackenEnabled != 0 → deductAssistCredit(size)  :1047~1048
│   → g.gcAssistBytes가 음수면 gcAssistAlloc(mgcmark.go:441)  ← mark assist
├ 크기·포인터 유무로 분기: Tiny(1110) / SmallNoscan(1266)
│   / SmallScanNoHeader(1352) / SmallScanHeader(1443) / Large(1536)
├ mcache(락 없음) → mcentral(spanClass별 락) → mheap(전역 락)  3계층
│   nextFree(:958) → mcache.refill(mcache.go:149)
│   → mcentral.cacheSpan(mcentral.go:82) → mheap.alloc(mheap.go:1006)
└ gcTrigger{gcTriggerHeap}.test() → gcStart(mgc.go:643)
```

**GC는 별도 전용 스레드가 아니다.** `gcBgMarkWorker`(`mgc.go:1428`)는 평범한 goroutine이고 평소 `gopark`(`:1463`)으로 잔다. `findRunnable`(`proc.go:3421`)이 `gcController.findRunnableGCWorker`(`mgcpacer.go:754`)를 호출해 **스케줄러가 직접 골라 실행**한다. 게다가 할당하는 goroutine 자신도 mark assist로 동원된다.

### 종료

- **일반 goroutine**: 함수 리턴 → `goexit`(`asm_amd64.s:1692`) → `goexit1`(`proc.go:4431`) → `mcall(goexit0)` → `gdestroy`(`:4452`) → `gfput`(`:5320`)로 **G를 P의 gFree에 넣어 재사용**(`gfget`, `:5362`) → `schedule()`. **goroutine 종료는 스레드 종료가 아니다.**
- **main goroutine**: `runtime.main`으로 복귀 → `runExitHooks`(`:324`) → `exit(0)`(`:327`) → `exit_group` syscall(`sys_linux_amd64.s:51`)
- **데드락**: `checkdead`(`:6105`)가 실행 중 M이 0이고(`:6134`) 모든 G가 `_Gwaiting`/`_Gpreempted`이며 남은 타이머도 없으면(`:6200`) `fatal("all goroutines are asleep - deadlock!")`(`:6206`)

---

# 축 E — 관통 계약: 컴파일러가 심고, 링커가 조립하고, 런타임이 읽는다

**이게 4단계 구분에 추가해야 하는 축이다.** 단계별로 나열하면 보이지 않지만, Go의 특징적인 런타임 기능은 전부 이 3자 계약에서 나온다.

| 계약 | 컴파일러가 심는다 | 링커가 조립한다 | 런타임이 읽는다 | 그래서 가능해지는 것 |
|---|---|---|---|---|
| **포인터 맵** | `FUNCDATA_Locals/ArgsPointerMaps`, `StackObjects` | `go:func.*` 캐리어 밑에 묶어 배치 | `getStackMap` (`stkframe.go:157`) | **정확한 GC**, `copystack`으로 **스택 이동** |
| **pclntab** | `Pcln` (PC-value 테이블, `linkpcln`) | `pcln.go:792` — 매직 `0xfffffff1` + funcnametab/cutab/filetab/pctab/functab, 함수당 `_func` **44바이트**(`funcSize = 11*4`) | `pcHeader`(`symtab.go:374`), `_func`(`runtime2.go:906`), `findfunc`(`symtab.go:915`) | **traceback**, GC 스택 스캔, `runtime.Caller` |
| **moduledata** | (runtime이 심볼만 선언) | `linksetup`이 크기 0으로 자르고 `symtab`(`symtab.go:623`)이 전부 다시 씀 | `moduledata`(`symtab.go:394`) — 필드 순서가 곧 ABI | 위 전부의 출발점. `moduledataverify1`(`:615`)가 어긋나면 즉시 throw |
| **typelinks** | 타입 디스크립터 + `IsTypelink` 마킹 | 타입 문자열로 정렬된 4바이트 `R_ADDROFF` 배열 (`typelink.go:23`) | `typelinksinit`(`type.go:438`) | `reflect.typelinks()` |
| **itablinks** | `go:itab.*` 심볼 | `*itab` 포인터 배열 | `itabsinit`(`iface.go:259`) → 전역 해시테이블 | 자주 쓰는 **인터페이스 변환이 런타임 itab 생성 없이 동작** |
| **gcdata/gcbss** | 전역 변수 타입 정보 | `.data`/`.bss` 배치 직후 `GCProg`로 포인터 비트맵 생성 (`data.go:1984`) | `modulesinit`이 `progToPointerMask`로 풀어 `gcdatamask` | GC의 **전역 루트 스캔** |
| **init 순서** | `p..inittask` + `R_INITORDER` relocation | 위상정렬 + 사전순 → `go:main.inittasks` (`inittask.go:82`) | `doInit1`(`proc.go:7641`) | **결정적** 패키지 초기화 순서 |
| **write barrier** | `ssa/writebarrier.go:164`가 포인터 store를 `if writeBarrier.enabled { gcWriteBarrier2(); ... }`로 재작성 | — | `writeBarrier`(`mgc.go:237`), `wbBuf`(`mwbbuf.go:42`, 512칸), `gcWriteBarrier1~8`(`asm_amd64.s:1807~`) | **동시 마킹** |
| **스택 확장** | `preprocess`/`stacksplit`(`obj6.go:1033`)이 프롤로그에 `CMPQ SP, stackguard` | — | `morestack`→`newstack` | **2KB에서 시작하는 성장 스택** |
| **선점** | 위와 같은 프롤로그 체크 | — | `gp.stackguard0 = stackPreempt`(`proc.go:6511`) | 스택 체크 하나를 **선점에 겸용** |
| **제네릭 딕셔너리** | `.dict` RODATA 심볼(`reader.go:1439`) + shaped 호출 규약 | 배치만 | (코드가 직접 참조) | GC shape stenciling |

**깨지기 쉬운 상수 짝**을 하나만 예로 들면:

```
cmd/compile/internal/ssa/writebarrier.go:172   const maxEntries = 8
runtime/mwbbuf.go:74                           wbMaxEntriesPerCall = 8
runtime/asm_amd64.s:1807~                      gcWriteBarrier1 … gcWriteBarrier8
```
한쪽만 고치면 **조용히** 깨진다. 마찬가지로 `pcln.go:20 funcSize = 11*4`와 `runtime2.go:906 _func`가 어긋나면 스택 트레이스가 즉시 깨진다.

그리고 write barrier의 실제 형태 (`ssa/writebarrier.go:155~160` 주석):

```go
if writeBarrier.enabled {
    buf := gcWriteBarrier2()
    buf[0] = val      // 새 값 (insertion barrier)
    buf[1] = *ptr     // 예전 값 (deletion barrier)  ← hybrid!
}
*ptr = val
```

**Dijkstra 스타일 삽입 배리어만 있다고 알려진 것과 달리 hybrid(deletion + insertion)다.**

---

# 요약: Go 1.25 기준 오해 정정 모음

옛 자료를 볼 때 바로 걸러야 하는 것들:

| 옛 설명 | Go 1.25 실제 | 근거 |
|---|---|---|
| mtime으로 재빌드 판정 | content-based (파일 내용 해시 + build ID) | `work/buildid.go:388, 416` |
| `$GOROOT/pkg`에 stdlib `.a` 사전 배포 | 1.20부터 안 함 | `work/exec.go:266~270` |
| `gc/typecheck`가 타입체커 | `types2`가 타입체크, `typecheck`는 헬퍼 | `unified.go:168~183` |
| export data = iexport | UIR(pkgbits), 표식 `'u'` | `noder/export.go:19` |
| `cmd/internal/pkgbits` | `internal/pkgbits` | — |
| `RelocString`/`RelocObj` | `SectionString`/`SectionObj` | `pkgbits/reloc.go:13` |
| `deadcode` 패키지가 IR을 정리 | 패키지 자체가 없음. SSA pass 8개 | `ssa/compile.go:460~500` |
| `inline.InlineCalls` | `interleaved.DevirtualizeAndInlinePackage` | `gc/main.go:240` |
| devirt와 inline이 별개 패스 | 고정점 교차 실행 | `interleaved/interleaved.go:22` |
| 인자는 항상 스택 (ABI0) | ABIInternal(레지스터)이 기본 | `abi-internal.md:390` |
| `ssa/gen` 디렉터리 | `ssa/_gen` (별도 go.mod) | `ssa/generate.go:9` |
| `*sym.Symbol` + `ctxt.Syms.Lookup` | `loader.Sym`(uint32) + `Loader` + Bitmap | `loader/loader.go:30` |
| 아카이브에서 필요한 오브젝트만 꺼냄 | 전부 읽고 나중에 데드코드로 버림 | `ld/lib.go:1109~1117` |
| 런타임이 import 그래프를 재귀 순회해 init | 링커가 위상정렬해 평탄한 배열로 넘김 | `ld/inittask.go:82` |
| pclntab = Go 1.2 포맷 | 매직 `0xfffffff1` pcHeader 기반, 함수 엔트리는 `runtime.text` 상대 오프셋 | `ld/pcln.go:792` |
| 협조적 선점만 → 타이트 루프 못 멈춤 | SIGURG 비동기 선점 (1.14+) | `signal_unix.go:347` |
| 고루틴이 블로킹되면 스레드도 블로킹 | 네트워크는 netpoll로 고루틴만 park | `netpoll.go:575` |
| GOMAXPROCS = NumCPU | cgroup 상한 반영 + 실행 중 갱신 (1.25) | `cgroup_linux.go:85` |
| GC 전용 스레드가 있다 | 마크 워커는 평범한 goroutine, 스케줄러가 고름 | `proc.go:3421` |
| write barrier는 insertion만 | hybrid (insertion + deletion) | `ssa/writebarrier.go:157~158` |
| `sched.runq`가 (head,tail,size) 3필드 | `gQueue` 타입 하나, 길이는 `.size` | `proc.go:7318` |
| 전역 큐에서 하나씩 가져옴 | `globrunqgetbatch`로 128개 배치 | `proc.go:3464` |

---

# 학습 경로: 이 순서로 파세요

**1주차 — 축 A (전체 그림 잡기)**
```
cmd/go/main.go:99  →  work/build.go:460 runBuild
work/action.go:82 Action, :544 CompileAction, :690 LinkAction
work/exec.go:73 Do, :241 buildActionID, :464 build
work/buildid.go 상단 60~97줄 주석  ← 반드시
work/gc.go:57 gc
```
실습: `go build -work -x`로 실제 `$WORK/bNNN`을 열어 `importcfg`를 눈으로 볼 것. `-debug-actiongraph`로 DAG를 JSON으로 뽑을 것.

**2주차 — 축 B 프론트엔드**
```
cmd/compile/internal/gc/main.go:61 Main  ← Timer 호출이 목차
noder/noder.go:27 LoadPackage
noder/irgen.go:26 checkFiles
noder/unified.go:148~188 주석  ← ★ 왕복의 근거
noder/doc.go:11 UIR 문법(EBNF)
internal/pkgbits/reloc.go:40~101 주석  ← 참조 테이블 설계
noder/reader.go:902 shapify, :1439 dictNameOf
```

**3주차 — 축 B 미들엔드**
```
escape/escape.go:20~68 주석  ← ★ 먼저 읽을 문서
escape/solve.go:70 walkOne, :282 outlives
inline/inl.go:50~61 상수, :433 doNode
inline/interleaved/interleaved.go:22
walk/order.go:24~39 주석 → walk/range.go:181~230
```
실습: `go build -gcflags='-m -m'`을 작은 파일에 걸고 escape/인라인 판정을 소스와 대조.

**4주차 — 축 B 백엔드**
```
ssa/README.md  ← 전체
ssa/compile.go:457 passes 배열  ← 그냥 통독
ssa/regalloc.go:5~111 주석  ← ★
ssa/_gen/AMD64.rules:244  ↔  ssa/rewriteAMD64.go:26131  (1:1 비교)
cmd/internal/obj/plist.go:160~176
cmd/internal/obj/x86/obj6.go:1033 stacksplit
```
실습: `GOSSAFUNC=함수명 go build` → `ssa.html`을 브라우저로 열기. pass별 변화를 볼 수 있다.

**5주차 — 축 C**
```
cmd/link/internal/ld/main.go:321 이후 bench.Start 목록  ← 목차
loader/loader.go:181 Loader, :2273 LoadSyms
ld/deadcode.go:402~442 주석  ← ★ 메서드 3경로
ld/pcln.go:799~826 주석  ← pclntab 레이아웃
ld/symtab.go:623 이후  ↔  runtime/symtab.go:394  (나란히 놓고)
```

**6주차 — 축 D**
```
runtime/asm_amd64.s:159 rt0_go  ← 한 줄씩
runtime/proc.go:824~831 주석 → :832 schedinit
runtime/proc.go:148 main
runtime/proc.go:3377 findRunnable  +  :3136 handoffp  (나란히)
runtime/proc.go:3610~3645 "Delicate dance"  ← ★
runtime/stack.go:899 copystack → :733 getStackMap
runtime/netpoll.go:548 netpollblock
runtime/preempt.go:348~358 주석
```
실습: `GODEBUG=schedtrace=1000,scheddetail=1`로 스케줄러 상태를 실시간 관찰. trace 분석은 `go tool trace`보다 **gotraceui**를 쓸 것.

**7주차 — 축 E**
축 B~D를 한 번 훑은 뒤 §E 표를 들고 각 항목의 세 지점(컴파일러/링커/런타임)을 왕복. 여기서 비로소 "Go는 왜 정확한 GC를 하면서 스택을 옮길 수 있는가"가 하나로 이어진다.
