[CmdletBinding()]
param(
  [string]$Context,
  [string]$ClusterName
)

$ErrorActionPreference = "Stop"

if ($Context -and $ClusterName) {
  throw "Specify either -Context or -ClusterName, not both."
}

if (-not [string]::IsNullOrWhiteSpace($Context)) {
  $resolvedContext = $Context.Trim()
} elseif (-not [string]::IsNullOrWhiteSpace($ClusterName)) {
  $resolvedContext = "kind-$($ClusterName.Trim())"
} else {
  $resolvedContext = (& kubectl config current-context 2>$null).Trim()
  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($resolvedContext)) {
    throw "No current kubectl context is configured. Select one with 'kubectl config use-context <name>' or pass -Context explicitly."
  }
}

$contextRecord = kubectl config get-contexts $resolvedContext --no-headers
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($contextRecord)) {
  throw "Kubectl context '$resolvedContext' does not exist."
}

$namespaceResource = kubectl --context $resolvedContext get namespace aion-6g --ignore-not-found -o name
if ($LASTEXITCODE -ne 0) {
  throw "Failed to query namespace aion-6g in context '$resolvedContext'."
}
if ([string]::IsNullOrWhiteSpace($namespaceResource)) {
  kubectl --context $resolvedContext create namespace aion-6g
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to create namespace aion-6g in context '$resolvedContext'."
  }
}

Write-Host "Deploying AION-6G manifests to $resolvedContext namespace aion-6g"
kubectl --context $resolvedContext apply -f deployments/kubernetes/
if ($LASTEXITCODE -ne 0) {
  throw "Failed to apply AION-6G manifests in context '$resolvedContext'."
}

kubectl --context $resolvedContext rollout status deployment/aion6g-worker -n aion-6g --timeout=120s
if ($LASTEXITCODE -ne 0) {
  throw "AION-6G worker rollout failed in context '$resolvedContext'."
}
