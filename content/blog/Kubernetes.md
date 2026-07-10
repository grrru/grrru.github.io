---
date: 2026-07-10
draft: true
title: Kubernetes
categories: infra
tags:
  - k8s
  - infra
author: grrru
---

# Kubernetes(k8s)

구글이 개발한 오픈 소스 기반의 컨테이너 오케스트레이션 플랫폼.
컨테이너형 애플리케이션의 배포, 확장, 관리, 장애 복구(Self-healing)를 자동화하여 운영 효율성을 높여준다.

## 0. 전제 조건

- [Kind](https://kind.sigs.k8s.io/) 설치
- [kubectl](https://kubernetes.io/docs/tasks/tools/) 설치

여기서는 [Rancher Desktop](https://rancherdesktop.io/)으로 kubectl을 설치했다.

## 1. Cluster

CLuster는 k8s에서 가장 큰 단위이다.

A Kubernetes cluster consists of a control plane plus a set of worker machines, called nodes, that run containerized applications. Every cluster needs at least one worker node in order to run Pods.

The worker node(s) host the Pods that are the components of the application workload. The control plane manages the worker nodes and the Pods in the cluster. In production environments, the control plane usually runs across multiple computers and a cluster usually runs multiple nodes, providing fault-tolerance and high availability.

### Cluster 생성 (feat. Kind)

[Kind](https://kind.sigs.k8s.io/)는 **K**8s in **D**ocker라는 도구인데, 실제 서버 없이도 k8s를 실습해보기 좋아서 사용했다.

kind is a tool for running local Kubernetes clusters using Docker container “nodes”.
kind was primarily designed for testing Kubernetes itself, but may be used for local development or CI.

하나의 Control Plane Node와 두 개의 Worker Node를 가지는 Multi-node 클러스터 생성한다.

#### `kind-config.yaml`

```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
```

#### create cluster

```bash
kind delete cluster --name k8s-study
kind create cluster --name k8s-study --config 01-basics/kind-config.yaml
```

위와 같이 생성하면 Node들이 Docker Container로 띄워진다.  물리 머신/VM 없이도 Node들을 Docker Container로 띄워볼 수 있다.

```bash
> kubectl get nodes

NAME                      STATUS   ROLES           AGE   VERSION
k8s-study-control-plane   Ready    control-plane   84m   v1.35.0
k8s-study-worker          Ready    <none>          84m   v1.35.0
k8s-study-worker2         Ready    <none>          84m   v1.35.0
```

## 2. Node

Node는 결국 물리적인 머신(서버) 또는 VM(virtual machine)이다.

Kubernetes runs your workload by placing containers into Pods to run on Nodes. A node may be a virtual or physical machine, depending on the cluster. Each node is managed by the control plane and contains the services necessary to run Pods.

Typically you have several nodes in a cluster; in a learning or resource-limited environment, you might have only one node.

The components on a node include the kubelet, a container runtime, and the kube-proxy.

## 3. Pod

Pods are the smallest deployable units of computing that you can create and manage in Kubernetes.

A Pod (as in a pod of whales or pea pod) is a group of one or more containers, with shared storage and network resources, and a specification for how to run the containers. A Pod's contents are always co-located and co-scheduled, and run in a shared context. A Pod models an application-specific "logical host": it contains one or more application containers which are relatively tightly coupled. In non-cloud contexts, applications executed on the same physical or virtual machine are analogous to cloud applications executed on the same logical host.

As well as application containers, a Pod can contain init containers that run during Pod startup. You can also inject ephemeral containers for debugging a running Pod.

### Pod 직접 실행하기

Pod은 Node 내에서 하나 이상의 Container를 실행하는 집합이기 때문에 실행할 이미지가 필요하다. nginx image를 이용해서 아까 실행해놓은 worker node에 nginx pod을 띄워본다.

#### `nginx-pod.yaml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
    - name: nginx
      image: nginx:1.14.2
      ports:
        - containerPort: 80
```

각 field의 의미

- apiVersion: 이 resource가 사용할 k8s API version
- kind: 정의할 resource type (e.g. Pod, DaemonSet, Deployment, Service)
- metadata.name: resource 식별자. `kubectl get pods nginx` 등에 사용된다.
- spec: 이 resource에 들어갈 스펙을 정의한다. kind에 따라 들어가는 필드가 다르다.
  - pod은 하나 이상의 container를 포함하기 때문에 `containers` 내에 (-) 배열로 사용할 container를 나열한다.

#### pod 생성/삭제

```bash
kubectl apply -f 01-basics/nginx-pod.yaml
kubectl get pod nginx
kubectl describe pod nginx
kubectl logs nginx
kubectl delete pod nginx
```

## 4. [Workload Management](https://kubernetes.io/docs/concepts/workloads/)

A workload is an application running on Kubernetes. Whether your workload is a single component or several that work together, on Kubernetes you run it inside a set of pods. In Kubernetes, a Pod represents a set of one or more running containers on your cluster.

### DaemonSet

DaemonSet은 특정 기능을 모든(혹은 선택된) Node에 보장하기 위해, Node마다 Pod을 한 개씩 자동 배치하고 유지하는 Workload 관리 방식이다.

A DaemonSet defines Pods that provide node-local facilities. These might be fundamental to the operation of your cluster, such as a networking helper tool, or be part of an add-on.
A DaemonSet ensures that all (or some) Nodes run a copy of a Pod. As nodes are added to the cluster, Pods are added to them. As nodes are removed from the cluster, those Pods are garbage collected. Deleting a DaemonSet will clean up the Pods it created.

Some typical uses of a DaemonSet are:

- running a cluster storage daemon on every node
- running a logs collection daemon on every node
- running a node monitoring daemon on every node

In a simple case, one DaemonSet, covering all nodes, would be used for each type of daemon. A more complex setup might use multiple DaemonSets for a single type of daemon, but with different flags and/or different memory and cpu requests for different hardware types.

#### DaemonSet 생성

##### `nginx-daemonset.yaml` 작성

yaml 파일로 daemonset을 정의한다.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: nginx
spec:
  selector:
    matchLabels:
      name: nginx-pod
  template: 
    metadata:
      labels:
        name: nginx-pod
    spec:
      containers:
        - name: nginx-container
          image: nginx:1.14.2
```

- apiVersion: DaemonSet은 `apps` 그룹에 속하기 때문에 `apps/v1`으로 쓴다.
- kind: DaemonSet resource를 생성한다고 명시
- metadata.name: pod과 마찬가지로 DaemonSet을 구별하는 이름이다. metadata.name이 `nginx`이므로 DaemonSet으로 생성되는 Pod의 이름은 `nginx-{random hash}` 형태로 자동 생성된다.
- spec.selector: DaemonSet이 어떤 Pod을 관리할지 지정하는 selector. pod의 name과 label은 별개이며, `nginx-pod`이라는 label이 달린 Pod을 관리한다.
- spec.template: DaemonSet이 생성할 Pod의 템플릿. Pod을 생성할 때 작성하는 yaml의 spec과 동일한 구조다. 내부의 metadata.labels이 selector.matchLabels와 일치해야 한다.

> matchLables, labels에 들어가는 라벨은 key-value 형태로 작성한다. 위에서 작성한 name도 관례적으로 쓰는 key일 뿐이지 `app`, `whatever` 등 원하는 대로 key를 붙일 수 있다.

#### DaemonSet apply

```bash
kubectl apply -f ./02-workloads/nginx-daemonset.yaml
```

DaemonSet을 적용하면 아래와 같이 worker node에 pod이 하나씩 배치되는 걸 볼 수 있다.

```bash
kubectl get pods -o wide

NAME          READY   STATUS    RESTARTS   AGE   IP           NODE                NOMINATED NODE   READINESS GATES
nginx-9nsjv   1/1     Running   0          39s   10.244.2.3   k8s-study-worker2   <none>           <none>
nginx-rjbk7   1/1     Running   0          39s   10.244.1.3   k8s-study-worker    <none>           <none>
```

```bash
kubectl get daemonsets -o wide
NAME    DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE    CONTAINERS        IMAGES         SELECTOR
nginx   2         2         2       2            2           <none>          2m2s   nginx-container   nginx:1.14.2   name=nginx-pod
```

#### DaemonSet delete

DaemonSet을 삭제하면 DaemonSet에 의해 생성된 pod들도 종료된다.

```bash
kubectl delete daemonsets nginx
```

#### DaemonSet nodeSelector

모든 k8s resource에는 label을 붙일 수 있다. DaemonSet은 기본적으로는 모든 Node에 Pod을 올리지만 nodeSelector라는 spec을 추가하면 일치하는 label이 있는 Node에만 Pod을 배치할 수 있다.

##### 1. Node에 label 생성

```bash
kubectl label node k8s-study-worker role=only-worker-1
kubectl get node k8s-study-worker --show-labels
```

LABELS 필드에 `role=only-worker-1`이 생성된 걸 볼 수 있다.

##### 2. yaml에 nodeSelector 필드 작성

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: nginx
spec:
  selector:
    matchLabels:
      name: nginx-pod
  template:
    metadata:
      labels:
        name: nginx-pod
    spec:
      nodeSelector:
        role: only-worker-1
      containers:
        - name: nginx-container
          image: nginx:1.14.2
```

##### 3. daemonset apply

```bash
kubectl apply -f 02-workloads/nginx-daemonset.yaml
```

아까와 다르게 일치하는 label이 있는 `k8s-study-worker` Node에만 Pod이 생성됐다.

```bash
kubectl get pods -o wide
NAME          READY   STATUS    RESTARTS   AGE   IP           NODE               NOMINATED NODE   READINESS GATES
nginx-2qv99   1/1     Running   0          99s   10.244.1.4   k8s-study-worker   <none>           <none>
```

> label  제거는 `key-` 형태를 뒤에 붙이면 된다.
> `kubectl label node k8s-study-worker role-`

#### RollingUpdate

Pod을 순차적으로 교체하는 update strategy.
`maxUnavailabe` 필드로 한 번에 몇 개의 pod을 동시에 업데이트할 수 있는지를 정해두어 무중단 배포가 가능하다.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: nginx
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
  selector:
    matchLabels:
      name: nginx-pod
  template:
    metadata:
      labels:
        name: nginx-pod
    spec:
      containers:
        - name: nginx-container
          image: nginx:alpine
```

pod에 변경이 있어야 재실행하기 때문에 `nginx:alpine`으로 이미지를 변경했다.

yaml 파일을 수정한 뒤 `kubectl apply -f`를 다시 실행해야 k8s가 변경사항을 인지하고 RollingUpdate를 시작한다.

`rollout`은 배포 상태를 확인하고 관리하는 command다. `rollout status`로 배포 진행 상태를 확인할 수 있다.

```bash
kubectl rollout status daemonset/nginx

Waiting for daemon set "nginx" rollout to finish: 0 of 2 updated pods are available...
Waiting for daemon set "nginx" rollout to finish: 1 of 2 updated pods are available...
```

DaemonSet에 의해 배포된 pod이 두 개인데, 하나씩 업데이트되는 걸 볼 수 있다.

### Deployment

Deployment는 원하는 수의 Pod을 유지하는 Workload 관리 방식이다.

DaemonSet과 구조가 거의 동일하지만 `replicas` 필드를 설정한다는 차이가 있다. `replicas`를 설정하여 몇 개의 Pod을 유지할지 지정한다.

#### `nginx-deployment.yaml`

```yaml
# https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    type: RollingUpdate
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:1.14.2
```

`replicas: 3`을 설정하여 3 개의 Pod을 생성한다.
worker node가 2개이므로 node 1개에 두 개의 pod이 배포됐다.

```bash
kubetl apply -f ./02-workloads/nginx-deployment.yaml
kubectl get pods -o wide

NAME                                READY   STATUS    RESTARTS   AGE   IP           NODE                NOMINATED NODE   READINESS GATES
nginx-deployment-667d796f77-9b7xc   1/1     Running   0          11m   10.244.1.8   k8s-study-worker    <none>           <none>
nginx-deployment-667d796f77-g5gll   1/1     Running   0          11m   10.244.2.7   k8s-study-worker2   <none>           <none>
nginx-deployment-667d796f77-npkxk   1/1     Running   0          11m   10.244.1.9   k8s-study-worker    <none>           <none>
```

Deployment가 자동으로 생성한 ReplicaSet을 확인할 수 있다.

```bash
kubectl get replicaset
NAME                          DESIRED   CURRENT   READY   AGE
nginx-deployment-667d796f77   3         3         3       12m
```

#### Controller Manager

Deployment는 replicaset의 pod의 현재 상태를 감시하다가 어떤 pod이 죽으면 자동으로 재생성하는 기능이 있다.

임의로 pod 하나를 delete하고 다른 이름의 pod이 다시 켜지는지 확인한다.

```bash
kubectl delete pod nginx-deployment-667d796f77-g5gll
```

## 5. Service

Service는 Pod에 접근하는 방법을 정의하는 resource다.
Pod은 죽었다가 살아나면 IP가 바뀌기 때문에 Pod IP로 직접 통신할 수 없다. 대신 앞에 Service를 둬서 접근점을 만든다.

Service는 프로세스로 뜨는 건 아니고, 트래픽 규칙을 정의하는 설정이다. 

`kubectl apply`로 Service를 적용하면 control-plane Node의 kube-api-server가 etcd에 저장하고,  
각 worker node의 kube-proxy가 변경을 감지하여 자신이 속한 Node의 iptables 규칙을 업데이트한다.  
실제 트래픽은 각각의 Node로 전달되고 Node에 설정된 iptables 규칙에 따라 '실제 요청을 처리할 Node의 Pod'으로 전달한다.

Service type에는 4가지가 있다.

| Type         | 접근 범위    | 설명                                                       |
|--------------|--------------|------------------------------------------------------------|
| ClusterIP    | Cluster 내부 | default type. 내부 Pod끼리 통신할 때 사용한다.             |
| NodePort     | 외부         | Node IP + Port로 외부 접근 가능(30000 ~ 32767)             |
| LoadBalancer | 외부         | 클라우드(AWS 등)가 외부 IP를 자동 할당한다.                |
| ExternalName | 외부 DNS     | Cluster 내부에서 외부 DNS를 k8s Service 이름으로 매핑한다. |


### ClusterIP type Service 생성

`spec.type`에 Service Type을 작성한다. default값은 ClusterIP이다.

> `---`으로 구분하면 한 파일에 여러 resource를 정의할 수 있다.

```yaml
# nginx-clusterip.yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-clusterip
spec:
  type: ClusterIP
  selector:
    app: nginx
  ports:
    - port: 80
      targetPort: 80

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:alpine
```

작성한 yaml 파일을 적용한다.

```bash
kubectl apply -f nginx-clusterip.yaml
```

생성된 service와 pod을 확인한다.
```bash
kubectl get service
kubectl get pods
```

위 파일로 생성된 service는 다음과 같은 역할을 한다.

- Cluster 내에서 `nginx-clusterip:80`으로 들어오는 패킷을 연결된(selector) pods의 80번 포트로 라우팅한다.
- pod이 여러 개면 라운드로빈 방식으로 로드밸런싱한다.
- pod이 죽더라도 새로 뜬 Pod으로 Endpoints가 업데이트되어 항상 살아있는 Pod으로만 트래픽을 보낸다.

ClusterIP Service는 Cluster 외부에서는 접근할 수 없다. 

따라서 service 요청이 제대로 pod으로 전달되는지 확인하기 위해 curl을 실행할 임시 pod을 만들어서 `nginx-clusterip:80`으로 요청을 보낸다.

```bash
kubectl run curl --image=curlimages/curl --rm -it --restart=Never -- curl nginx-clusterip:80
```
nginx 응답이 오면 성공이다.

### NodePort Type Service 생성

NodePort는 Cluster 외부에서도 NodeIP:NodePort로 접근 가능하게 하는 Service다.

```yaml
# nginx-nodeport.yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-nodeport
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30080
```

`ports`에 작성하는 port에는 `port`, `targetPort`, `nodePort`가 있다.

```text
외부 -> NodeIP:30080 (nodePort) -> Service:80 (port) -> Pod:80 (targetPort)
```

Cluster 외부에서 접근하려면 Node IP와 nodePort를 이용해서 접근해야 한다. Service, Pod에 직접 접근은 불가능하다.

nodePort를 지정하지 않으면 30000 ~ 32767 범위 내에서 랜덤 할당된다.

```bash
kubetl apply -f nginx-nodeport.yaml
```
kind로 띄운 cluster여서 로컬 머신에서 바로 node ip로는 접근이 어렵다.(Node도 실습 환경에선 docker container이므로)

따라서 docker container(worker node)에 접속해서 localhost로 테스트한다.

```bash
docker exec -it k8s-study-worker curl localhost:30080
```

## 6. Storage

Ways to provide both long-term and temporary storage to Pods in your cluster.

### ConfigMap

ConfigMap은 설정값을 Pod과 분리해서 관리하는 resource다. 코드에 하드코딩하거나 이미지에 포함하지 않고, 배포 시점에 주입할 수 있다.

Pod에 config를 주입하는 방법은 두 가지다.
1. 환경변수로 주입
2. 파일(Volume)로 주입

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: myconfig
  namespace: default
data:
  APP_ENV: production
  APP_PORT: "8080"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myjob
  namespace: default
  labels:
    app: myjob
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:alpine
          envFrom:
            - configMapRef:
                name: myconfig
```

`configMapRef`를 통해 ConfigMap을 주입한다.

```bash
kubectl apply -f nginx-configmap.yaml

kubectl exec -it myjob-8644994457-9cxwk -- env
```




## Reference

- <https://kubernetes.io/docs/home/>
- <https://kind.sigs.k8s.io/>
