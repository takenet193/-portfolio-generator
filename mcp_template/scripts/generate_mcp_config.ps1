param(
    [string]$Output = ".cursor/mcp.json"
)

$ErrorActionPreference = "Stop"

# プロジェクトルート（現在のディレクトリ）
$projectRoot = Get-Location
$workspacePath = $projectRoot.Path

# .cursorディレクトリを作成（存在しない場合）
$cursorDir = Join-Path $projectRoot ".cursor"
if (-not (Test-Path $cursorDir)) {
    New-Item -ItemType Directory -Path $cursorDir -Force | Out-Null
    Write-Host "Created .cursor directory"
}

# テンプレートファイルのパス
$templatePath = Join-Path $PSScriptRoot "..\mcp_config.template.json"

# テンプレートを読み込む
$templateContent = Get-Content -Path $templatePath -Raw -Encoding UTF8

# ワークスペースパスを置き換え（Windowsパスのバックスラッシュをエスケープ）
$workspacePathEscaped = $workspacePath -replace '\\', '\\'

# プレースホルダーを置き換え
$configContent = $templateContent -replace '\$\{WORKSPACE_PATH\}', $workspacePathEscaped

# 出力ファイルに書き込む
$outputPath = Join-Path $projectRoot $Output
$configContent | Set-Content -Path $outputPath -Encoding UTF8 -NoNewline

Write-Host "Generated $Output with workspace path: $workspacePath"
Write-Host "Next step: Set GITHUB_PERSONAL_ACCESS_TOKEN in .env file (if needed)"
