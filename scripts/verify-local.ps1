param(
    [string]$BaseUrl = "http://localhost:8080"
)

$ErrorActionPreference = "Stop"

Write-Host "Comprobando Round Robin en $BaseUrl/health"
$counts = @{}
1..12 | ForEach-Object {
    $response = Invoke-RestMethod -Uri "$BaseUrl/health"
    $backend = $response.backend
    if (-not $counts.ContainsKey($backend)) { $counts[$backend] = 0 }
    $counts[$backend]++
}
$counts.GetEnumerator() | Sort-Object Name | Format-Table Name, Value -AutoSize

if ($counts.Keys.Count -ne 3) {
    throw "Se esperaban respuestas de 3 backends y se obtuvieron $($counts.Keys.Count)."
}

Write-Host "Comprobando LOGIN y CRUD mediante Nginx"
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/login" -Method Post -WebSession $session -Body @{
    username = "admin"
    password = "admin123"
} | Out-Null

$title = "Prueba automatizada $(Get-Date -Format 'yyyyMMdd-HHmmss')"
Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/tasks/new" -Method Post -WebSession $session -Body @{
    title = $title
    description = "Registro creado a traves del balanceador Nginx"
} | Out-Null

$page = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/" -WebSession $session
if ($page.Content -notmatch [regex]::Escape($title)) {
    throw "El registro creado no aparece en el listado del CRUD."
}

$editMatch = [regex]::Match($page.Content, '/tasks/(\d+)/edit')
if (-not $editMatch.Success) {
    throw "No se encontro el enlace de edicion del registro creado."
}
$taskId = $editMatch.Groups[1].Value
$updatedTitle = "$title actualizado"
Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/tasks/$taskId/edit" -Method Post -WebSession $session -Body @{
    title = $updatedTitle
    description = "Registro actualizado a traves del balanceador Nginx"
    completed = "on"
} | Out-Null

$updatedPage = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/" -WebSession $session
if ($updatedPage.Content -notmatch [regex]::Escape($updatedTitle) -or $updatedPage.Content -notmatch "Completada") {
    throw "La actualizacion del registro no se reflejo en el listado."
}

Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/tasks/$taskId/delete" -Method Post -WebSession $session | Out-Null
$finalPage = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/" -WebSession $session
if ($finalPage.Content -match [regex]::Escape($updatedTitle)) {
    throw "El registro de prueba no fue eliminado."
}

Write-Host "OK: login y CRUD completo (crear, leer, actualizar y eliminar) funcionan a traves de Nginx."
