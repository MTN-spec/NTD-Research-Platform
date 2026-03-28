$path = "c:\Users\MTN\OneDrive\Desktop\MTN\External Projects\UZ - Survey and Geomatics\Agriculture - ML model\gee_app_fixed.js"
$content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)

$dict = [ordered]@{
    "â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• â• " = "═══════════════════════════════════════";
    "â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€" = "───────────────────────────────────────";
    "ðŸŒ¾" = "🌾";
    "â€”" = "—";
    "ðŸ“Š" = "📊";
    "âœ…" = "✅";
    "ðŸ“ " = "📐";
    "ðŸ“ˆ" = "📈";
    "ðŸ“‰" = "📉";
    "â„¹ï¸ " = "ℹ️";
    "ðŸŒ§ï¸ " = "🌧️";
    "ðŸ’§" = "💧";
    "ðŸ œï¸ " = "🏜️";
    "ðŸš¿" = "🚿";
    "âš ï¸ " = "⚠️";
    "ðŸŸ¡" = "🟡";
    "ðŸŸ¢" = "🟢";
    "ðŸŒ±" = "🌱";
    "ðŸ“…" = "📅";
    "ðŸ”´" = "🔴";
    "ðŸšœ" = "🚜";
    "ðŸ–Œï¸ " = "🖌️";
    "ðŸŽ¯" = "🎯";
    "ðŸ›‘" = "🛑";
    "â†’" = "→";
    "ðŸš€" = "🚀";
    "ðŸ”„" = "🔄";
    "ðŸ’¾" = "💾";
    "ðŸ—ºï¸ " = "🗺️";
    "ðŸ’¡" = "💡";
    "â ³" = "⏳";
    "âœ•" = "✖"
}

foreach ($key in $dict.Keys) {
    if ($content.Contains($key)) {
        $content = $content.Replace($key, $dict[$key])
    }
}

[System.IO.File]::WriteAllText("c:\Users\MTN\OneDrive\Desktop\MTN\External Projects\UZ - Survey and Geomatics\Agriculture - ML model\gee_app.js", $content, [System.Text.Encoding]::UTF8)
Write-Output "Successfully replaced corrupted strings in gee_app.js using proper UTF-8 parsing!"
