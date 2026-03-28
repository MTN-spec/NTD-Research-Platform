$path = "c:\Users\MTN\OneDrive\Desktop\MTN\External Projects\UZ - Survey and Geomatics\Agriculture - ML model\gee_app.js"
$content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)

$dict = [ordered]@{
    "Ã¢â€¢Â " = "═";
    "Ã¢â€ â‚¬" = "─";
    "Ã¢â‚¬â€ " = "—";
    "Ã¢â€ â€™" = "→";
    "Ã°Å¸Å’Â¾" = "🌾";
    "Ã°Å¸â€œÅ " = "📊";
    "Ã¢Å“â€¦" = "✅";
    "Ã°Å¸â€œÂ " = "📐";
    "Ã°Å¸â€œË†" = "📈";
    "Ã°Å¸â€œâ€°" = "📉";
    "Ã¢â€žÂ¹Ã¯Â¸Â " = "ℹ️";
    "Ã°Å¸Å’Â§Ã¯Â¸Â " = "🌧️";
    "Ã°Å¸â€™Â§" = "💧";
    "Ã°Å¸Â Å“Ã¯Â¸Â " = "🏜️";
    "Ã°Å¸Å¡Â¿" = "🚿";
    "Ã¢Å¡Â Ã¯Â¸Â " = "⚠️";
    "Ã°Å¸Å¸Â¡" = "🟡";
    "Ã°Å¸Å¸Â¢" = "🟢";
    "Ã°Å¸Å’Â±" = "🌱";
    "Ã°Å¸â€œâ€¦" = "📅";
    "Ã°Å¸â€ Â´" = "🔴";
    "Ã°Å¸Å¡Å“" = "🚜";
    "Ã°Å¸â€“Å’Ã¯Â¸Â " = "🖌️";
    "Ã°Å¸Å½Â¯" = "🎯";
    "Ã°Å¸â€ºâ€˜" = "🛑";
    "Ã°Å¸Å¡â‚¬" = "🚀";
    "Ã°Å¸â€ â€ž" = "🔄";
    "Ã°Å¸”„" = "🔄";
    "Ã°Å¸â€™Â¾" = "💾";
    "Ã°Å¸â€“Â°Ã¯Â¸Â " = "🗺️";
    "Ã°Å¸â€™Â¡" = "💡"
}

foreach ($key in $dict.Keys) {
    if ($content.Contains($key)) {
        $content = $content.Replace($key, $dict[$key])
    }
}

[System.IO.File]::WriteAllText($path, $content, [System.Text.Encoding]::UTF8)
Write-Output "Successfully replaced corrupted strings in gee_app.js"
