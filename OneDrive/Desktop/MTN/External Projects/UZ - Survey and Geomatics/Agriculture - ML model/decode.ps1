$path = "c:\Users\MTN\OneDrive\Desktop\MTN\External Projects\UZ - Survey and Geomatics\Agriculture - ML model\gee_app.js"
$outPath = "c:\Users\MTN\OneDrive\Desktop\MTN\External Projects\UZ - Survey and Geomatics\Agriculture - ML model\gee_app_fixed.js"

$corruptedText = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
$ansiEncoding = [System.Text.Encoding]::GetEncoding(1252)
$originalBytes = $ansiEncoding.GetBytes($corruptedText)
$fixedText = [System.Text.Encoding]::UTF8.GetString($originalBytes)

# Also fix the weird "Ã¢â€ â€™" which might just be an arrow "→" and "Ã¢â‚¬â€ " which is "—"
# If there are any stray corruptions due to CP1252 unassigned chars, this next step will ensure they don't break JS

[System.IO.File]::WriteAllText($outPath, $fixedText, [System.Text.Encoding]::UTF8)
Write-Output "Successfully wrote decoded file to gee_app_fixed.js"
