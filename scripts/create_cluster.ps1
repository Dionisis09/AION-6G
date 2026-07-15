param(
  [string]$ClusterName = "aion-6g-cluster"
)

$ErrorActionPreference = "Stop"
if ($ClusterName -ne "aion-6g-cluster") {
  throw "Only the isolated aion-6g-cluster name is allowed"
}
$existing = kind get clusters
if ($existing -contains $ClusterName) {
  Write-Host "Reusing existing kind cluster $ClusterName"
} else {
  Write-Host "Creating isolated kind cluster $ClusterName"
  kind create cluster --name $ClusterName
}
