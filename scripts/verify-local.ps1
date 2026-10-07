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
    password = "Admin123!"
} | Out-Null

$stamp = Get-Date -Format 'yyyyMMddHHmmss'
$sku = "QA-$stamp"
$name = "Producto automatizado $stamp"
Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/products/new" -Method Post -WebSession $session -Body @{
    sku = $sku
    name = $name
    brand = "TechStore QA"
    category = "Pruebas"
    stock = "6"
    min_stock = "3"
    price = "99.90"
    description = "Registro creado a traves del balanceador Nginx"
    active = "on"
} | Out-Null

$page = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/" -WebSession $session
if ($page.Content -notmatch [regex]::Escape($sku)) {
    throw "El registro creado no aparece en el listado del CRUD."
}

$rowPattern = '<tr[^>]*data-search="[^"]*' + [regex]::Escape($sku.ToLowerInvariant()) + '[^"]*"[^>]*>.*?</tr>'
$productBlock = [regex]::Match($page.Content, $rowPattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)
$editMatch = [regex]::Match($productBlock.Value, '/products/(\d+)/edit')
if (-not $editMatch.Success) {
    throw "No se encontro el enlace de edicion del registro creado."
}
$productId = $editMatch.Groups[1].Value
$updatedName = "$name actualizado"
Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/products/$productId/edit" -Method Post -WebSession $session -Body @{
    sku = $sku
    name = $updatedName
    brand = "TechStore QA"
    category = "Pruebas"
    stock = "2"
    min_stock = "3"
    price = "109.90"
    description = "Registro actualizado a traves del balanceador Nginx"
    active = "on"
} | Out-Null

$updatedPage = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/" -WebSession $session
if ($updatedPage.Content -notmatch [regex]::Escape($updatedName) -or $updatedPage.Content -notmatch "Stock bajo") {
    throw "La actualizacion del registro no se reflejo en el listado."
}

Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/products/$productId/delete" -Method Post -WebSession $session | Out-Null
$finalPage = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/" -WebSession $session
if ($finalPage.Content -match [regex]::Escape($updatedName)) {
    throw "El registro de prueba no fue eliminado."
}

Write-Host "OK: login y CRUD completo (crear, leer, actualizar y eliminar) funcionan a traves de Nginx."
