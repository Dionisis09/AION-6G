param(
  [string]$ClusterName = "aion-6g-cluster"
)

Write-Host "Deploying Kubernetes manifests"
kubectl apply -f deployments/kubernetes/
