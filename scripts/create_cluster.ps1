param(
  [string]$ClusterName = "aion-6g-cluster"
)

Write-Host "Creating kind cluster $ClusterName"
kind create cluster --name $ClusterName
