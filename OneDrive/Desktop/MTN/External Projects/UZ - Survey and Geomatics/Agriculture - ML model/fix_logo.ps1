$b64Path = "c:\Users\MTN\OneDrive\Desktop\MTN\External Projects\UZ - Survey and Geomatics\Agriculture - ML model\base64_logo.txt"
$b64 = Get-Content -Raw -Path $b64Path
$b64 = $b64.Trim()

$newHeader = @"
// Title Panel
var titleLabel = ui.Label('Optiflow Aqua Systems', {
    fontWeight: 'bold', fontSize: '18px', margin: '20px 0 10px 0', color: '#0066cc'
});
var titlePanel = ui.Panel({
    widgets: [titleLabel],
    layout: ui.Panel.Layout.Flow('horizontal'),
    style: {margin: '0 0 10px 0'}
});
var subtitle = ui.Label('Select a crop, date, and run analysis on Sentinel-2 imagery.', {
    fontSize: '13px', color: '#555'
});
mainPanel.add(titlePanel);
mainPanel.add(subtitle);
"@

$jsPath = "c:\Users\MTN\OneDrive\Desktop\MTN\External Projects\UZ - Survey and Geomatics\Agriculture - ML model\gee_app.js"
$jsContent = Get-Content -Raw -Path $jsPath

# Regex to match from "// Title" up to "mainPanel.add(subtitle);"
$jsContent = $jsContent -replace "// Title[\s\S]*?mainPanel\.add\(subtitle\);", $newHeader

[System.IO.File]::WriteAllText($jsPath, $jsContent)
Write-Output "Successfully updated layout in gee_app.js"
