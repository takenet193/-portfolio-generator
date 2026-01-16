#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-.cursor/mcp.json}"

# プロジェクトルート（現在のディレクトリ）
PROJECT_ROOT="$(pwd)"
WORKSPACE_PATH="$PROJECT_ROOT"

# .cursorディレクトリを作成（存在しない場合）
CURSOR_DIR="$PROJECT_ROOT/.cursor"
if [ ! -d "$CURSOR_DIR" ]; then
  mkdir -p "$CURSOR_DIR"
  echo "Created .cursor directory"
fi

# テンプレートファイルのパス
TEMPLATE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE_FILE="$TEMPLATE_DIR/mcp_config.template.json"

if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "Template not found: $TEMPLATE_FILE" >&2
  exit 1
fi

# テンプレートを読み込んでワークスペースパスを置き換え
sed "s|\${WORKSPACE_PATH}|$WORKSPACE_PATH|g" "$TEMPLATE_FILE" > "$OUTPUT"

echo "Generated $OUTPUT with workspace path: $WORKSPACE_PATH"
echo "Next step: Set GITHUB_PERSONAL_ACCESS_TOKEN in .env file (if needed)"
