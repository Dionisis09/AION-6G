[CmdletBinding()]
param(
  [switch]$ForDocker,
  [ValidateRange(1024, 65535)]
  [int]$LocalPort = 8002,
  [string]$Context,
  [string]$ClusterName
)

$ErrorActionPreference = "Stop"
$localPortWasExplicit = $PSBoundParameters.ContainsKey("LocalPort")

function Test-LocalPortAvailable {
  param(
    [Parameter(Mandatory)]
    [string]$ListenAddress,
    [Parameter(Mandatory)]
    [int]$Port
  )

  $listener = $null
  try {
    $listener = [System.Net.Sockets.TcpListener]::new(
      [System.Net.IPAddress]::Parse($ListenAddress),
      $Port
    )
    $listener.Server.ExclusiveAddressUse = $true
    $listener.Start()
    return $true
  } catch [System.Net.Sockets.SocketException] {
    return $false
  } finally {
    if ($null -ne $listener) {
      $listener.Stop()
    }
  }
}

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

$namespace = "aion-6g"
$service = "aion6g-worker"
$address = if ($ForDocker) { "0.0.0.0" } else { "127.0.0.1" }

if (-not (Test-LocalPortAvailable -ListenAddress $address -Port $LocalPort)) {
  if ($localPortWasExplicit) {
    throw "Local port $LocalPort is already in use on $address. Stop the process using it or choose another port with -LocalPort <port>."
  }

  $preferredPort = $LocalPort
  do {
    $LocalPort++
    if ($LocalPort -gt 65535) {
      throw "No available local port was found after preferred port $preferredPort."
    }
  } while (-not (Test-LocalPortAvailable -ListenAddress $address -Port $LocalPort))

  Write-Warning "Preferred port $preferredPort is already in use. Using available port $LocalPort instead."
}

$contextRecord = kubectl config get-contexts $resolvedContext --no-headers
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($contextRecord)) {
  throw "Kubectl context '$resolvedContext' does not exist."
}

kubectl --context $resolvedContext get deployment/aion6g-worker -n $namespace | Out-Null
if ($LASTEXITCODE -ne 0) {
  throw "The AION-6G deployment is not available in $resolvedContext/$namespace"
}

if ($ForDocker) {
  Write-Warning "Docker access requires a host-reachable listener. Port $LocalPort will listen on all host interfaces until this process stops. Use only on a trusted development machine."
  if ($LocalPort -ne 8002) {
    Write-Warning "For Docker-to-Kubernetes validation, set KUBERNETES_WORKER_URL=http://host.docker.internal:$LocalPort so the API uses the selected port."
  }
}

Write-Host "Forwarding $address`:$LocalPort to service/$service`:8001 in $resolvedContext/$namespace"
Write-Host "Worker health URL: http://127.0.0.1:$LocalPort/health"
kubectl --context $resolvedContext port-forward --address=$address -n $namespace service/$service "${LocalPort}:8001"
