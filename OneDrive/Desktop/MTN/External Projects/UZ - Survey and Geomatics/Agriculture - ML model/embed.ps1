$b64Path = "c:\Users\MTN\OneDrive\Desktop\MTN\External Projects\UZ - Survey and Geomatics\Agriculture - ML model\base64_logo.txt"
$b64 = Get-Content -Raw -Path $b64Path
$b64 = $b64.Trim()

$newLabel = "var title = ui.Label({value: 'Optiflow Aqua Systems', style: {fontWeight: 'bold', fontSize: '20px', margin: '0 0 10px 0'}, imageUrl: 'data:image/jpeg;base64," + $b64 + "'});"

$jsPath = "c:\Users\MTN\OneDrive\Desktop\MTN\External Projects\UZ - Survey and Geomatics\Agriculture - ML model\gee_app.js"
$jsContent = Get-Content -Raw -Path $jsPath

# Regex replace the specific title definition block
$jsContent = $jsContent -replace "var title = ui.Label\('💧 Optiflow Aqua Systems'[\s\S]*?\}\);", $newLabel

[System.IO.File]::WriteAllText($jsPath, $jsContent)
Write-Output "Successfully embedded Base64 image into gee_app.js"
