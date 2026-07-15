param(
  [string]$ClusterName = "aion-6g-cluster"
)

Write-Host "Deleting kind cluster $ClusterName"
kind delete cluster --name $ClusterName
