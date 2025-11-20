---
title: Flight Recorder in Go 1.25
date: "2025-10-21T12:59:00+09:00"
categories:
  - golang
tags:
  - monitering
pin: false
---

# More powerful Go execution traces (2024)
>[more powerful Go execution traces](https://go.dev/blog/execution-traces-2024)
## Issues
 `runtime/trace` 패키지는 goroutine의 실행 흐름을 시간 순으로 기록해서 trace를 생성하고 이를 `go tool trace command`로 시각화할 수 있게 도와주는 패키지다. 하지만 기존에 제공하던 `runtime/trace` 패키지에는 excution traces 생성하는 데 네 가지 큰 문제가 있었다.
- trace는 오버헤드가 크다
- trace는 확장성이 좋지 않아 분석하기에 너무 커질 수 있다
- 특정 문제를 포착하기 위해 언제 tracing을 시작해야할지 불분명하다
- trace를 파싱하고 해석하는 public package의 부족으로 일부 모험적인 개발자만이 사용 가능하다

## 개선 사항
### Low-overhead tracing
 [Felix’s great blog post](https://blog.felixge.de/reducing-gos-execution-tracer-overhead-with-frame-pointer-unwinding/)  
 Go 1.21 이전에는 전체 앱 CPU 사용률의 10\~20%를 차지하던 tracing의 런타임 오버헤드가 1\~2% 수준으로 크게 줄어들었다. tracing 비용의 대부분이 traceback에 있었고, traceback을 최적화하여 CPU 오버헤드를 크게 줄였다.

### Scalable traces
 기존 trace 포맷은 출력 자체는 효율적으로 설계되었지만, 전체 trace를 한번에 메모리에 올려야만 분석 도구로 시각화할 수 있다는 한계가 있었다.
  이를 개선하기 위해 trace를 주기적으로 분할하여 생성하는 방식이 도입되었다. 이 방식은 trace 생성 시의 런타임 오버헤드를 줄이고, `go tool trace`로 특정 구간만 분석하는 것을 가능하게 하며 Flight Recording이라는 새로운 기능의 기반이 되었다.

### Flight recording
웹서비스처럼 오랜 시간 지속되는 프로그램에서는, 느린 요청 등의 정확한 문제 발생 시점을 미리 알 수 없어 언제 tracing을 시작해야 할지 판단하기 어렵다.
기존에는 tracing을 쪼갤 수 없었기 때문에 이런 상황을 추적하는 것이 불가능했지만, 런타임 오버헤드가 낮아지고, 필요할 때 trace를 분할할 수 있는 구조가 되면서 Flight Recording 기능을 구현할 수 있게 되었다.

### Trace reader API
`go tool trace`를 이용하지 않고 reader API를 이용해서 프로그래밍적으로 trace에 접근할 수 있도록 하는 API로, 아직 개발 중이다.

# Flight Recorder in Go 1.25
Go 1.25부터 flight recording 기능을 사용할 수 있게 된다.

## Execution traces
 Go 런타임은 Go 애플리케이션 실행 중 발생하는 이벤트를 기록하는 로그, 즉 Execution trace를 작성할 수 있다. Execution trace에는 고루틴들이 서로 어떻게 상호작용하는지에 대한 정보가 담겨있어 디버깅에 유용하다.
 `runtime/trace` 패키지의 `runtime/trace.Start`, `runtime/trace.Stop`를 호출하여 주어진 시간동안 trace를 수집하는 API를 제공했지만, 이는 tracing하려는 코드가 테스트, 마이크로벤치마크 등인 경우에 적합했다. 웹서비스는 장기간 가동되며 전체 트레이스를 수집하기엔 너무 데이터가 커져 분석하기 어렵다. 또한 요청 시간 초과 등의 문제가 발생했을 때는 이미 `Start`를 호출하기에 늦은 시점이다.

## Flight recording
flight recorder는 trace를 수집하며 소켓이나 파일에 쓰는 대신 trace의 마지막 몇 초를 메모리에 버퍼링한다. 프로그램은 언제든지 버퍼의 내용을 요청해 문제 발생 시점의 정확한 스냅샷을 찍을 수 있다.

### FlightRecorder 생성
```go
func main() {
	config := trace.FlightRecorderConfig{
		MinAge:   5 * time.Second,
		MaxBytes: 3 << 20,
	}
	fr := trace.NewFlightRecorder(config)
	if err := fr.Start(); err != nil {
		log.Fatalf("unable to start trace flight recorder: %v", err)
	}
	defer fr.Stop()

	http.HandleFunc("/", testHandler(fr))
	log.Fatal(http.ListenAndServe(":8080", nil))
}
```
- FlightRecorderConfig
	- MinAge : 트레이스 이벤트를 최소 5초동안 유지하도록 한다
	- MaxBytes : 최대 버퍼 크기를 3MB로 정의한다
	- 이 필드들은 런타임에 대한 권장 사항일 뿐이며, 지정된 시간과 크기를 정확히 따르진 않는다
	- MaxBytes는 MinAge보다 더 높은 우선순위를 가진다
- `Start()` 함수로 레코더를 시작하며 `defer fr.Stop()`으로 애플리케이션 종료 시 레코더를 반드시 중지시킨다
### 테스트 함수
```go
func heavyLoad(wg *sync.WaitGroup, iterations int) {
	defer wg.Done()
	for i := range iterations {
		_ = fmt.Sprintf("processing %d", i)
	}
	time.Sleep(500 * time.Millisecond)
}
```

### 테스트 핸들러
```go
func testHandler(fr *trace.FlightRecorder) http.HandlerFunc {
	var traceWritten sync.Once
	return func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		var wg sync.WaitGroup
		wg.Add(2)

		go heavyLoad(&wg, 100_000)
		go heavyLoad(&wg, 10_000_000)

		wg.Wait()

		diff := time.Since(start)
		if diff > 300*time.Millisecond {
			traceWritten.Do(func() {
				if err := writeTrace(fr); err != nil {
					log.Printf("failed to write to trace: %v", err)
					return
				}
			})
		}

		fmt.Fprintf(w, "worked for %f seconds", diff.Seconds())
	}
}
```

### writeTrace
```go
func writeTrace(fr *trace.FlightRecorder) error {
	if !fr.Enabled() {
		return fmt.Errorf("flight recorder is not enabled")
	}

	file, err := os.Create("trace.out")
	if err != nil {
		return fmt.Errorf("failed to creat trace file: %w", err)
	}
	defer file.Close()

	_, err = fr.WriteTo(file)
	return err
}
```

- `WriteTo`는 한 번에 하나씩만 실행될 수 있다
- trace는 `trace.out`에 저장되며 `go tool trace trace.out` 명령어를 실행하여 트레이스 뷰어를 연다


## Go trace event viewer
### Goroutine Analysis
- 트레이스에 저장된 고루틴들을 확인할 수 있으며 각 고루틴의 총 실행시간, 횟수 등을 볼 수 있다
![image1](https://github.com/user-attachments/assets/38e701ba-da64-4f09-8dbf-27a5a7ecdf4e)


### View trace by proc
- 논리 프로세서 별로 어떤 고루틴이 실행되었는지 시각화한다
![image2](https://github.com/user-attachments/assets/52ab3ea6-0a8c-46ca-89f9-e2a9e07e6ee9)

- 숫자 `2`를 누르면 좌우로 움직이는 마우스 포인터가 되고, 숫자 `3`을 누르면 확대/축소가 가능하다
- 상단 Flow events를 누르면 고루틴들이 연결된 선을 확인할 수 있다

## 출처
[Flight Recorder in Go 1.25 - The Go Programming Language](https://go.dev/blog/flight-recorder)  
[More powerful Go execution traces - The Go Programming Language](https://go.dev/blog/execution-traces-2024)  
[Reducing Go Execution Tracer Overhead With Frame Pointer Unwinding](https://blog.felixge.de/reducing-gos-execution-tracer-overhead-with-frame-pointer-unwinding/)  
[Go 1.25의 새로운 Trace Flight Recorder가 정말 멋지네요! - YouTube](https://www.youtube.com/watch?v=mQM2DQ9yZ5I)  