param(
  [Parameter(Position=0)]
  [ValidateSet("up", "down", "logs", "ps")]
  [string]$cmd = "up"
)

$RepoRoot   = $PSScriptRoot
$ComposeFile = Join-Path $RepoRoot "infra/docker-compose.yml"
$EnvFile     = Join-Path $RepoRoot ".env"

# -------------------------
# Helpers
# -------------------------

function Test-EnvFile {
  if (-not (Test-Path $EnvFile)) {
    Write-Host "ERROR: .env not found." -ForegroundColor Red
    Write-Host "Copy .env.example -> .env and edit required values." -ForegroundColor Yellow
    exit 1
  }
}

function Import-EnvFile {
  Get-Content $EnvFile |
    Where-Object { $_ -match "=" -and $_ -notmatch "^\s*#" } |
    ForEach-Object {
      $pair  = $_ -split "=", 2
      $name  = $pair[0].Trim()
      $value = $pair[1].Trim()

      # Strip quotes if present
      if ($value.Length -ge 2) {
        if (
          ($value.StartsWith('"') -and $value.EndsWith('"')) -or
          ($value.StartsWith("'") -and $value.EndsWith("'"))
        ) {
          $value = $value.Substring(1, $value.Length - 2)
        }
      }

      Set-Item -Path "env:$name" -Value $value
    }
}

function Test-HealthUrl {
  param(
    [Parameter(Mandatory=$true)]
    [string]$Url
  )
  try {
    $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
    return ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300)
  } catch {
    return $false
  }
}

function Get-ContainerHealth {
  param(
    [Parameter(Mandatory=$true)]
    [string]$Name
  )
  try {
    $status = docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' $Name 2>$null
    return $status.Trim()
  } catch {
    return "none"
  }
}

function Wait-ForHealth {
  param(
    [int]$TimeoutSec  = 120,
    [int]$IntervalSec = 2
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSec)

  while ((Get-Date) -lt $deadline) {

    $backendOk  = (Test-HealthUrl -Url "http://127.0.0.1:8810/health")
    $frontendOk = (Test-HealthUrl -Url "http://127.0.0.1:3000/api/health")

    $frontendHealth = (Get-ContainerHealth -Name "travelai-frontend")

    if ($backendOk -and $frontendOk -and ($frontendHealth -eq "healthy")) {
      return $true
    }

    Start-Sleep -Seconds $IntervalSec
  }

  return $false
}

# -------------------------
# Commands
# -------------------------

switch ($cmd) {

  "up" {
    Test-EnvFile
    Import-EnvFile

    Write-Host "> Starting TravelAI (docker compose up --build)..." -ForegroundColor Cyan
    docker compose --env-file $EnvFile -f $ComposeFile up --build -d

    Write-Host "Waiting for healthchecks..." -ForegroundColor Cyan
    if (-not (Wait-ForHealth)) {
      Write-Host "ERROR: Timed out waiting for healthchecks." -ForegroundColor Red
      docker compose --env-file $EnvFile -f $ComposeFile ps
      Write-Host "Hint: docker compose --env-file `"$EnvFile`" -f `"$ComposeFile`" logs --tail=200 backend frontend" -ForegroundColor Yellow
      exit 1
    }

    Write-Host ""
    Write-Host "> Containers status:" -ForegroundColor Cyan
    docker compose --env-file $EnvFile -f $ComposeFile ps

    $frontendPort = if ($env:FRONTEND_PORT) { $env:FRONTEND_PORT } else { "3000" }
    $backendPort  = if ($env:BACKEND_PORT)  { $env:BACKEND_PORT }  else { "8810" }

    Write-Host ""
    Write-Host "Frontend: http://localhost:$frontendPort" -ForegroundColor Green
    Write-Host "Backend:  http://localhost:$backendPort"  -ForegroundColor Green
    Write-Host "Health:   http://localhost:$backendPort/health" -ForegroundColor Green
  }

  "down" {
    Write-Host "> Stopping containers..." -ForegroundColor Yellow
    docker compose --env-file $EnvFile -f $ComposeFile down -v
  }

  "logs" {
    docker compose --env-file $EnvFile -f $ComposeFile logs -f --tail=200
  }

  "ps" {
    docker compose --env-file $EnvFile -f $ComposeFile ps
  }
}
