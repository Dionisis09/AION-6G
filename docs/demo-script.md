# AION-6G — Live Demo Runbook

Τελευταία live επαλήθευση: **22/07/2026**
Περιβάλλον: Docker Desktop, Kubernetes context `docker-desktop`, namespace `aion-6g`

Το runbook προορίζεται για παρουσίαση 7–10 λεπτών. Οι εντολές εκτελούνται από το repository root:

```powershell
cd C:\Users\dioni\Desktop\AION-6G
```

## 1. Τι παρουσιάζουμε

Το AION-6G είναι 6G-oriented Cloud–Edge orchestration testbed. Μετατρέπει natural-language requirements σε validated Service Intent, συγκρίνει local και Kubernetes targets, εκτελεί bounded workloads και επαληθεύει runtime identity, metadata, checksum και SLA.

Δεν είναι πραγματικό 6G radio network, network-slicing platform ή production telecom infrastructure.

## 2. Docker Desktop Kubernetes

Στο Docker Desktop πρέπει να είναι ενεργοποιημένο το Kubernetes από **Settings → Kubernetes**. Το cluster δημιουργείται και διαχειρίζεται από το Docker Desktop· δεν δημιουργείται από script του project.

```powershell
kubectl config current-context
kubectl get nodes -o wide
```

Τι κάνουν:

- `current-context`: εμφανίζει ποιο cluster θα χρησιμοποιήσουν αυτόματα τα scripts.
- `get nodes`: επιβεβαιώνει ότι υπάρχει node σε κατάσταση `Ready`.
- Στη σημερινή workflow το context είναι `docker-desktop`.

Δεν χρησιμοποιούμε hardcoded context. Αν χρειαστεί άλλο cluster, δίνουμε ρητά `-Context`. Η προαιρετική συμβατότητα με kind παραμένει μέσω explicit `-Context` ή `-ClusterName`.

## 3. Build του Kubernetes worker image

```powershell
docker build `
  -f deployments/docker/worker.Dockerfile `
  -t aion6g-worker:validation `
  .
```

Τι κάνει:

- Χτίζει το image του dedicated worker.
- Το tag `aion6g-worker:validation` είναι ακριβώς αυτό που ζητά το Kubernetes Deployment.
- Το manifest χρησιμοποιεί `imagePullPolicy: IfNotPresent`, ώστε το Docker Desktop Kubernetes να χρησιμοποιεί το διαθέσιμο local image.

## 4. Deployment στο ενεργό kubectl context

```powershell
.\scripts\deploy_kubernetes.ps1
```

Τι κάνει το script:

1. Διαβάζει `kubectl config current-context`.
2. Ελέγχει ότι το context υπάρχει.
3. Δημιουργεί το namespace `aion-6g` αν λείπει.
4. Εκτελεί `kubectl apply -f deployments/kubernetes/`.
5. Περιμένει το rollout του `deployment/aion6g-worker`.

## 5. Verification των Kubernetes resources

### Deployment

```powershell
kubectl get deployment/aion6g-worker -n aion-6g
```

Περιμένουμε `READY 1/1` και `AVAILABLE 1`. Το Deployment δηλώνει την επιθυμητή κατάσταση και δημιουργεί/αντικαθιστά Pods μέσω του controller.

### Pod

```powershell
kubectl get pods -n aion-6g -l app=aion6g-worker -o wide
```

Περιμένουμε `1/1 Running` και ιδανικά `0` restarts. Το Pod είναι το πραγματικό runtime instance του worker image.

Για pod identity:

```powershell
$columns = 'NAME:.metadata.name,UID:.metadata.uid,' +
  'READY:.status.containerStatuses[0].ready,' +
  'RESTARTS:.status.containerStatuses[0].restartCount'

kubectl get pods `
  -n aion-6g `
  -o "custom-columns=$columns"
```

Το `pod_uid` είναι σημαντικότερο από το όνομα μόνο του: συνδέει το execution evidence με συγκεκριμένο Pod instance.

### Service

```powershell
kubectl get service/aion6g-worker -n aion-6g
```

Περιμένουμε Service τύπου `ClusterIP` στο port `8001`. Το Service δίνει σταθερό εσωτερικό endpoint προς το Pod χωρίς δημόσιο LoadBalancer.

## 6. Port forwarding

Αν το API/dashboard τρέχει απευθείας στον host:

```powershell
.\scripts\port_forward_kubernetes.ps1
```

Αν το API/dashboard τρέχει μέσα στο Docker Compose:

```powershell
.\scripts\port_forward_kubernetes.ps1 -ForDocker
```

Το terminal παραμένει απασχολημένο όσο λειτουργεί το port-forward. Αυτό είναι φυσιολογικό. Το σταματάμε με `Ctrl+C` μετά το demo.

Η προτιμώμενη θύρα είναι η `8002`. Αν είναι κατειλημμένη και δεν έχει δοθεί `-LocalPort`, το script βρίσκει την επόμενη διαθέσιμη και εμφανίζει:

```text
Worker health URL: http://127.0.0.1:<selected-port>/health
```

Αν οριστεί ρητά κατειλημμένη θύρα, το script αποτυγχάνει καθαρά αντί να αλλάξει σιωπηρά port.

Έλεγχος:

```powershell
curl.exe --silent --show-error --fail `
  http://127.0.0.1:8002/health
```

Αναμενόμενο αποτέλεσμα:

```json
{"status":"ok","execution_mode":"KUBERNETES"}
```

## 7. Εκκίνηση Dashboard

Σε άλλο PowerShell terminal:

```powershell
docker compose -p aion6g up -d --build --remove-orphans
docker compose -p aion6g ps
Start-Process http://127.0.0.1:8000/
```

Τι κάνουν:

- `up -d --build`: χτίζει και ξεκινά το FastAPI dashboard και τον dedicated local worker.
- `--remove-orphans`: αφαιρεί μόνο orphan containers του Compose project `aion6g`.
- `ps`: δείχνει running/healthy state και host ports.
- `Start-Process`: ανοίγει το dashboard στον browser.

## 8. Πώς διαβάζουμε το Dashboard

### Natural-language intent

Ο χρήστης γράφει workload type και αριθμητικά SLA limits. Ο deterministic parser εφαρμόζει profile defaults και δημιουργεί Pydantic-validated `ServiceIntent`.

### Placement policy

- `adaptive`: συγκρίνει όλους τους eligible candidates και επιλέγει το υψηλότερο score.
- `always-local`: αναγκάζει local-edge προσπάθεια για baseline/debugging.
- `always-kubernetes`: αναγκάζει Kubernetes προσπάθεια για pod-evidence validation.

Forced policy δεν σημαίνει forced success. Το verification μπορεί να αποτύχει.

### Candidate comparison

- `eligible`: αν health/readiness και διαθέσιμα thresholds επιτρέπουν τον candidate.
- `score`: 30% latency, 20% CPU, 20% memory, 15% health, 15% readiness.
- `rejection_reasons`: γιατί απορρίφθηκε candidate.
- Nested telemetry: latency, CPU, memory, health, endpoint readiness και metric provenance.

### Execution and verification

- `selected_target`: λογική απόφαση placement.
- `execution_mode`: πραγματική worker identity.
- `pod_uid`: συγκεκριμένο Kubernetes runtime instance.
- `checksum`: deterministic workload content result.
- `verification.status`: αποτέλεσμα ελέγχων identity, metadata, checksum και SLA.
- `fallback`: αν έγινε μία bounded retry και ποια attempts διατηρήθηκαν.

## 9. Προτεινόμενα walkthroughs

### A. adaptive + baseline

```text
Intent: Deploy a critical-control workload with latency below 100 ms and CPU below 70%
Policy: adaptive
Scenario: baseline
```

Το local-edge συνήθως επιλέγεται επειδή έχει μικρότερο measured latency και μεγαλύτερο score. Με Compose περιμένουμε `execution_mode=DOCKER`, `verification=PASSED`, `fallback.used=false`.

### B. always-local

Το candidate list περιορίζεται στο local-edge. Το αποτέλεσμα αποδεικνύει τον local worker path, όχι σύγκριση των δύο targets.

### C. always-kubernetes

```text
Intent: Deploy a massive-iot workload with latency below 100 ms and CPU below 80%
Policy: always-kubernetes
Scenario: baseline
```

Περιμένουμε `KUBERNETES`, namespace, deployment, pod name/UID, container, checksum και `PASSED`.

### D. adaptive + local-high-cpu

Η local CPU γίνεται CONTROLLED 99%. Με max CPU 80%, το local γίνεται ineligible και επιλέγεται Kubernetes χωρίς fallback.

### E. adaptive + kubernetes-high-latency

Προστίθενται EMULATED 35 ms στο Kubernetes HTTP latency. Το local αναμένεται να επιλεγεί αν παραμένει eligible και έχει μεγαλύτερο score.

### F. selected-target-failure

Η επιλεγμένη local προσπάθεια αποτυγχάνει CONTROLLED. Με ενεργό fallback περιμένουμε `used=true`, `retry_count=1`, δύο retained attempts και πραγματική Kubernetes retry.

### G. no-eligible-target

Και οι δύο candidates γίνονται CONTROLLED unhealthy/not-ready. Περιμένουμε `selected_target=null`, `execution_mode=UNAVAILABLE`, `verification=FAILED` και κανένα fabricated execution.

## 10. Current validation commands

```powershell
$env:AION_RUN_DOCKER_TESTS="1"
$env:AION_RUN_KUBERNETES_TESTS="1"
$env:AION_RUN_DOCKER_KUBERNETES_TESTS="1"
py -3.11 -m pytest -q --disable-warnings
```

Live αποτέλεσμα 22/07/2026:

```text
44 passed, 13 warnings
```

Security validation:

```powershell
py -3.11 scripts/run_security_scan.py
```

Live αποτέλεσμα 22/07/2026:

```json
{"status":"VERIFIED","findings":0}
```

Τα 60 experiment runs είναι stored functional snapshot της 18/07/2026: 56 PASSED και 4 retained FAILED. Δεν είναι production benchmark.

## 11. Stop conditions

Σταματάμε το live path και χρησιμοποιούμε τα validated screenshots όταν:

- το context δεν είναι αυτό που περιμένουμε,
- ο node δεν είναι Ready,
- το deployment/pod δεν είναι 1/1,
- το worker health δεν επιστρέφει `KUBERNETES`,
- το dashboard API δεν είναι healthy,
- το port-forward τερματίζεται.

Δεν επαναλαμβάνουμε tests μέχρι να “περάσουν” και δεν μετατρέπουμε `FAILED` ή `UNAVAILABLE` σε success.

## 12. Τερματισμός demo

Στο terminal του port-forward:

```text
Ctrl+C
```

Προαιρετικό cleanup των test variables:

```powershell
Remove-Item Env:AION_RUN_DOCKER_TESTS
Remove-Item Env:AION_RUN_KUBERNETES_TESTS
Remove-Item Env:AION_RUN_DOCKER_KUBERNETES_TESTS
```

Τα Compose services μπορούν να παραμείνουν για επόμενο demo ή να σταματήσουν με:

```powershell
docker compose -p aion6g down
```
