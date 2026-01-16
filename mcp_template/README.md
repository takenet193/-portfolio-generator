# MCP テンプレート

このディレクトリは、GitHub/Filesystem MCP 連携を他プロジェクトに即適用するためのテンプレートです。

## 構成
- `mcp_config.template.json`: プレースホルダ入りMCP設定テンプレート
- `env.example`: 参考用環境変数テンプレート
- `scripts/`:
  - `generate_mcp_config.ps1`: Windows PowerShell用生成スクリプト
  - `generate_mcp_config.sh`: Unix系シェル用生成スクリプト

## 使い方（最短）
1. `.env` をプロジェクトルートに作成（`env.example`を参考）し、`GITHUB_PERSONAL_ACCESS_TOKEN` を設定
2. `mcp_template/` を新規プロジェクトへコピー
3. スクリプトを実行して `.cursor/mcp.json` を自動生成（`.cursor`ディレクトリも自動作成されます）
4. Cursor は自動的に `.cursor/mcp.json` を読み込みます

### PowerShell
```powershell
# mcp_templateディレクトリをコピーしたプロジェクトのルートから実行
.\mcp_template\scripts\generate_mcp_config.ps1
```

### Bash
```bash
# mcp_templateディレクトリをコピーしたプロジェクトのルートから実行
bash ./mcp_template/scripts/generate_mcp_config.sh
```

## よくある質問
- GitHubトークンはどこで設定しますか？
  - `.env` に `GITHUB_PERSONAL_ACCESS_TOKEN` を設定してください。Cursor/MCP 実行環境から参照されます。
- workspace の相対パスは使えますか？
  - いいえ。`filesystem` MCP は絶対パスが必要です。


## 環境変数
- `${WORKSPACE_PATH}`: ファイルシステムMCPでアクセス許可する絶対パス
- `${GITHUB_PERSONAL_ACCESS_TOKEN}`: GitHub Personal Access Token

## 注意
- `.env` はGit管理に含めないでください
- ワークスペースパスは必ず絶対パスで指定してください
