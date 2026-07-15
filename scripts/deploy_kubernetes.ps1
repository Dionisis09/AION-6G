param(
  [string]$ClusterName = "aion-6g-cluster"
)

$ErrorActionPreference = "Stop"
if ($ClusterName -ne "aion-6g-cluster") {
  throw "Only the isolated aion-6g-cluster name is allowed"
}
$context = "kind-$ClusterName"
kubectl --context $context get namespace aion-6g 2>$null
if ($LASTEXITCODE -ne 0) {
  kubectl --context $context create namespace aion-6g
}
Write-Host "Deploying AION-6G manifests to $context namespace aion-6g"
kubectl --context $context apply -f deployments/kubernetes/
kubectl --context $context rollout status deployment/aion6g-worker -n aion-6g --timeout=120s
