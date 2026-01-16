# Portfolio Generator

コードベースから自動的に情報を抽出し、Excelベースのポートフォリオ（職務経歴ポートフォリオなど）を自動生成するためのツールです。

## ✨ 主な特徴

- **コードベースから直接情報抽出**: README、アーキテクチャドキュメント、Git履歴などから自動的に情報を抽出
- **AI連携による内容生成**: Cursor AIなどのAIツールと連携し、適切な内容を自動生成
- **柔軟な設定**: JSON設定ファイルで、セルごとのマッピングや文字数制限をカスタマイズ可能
- **多言語対応**: 日本語、英語、中国語など複数言語での生成に対応
- **プロンプト自動生成**: 各セルごとに詳細なプロンプトファイルを自動生成し、AI生成の品質を向上

## 🚀 クイックスタート

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/your-username/portfolio-generator.git
cd portfolio-generator

# 依存ライブラリをインストール
pip install -r requirements.txt
```

### MCP（Model Context Protocol）設定（オプション）

このプロジェクトでは、MCPを使用してGitHubやファイルシステムとの連携が可能です。設定するには：

1. **環境変数ファイルの作成**

   ```bash
   # .envファイルをプロジェクトルートに作成
   cp mcp_template/env.example .env
   ```

2. **環境変数の設定**

   `.env`ファイルを編集して、以下を設定：
   - `GITHUB_PERSONAL_ACCESS_TOKEN`: GitHub Personal Access Token（GitHub連携が必要な場合）
   - `WORKSPACE_PATH`: プロジェクトの絶対パス（例: `c:\Users\ND003\Desktop\portfolio-generator`）

3. **MCP設定ファイルの生成**

   ```powershell
   # Windows PowerShell
   # .cursor/mcp.json が自動生成されます（.cursorディレクトリも自動作成）
   .\mcp_template\scripts\generate_mcp_config.ps1
   ```

   または

   ```bash
   # Unix系シェル
   # .cursor/mcp.json が自動生成されます（.cursorディレクトリも自動作成）
   bash ./mcp_template/scripts/generate_mcp_config.sh
   ```

4. **Cursorでの設定**

   - スクリプト実行後、Cursorは自動的に`.cursor/mcp.json`を読み込みます
   - 詳細は [mcp_template/README.md](mcp_template/README.md) を参照してください

**注意**: MCP設定はオプションです。Git履歴の取得などは、MCPがなくても通常のGitコマンドで動作します。

### 基本的な使い方

1. **対象プロジェクトに設定ファイルを配置**

   ```bash
   # 対象プロジェクトのルートディレクトリに移動
   cd /path/to/your-project
   
   # .cursorディレクトリを作成
   mkdir -p .cursor
   
   # サンプル設定をコピー
   cp portfolio-generator/examples/simple-config/.cursor/portfolio_config.json .cursor/
   
   # Excelテンプレートを配置（設定ファイルで指定したファイル名に合わせる）
   cp your-template.xlsx ポートフォリオ_テンプレート.xlsx
   ```

2. **プロンプトファイルを生成**

   ```bash
   # portfolio-generatorのディレクトリから実行
   cd /path/to/portfolio-generator
   
   PYTHONPATH=src python -m portfolio.generate_portfolio_v2 \
     --project-root /path/to/your-project \
     --generate-prompts
   ```

3. **AIで内容を生成**

   - `docs/portfolio-prompts/` に生成されたプロンプトファイルを確認
   - Cursor AIなどで各プロンプトファイルを読み込み、内容を生成
   - 生成した内容を `.cursor/portfolio-generated-content.json` に保存

4. **Excelファイルを生成**

   ```bash
   PYTHONPATH=src python -m portfolio.generate_portfolio_v2 \
     --project-root /path/to/your-project \
     --from-json .cursor/portfolio-generated-content.json
   ```

## 📋 ワークフロー

ポートフォリオ生成は以下の3ステップで行われます：

1. **プロンプト生成フェーズ**
   - `.cursor/portfolio_config.json` と `docs/portfolio-user-settings.md`（オプション）をもとに、セルごとのプロンプトファイル（Markdown）を生成
   - コードベースのコンテキストや Git 履歴なども自動的に含まれます

2. **AI による内容生成フェーズ**
   - 生成されたプロンプトを AI（Cursor AI など）に読み込ませ、各セルに対応する文章・内容を生成
   - 生成結果は `.cursor/portfolio-generated-content.json` に保存

3. **Excel 出力フェーズ**
   - Excel テンプレートをコピーし、JSON に保存された内容を各セルに書き込み
   - 最終的なポートフォリオ Excel ファイルを出力

## 📁 プロジェクト構造

```
portfolio-generator/
├── src/portfolio/          # ソースコード
│   ├── generate_portfolio_v2.py  # メインスクリプト
│   ├── config_loader.py          # 設定ファイル読み込み
│   ├── prompt_generator.py       # プロンプト生成
│   └── ...
├── docs/                   # ドキュメント
│   ├── user-guide.md       # 詳細なユーザーガイド
│   └── portfolio-user-settings.md  # ユーザー設定の説明
├── examples/               # サンプル
│   └── simple-config/     # シンプルな設定例
├── mcp_template/           # MCP設定テンプレート
│   ├── env.example         # 環境変数テンプレート
│   ├── mcp_config.template.json  # MCP設定テンプレート
│   └── scripts/            # 設定ファイル生成スクリプト
└── requirements.txt        # 依存ライブラリ
```

## 📖 ドキュメント

- [詳細なユーザーガイド](docs/user-guide.md) - 完全な機能説明と使用方法
- [ユーザー設定ファイル](docs/portfolio-user-settings.md) - カスタマイズ方法
- [サンプル設定](examples/simple-config/) - 設定ファイルの例

## 🛠️ 主な機能

### コードベース解析
- README、アーキテクチャドキュメントの自動検出
- Git履歴の時系列解析
- ファイル重要度に基づく優先順位付け

### プロンプト生成
- セルごとの詳細なプロンプト自動生成
- コードベースコンテキストの自動組み込み
- 多言語・トーン設定に対応

### Excel出力
- テンプレートベースの自動書き込み
- セルマッピングの柔軟な設定
- 文字数制限の自動適用

## 📝 使用例

### プロンプト生成のみ

```bash
PYTHONPATH=src python -m portfolio.generate_portfolio_v2 \
  --project-root /path/to/project \
  --generate-prompts \
  --verbose
```

### JSONからExcel生成

```bash
PYTHONPATH=src python -m portfolio.generate_portfolio_v2 \
  --project-root /path/to/project \
  --from-json .cursor/portfolio-generated-content.json \
  --output my-portfolio.xlsx
```

## 🔧 設定ファイル

設定ファイル（`.cursor/portfolio_config.json`）で以下をカスタマイズできます：

- Excelテンプレートのパスとシート名
- セルごとのマッピング（セルアドレス、文字数制限など）
- コードベースソースの指定（README.md、Git履歴など）
- 生成言語とトーン設定

詳細は [examples/simple-config/.cursor/portfolio_config.json](examples/simple-config/.cursor/portfolio_config.json) を参照してください。

## 📄 ライセンス

このプロジェクトは [MIT License](LICENSE) の下で公開されています。

## 🤝 コントリビューション

プルリクエストやIssueの報告を歓迎します！詳細は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## 📧 お問い合わせ

問題や質問がある場合は、GitHubのIssueでお知らせください。

---

**注意**: このツールは Cursor AI などのAIツールと連携して使用することを想定しています。AIによる内容生成には、適切なAIツールのセットアップが必要です。

