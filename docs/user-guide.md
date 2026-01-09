# ポートフォリオ自動生成システム v2.0 ユーザーガイド

## 概要

ポートフォリオ自動生成システムは、コードベースから直接情報を抽出してエクセルファイルに自動入力するシステムです。マークダウンレポート経由方式を廃止し、AI（Cursor AI）による対話的な内容生成を採用しています。

### 主な特徴

- **コードベースから直接情報抽出**: マークダウンレポートを経由せず、コードベースを直接参照
- **動的ファイル探索**: パターンマッチングにより、プロジェクト構造に依存しない柔軟なファイル探索
- **AIによる対話的内容生成**: Cursor AIがコードベースを参照して適切な内容を生成
- **プロンプトファイルベース**: 各セルごとに詳細なプロンプトファイルを生成
- **JSON形式での内容管理**: 生成された内容をJSON形式で保存・管理

## システム構成

```
プロジェクトルート/
├── .cursor/
│   ├── portfolio_config.json              # 設定ファイル
│   └── portfolio-generated-content.json   # 生成された内容（JSON）
├── docs/
│   └── portfolio-prompts/                 # プロンプトファイル（自動生成）
│       ├── 日付.md
│       ├── タイトル.md
│       ├── 背景.md
│       └── ...
├── ポートフォリオ_テンプレート.xlsx      # エクセルテンプレート（例）
└── （その他、通常のコード・ドキュメントなど）
```

### ツール本体（`portfolio-generator`）の構成例

このリポジトリ自体の中身、あるいはモノレポ内で「ツール用スクリプト群」としてまとめて配置する場合のイメージです。  
（現在のリポジトリでは `src/portfolio/` にありますが、下記のように `scripts/portfolio/` 配下に置いても構いません。）

```text
├── scripts/
│   └── portfolio/
│       ├── generate_portfolio_v2.py   # メインスクリプト
│       ├── config_loader.py           # 設定ファイル読み込み
│       ├── excel_writer.py            # エクセル操作
│       ├── file_discovery.py          # ファイル探索
│       ├── codebase_reader.py         # コードベース読み込み
│       ├── semantic_search.py         # セマンティック検索
│       ├── git_history.py             # Git履歴読み込み
│       ├── content_generator.py       # 内容生成（簡易実装）
│       ├── prompt_generator.py        # プロンプトファイル生成
│       └── content_storage.py         # JSON保存・読み込み
└── ポートフォリオ_Template_ver2.0.xlsx  # エクセルテンプレート
```

## セットアップ手順（別プロジェクトで使う場合）

ここでは、「**あなたのポートフォリオ対象プロジェクト**」にこの仕組みを導入して使うための最低限のセットアップ手順を説明します。

### 1. このツールリポジトリの準備

1. `portfolio-generator` リポジトリを任意の場所にクローンします。
2. 依存ライブラリをインストールします。
   ```bash
   pip install -r requirements.txt
   ```

### 2. 対象プロジェクト側の `.cursor/portfolio_config.json` を用意

1. ポートフォリオを作りたい「対象プロジェクト」のルートディレクトリに移動します。
2. その直下に `.cursor` ディレクトリがなければ作成します。
   ```bash
   mkdir .cursor
   ```
3. このリポジトリのサンプル設定をベースにコピーします。
   - コピー元: `portfolio-generator/examples/simple-config/.cursor/portfolio_config.json`
   - コピー先: `（対象プロジェクト）/.cursor/portfolio_config.json`
4. 必要に応じて、コピーした `portfolio_config.json` を編集します。
   - `excel_template.file` … 使いたいエクセルテンプレートのファイル名
   - `cell_mapping` … セルの割り当てや文字数などをプロジェクトに合わせて調整

### 3. エクセルテンプレートファイルを配置

1. 対象プロジェクトのルート直下に、ポートフォリオ用テンプレートファイルを配置します。
   - 例: `ポートフォリオ_テンプレート.xlsx`
2. `portfolio_config.json` の `excel_template.file` に、そのファイル名を設定します。
   - 相対パスの場合、**対象プロジェクトのルート** からの相対パスとして解釈されます。
   - 例: ルート直下に置く場合
     ```json
     "excel_template": {
       "file": "ポートフォリオ_テンプレート.xlsx",
       "sheet": "フォーマット"
     }
     ```

### 4. コマンド実行時の注意（`--project-root`）

- `generate_portfolio_v2.py` は、`--project-root` で「対象プロジェクトのルート」を受け取ります。
  - 省略した場合は、**カレントディレクトリ** を対象プロジェクトとみなします。
- 例えば、`portfolio-generator` リポジトリのディレクトリで次のように実行すると、
  別ディレクトリのプロジェクトを対象にできます。

```bash
cd /path/to/portfolio-generator

PYTHONPATH=src python -m portfolio.generate_portfolio_v2 \
  --project-root /path/to/your/target-project \
  --generate-prompts --verbose
```

- 逆に、対象プロジェクト側でコマンドを実行したい場合は、環境変数 `PYTHONPATH` で
  `portfolio-generator/src` を見えるようにしてから実行してください。

## 使い方

### 基本的なワークフロー

ポートフォリオ生成は以下の3ステップで行われます：

1. **プロンプトファイルの生成**
2. **AIによる内容生成**
3. **エクセルファイルの生成**

### ステップ1: プロンプトファイルの生成

まず、各セルごとのプロンプトファイルを生成します。

```bash
python scripts/portfolio/generate_portfolio_v2.py --generate-prompts
```

このコマンドを実行すると：
- `docs/portfolio-prompts/` ディレクトリに各セルごとのMarkdownプロンプトファイルが生成されます
- 各プロンプトファイルには、セルの説明、コードベースコンテキスト、生成指示が含まれます

**出力例**:
```
プロンプトファイルを生成しました: 15 ファイル
プロンプトファイルの場所: docs/portfolio-prompts
```

### ステップ2: AIによる内容生成

生成されたプロンプトファイルをCursor AIで読み込み、コードベースを参照しながら各セルの内容を生成します。

1. `docs/portfolio-prompts/` ディレクトリ内の各プロンプトファイルを確認
2. Cursor AIで各プロンプトファイルを読み込み、コードベースを参照
3. 生成した内容を `.cursor/portfolio-generated-content.json` に保存

**JSON形式の例**:
```json
{
  "version": "2.0",
  "generated_at": "2025-11-27T11:00:00",
  "cells": {
    "日付": {
      "cell": "D3",
      "content": "2025年11月19日",
      "generated_by": "cursor-ai"
    },
    "タイトル": {
      "cell": "D4",
      "content": "発達障害者向け定型業務サポートツール",
      "generated_by": "cursor-ai"
    }
  }
}
```

### ステップ3: エクセルファイルの生成

生成されたJSONファイルからエクセルファイルを生成します。

```bash
python scripts/portfolio/generate_portfolio_v2.py --from-json .cursor/portfolio-generated-content.json
```

このコマンドを実行すると：
- JSONファイルから生成済みの内容を読み込み
- エクセルテンプレートをコピー
- 各セルに内容を書き込み
- 出力ファイルを保存

**出力例**:
```
定型作業支援ツール_ポートフォリオ.xlsx
```

## コマンドラインオプション

### 基本的なオプション

```bash
python scripts/portfolio/generate_portfolio_v2.py [オプション]
```

| オプション | 説明 | デフォルト値 |
|-----------|------|-------------|
| `--config`, `-c` | 設定ファイルのパス | `.cursor/portfolio_config.json` |
| `--output`, `-o` | 出力ファイルのパス | `{プロジェクト名}_ポートフォリオ.xlsx` |
| `--project-root`, `-p` | プロジェクトルートディレクトリ | 現在のディレクトリ |
| `--verbose`, `-v` | 詳細なログを出力 | `False` |

### プロンプト生成モード

```bash
python scripts/portfolio/generate_portfolio_v2.py --generate-prompts [オプション]
```

| オプション | 説明 | デフォルト値 |
|-----------|------|-------------|
| `--prompts-dir` | プロンプトファイルの出力ディレクトリ | `docs/portfolio-prompts/` |

**例**:
```bash
python scripts/portfolio/generate_portfolio_v2.py --generate-prompts --prompts-dir ./my-prompts
```

### JSON読み込みモード

```bash
python scripts/portfolio/generate_portfolio_v2.py --from-json <JSONファイルパス> [オプション]
```

**例**:
```bash
python scripts/portfolio/generate_portfolio_v2.py --from-json .cursor/portfolio-generated-content.json --output my-portfolio.xlsx
```

## 関連ファイル

### 設定ファイル: `.cursor/portfolio_config.json`

ポートフォリオ生成システムの設定を定義します。

#### 主要な設定項目

- **excel_template**: エクセルテンプレートファイルの情報
  - `file`: テンプレートファイル名
  - `sheet`: シート名
- **cell_mapping**: 各セルのマッピング情報
  - `cell`: セルアドレス（例: "D3"）
  - `max_chars`: 最大文字数
  - `codebase_sources`: 参照すべきコードベースソース
  - `transform`: 変換ルール
  - `description`: セルの説明
- **text_transforms**: テキスト変換ルールの定義

#### 設定例

```json
{
  "version": "2.0",
  "excel_template": {
    "file": "ポートフォリオ_Template_ver2.0.xlsx",
    "sheet": "フォーマット"
  },
  "cell_mapping": {
    "タイトル": {
      "cell": "D4",
      "max_chars": 50,
      "codebase_sources": ["README.md", "ARCHITECTURE.md"],
      "description": "このテーマを一言で表すと？"
    }
  }
}
```

### ユーザー設定ファイル: `docs/portfolio-user-settings.md`

ポートフォリオの**文字数やトーンをユーザーが直接コントロールするための設定ファイル**です。  
開発者向けの `portfolio_config.json` を触らずに、次のような項目をセルごとに指定できます。

- **最大文字数**（例: 背景は400文字、今後の施策は200文字 など）
- **AIへの指示**（そのセルで何を書いてほしいか・NG事項など）

このファイルの内容は、`--generate-prompts` 実行時に自動的に読み込まれ、  
`docs/portfolio-prompts/*.md` の「文字数制限」「ユーザー共通ルール」「ユーザーからの追加指示」に反映されます。

**使い方の流れ（ユーザー設定ファイルを使う場合）**

1. `docs/portfolio-user-settings.md` を編集し、各セルの最大文字数・指示文を調整する
2. プロンプトを再生成する  
   ```bash
   python scripts/portfolio/generate_portfolio_v2.py --generate-prompts --verbose
   ```
3. 更新された `docs/portfolio-prompts/*.md` をCursor AIに読み込ませ、指示どおりに内容を生成する
4. 生成した内容を `.cursor/portfolio-generated-content.json` に反映し、`--from-json` でExcelを生成する

### プロンプトファイル: `docs/portfolio-prompts/*.md`

各セルごとに生成されるMarkdown形式のプロンプトファイルです。

#### プロンプトファイルの構造

```markdown
# セル: {セル名} ({セルアドレス})

## 説明
{セルの説明}

## 文字数制限
最大: {max_chars}文字

## 変換ルール
{transform}

## 参照すべきコードベースソース
- {source1}
- {source2}

## コードベースコンテキスト

### 関連ファイルの内容
{関連ファイルの内容}

### Git開発履歴（gitソースが指定されている場合）
{時系列での開発履歴}

## 生成指示
{生成指示}
```

#### Git履歴の内容

`codebase_sources`に`git`が含まれている場合、プロンプトファイルには以下のGit履歴情報が自動的に含まれます：

- **時系列での開発の様子**: 日付ごとにグループ化されたコミット履歴
  - コミットメッセージ
  - コミットハッシュ
  - 作成者
  - 変更ファイル数とカテゴリ分類
- **開発統計**: 総コミット数、変更ファイル数、開発者数、開発期間

この情報により、AIは開発の流れやプロジェクトの進捗状況を把握し、より適切な内容を生成できます。

### マスタープロンプト: `portfolio_master_prompt.md`

ポートフォリオ生成全体の流れを AI に一括で指示するための**マスタープロンプト**です。  
`portfolio_master_prompt.md` に書かれている Markdown ブロックを、そのまま Cursor などのプロンプト欄にコピペして使います。

- `.cursor/portfolio_config.json` の設定
- `docs/portfolio-prompts/*.md` のプロンプトファイル
- コードベース全体

を参照して `.cursor/portfolio-generated-content.json` を作り直し、その内容を使って Excel のポートフォリオを生成するよう AI に依頼するテンプレートになっています。

### JSONファイル: `.cursor/portfolio-generated-content.json`

AIが生成した内容を保存するJSONファイルです。

#### JSONファイルの構造

```json
{
  "version": "2.0",
  "generated_at": "2025-11-27T11:00:00",
  "cells": {
    "{セル名}": {
      "cell": "{セルアドレス}",
      "content": "{生成された内容}",
      "generated_by": "cursor-ai",
      "generated_at": "2025-11-27T11:00:00"
    }
  }
}
```

### エクセルテンプレート: `ポートフォリオ_Template_ver2.0.xlsx`

ポートフォリオのテンプレートファイルです。このファイルをコピーして、各セルに内容を書き込みます。

## モジュール構成

### `scripts/portfolio/generate_portfolio_v2.py`

メインスクリプト。以下の機能を提供します：
- プロンプトファイル生成モード
- JSON読み込みモード
- 通常モード（簡易実装）

### `scripts/portfolio/config_loader.py`

設定ファイル（`portfolio_config.json`）の読み込みと検証を行います。

### `scripts/portfolio/excel_writer.py`

エクセルファイルの操作を行います：
- テンプレートファイルのコピー
- セルへの内容書き込み
- 書式の保持

### `scripts/portfolio/file_discovery.py`

コードベースから関連ファイルを探索します：
- パターンマッチングによるファイル探索
- ディレクトリ構造の自動認識
- ファイル重要度評価

### `scripts/portfolio/codebase_reader.py`

ファイルを読み込んでコンテキスト情報を構築します。

### `scripts/portfolio/semantic_search.py`

セマンティック検索のインターフェースを提供します（Cursor AIの機能を使用）。

### `scripts/portfolio/git_history.py`

Git履歴を読み込み、時系列で開発の様子をマークダウン形式で文書化します：
- Gitコミット履歴の取得
- 日付ごとのグループ化
- 変更ファイルのカテゴリ分類
- 開発統計情報の生成
- 最新コミット日の取得とフォーマット変換

### `scripts/portfolio/prompt_generator.py`

プロンプトファイルを生成します：
- 各セルごとのプロンプトファイル生成
- コードベースコンテキストの組み込み
- Git履歴の自動読み込みと組み込み
- 生成指示の追加

### `scripts/portfolio/content_storage.py`

生成された内容のJSON形式での保存・読み込みを行います。

### `scripts/portfolio/content_generator.py`

内容生成の簡易実装（現在は使用されていません。AIによる生成が推奨されます）。

## 使用例

### 基本的な使用例

```bash
# 1. プロンプトファイルを生成
python scripts/portfolio/generate_portfolio_v2.py --generate-prompts

# 2. Cursor AIでプロンプトファイルを読み込み、内容を生成
# → .cursor/portfolio-generated-content.json に保存

# 3. エクセルファイルを生成
python scripts/portfolio/generate_portfolio_v2.py --from-json .cursor/portfolio-generated-content.json
```

### カスタム出力パスを指定

```bash
python scripts/portfolio/generate_portfolio_v2.py --from-json .cursor/portfolio-generated-content.json --output ./output/my-portfolio.xlsx
```

### 詳細ログを有効化

```bash
python scripts/portfolio/generate_portfolio_v2.py --generate-prompts --verbose
```

### カスタム設定ファイルを使用

```bash
python scripts/portfolio/generate_portfolio_v2.py --config ./my-config.json --generate-prompts
```

## トラブルシューティング

### エラー: テンプレートファイルが見つかりません

**原因**: エクセルテンプレートファイルが指定されたパスに存在しない。

**解決方法**:
1. `ポートフォリオ_Template_ver2.0.xlsx` がプロジェクトルートに存在することを確認
2. `portfolio_config.json` の `excel_template.file` が正しいファイル名であることを確認

### エラー: JSONファイルにセルデータが含まれていません

**原因**: JSONファイルが空、または `cells` セクションが存在しない。

**解決方法**:
1. JSONファイルの構造を確認
2. 以下の形式になっていることを確認：
   ```json
   {
     "cells": {
       "セル名": {
         "cell": "セルアドレス",
         "content": "内容"
       }
     }
   }
   ```

### エラー: セルアドレスが設定されていません

**原因**: `portfolio_config.json` の `cell_mapping` にセルアドレスが設定されていない。

**解決方法**:
1. `portfolio_config.json` を確認
2. 各セルの `cell` フィールドが正しく設定されていることを確認

### プロンプトファイルが生成されない

**原因**: ファイル権限の問題、または出力ディレクトリが作成できない。

**解決方法**:
1. 出力ディレクトリ（`docs/portfolio-prompts/`）の書き込み権限を確認
2. `--prompts-dir` オプションで別のディレクトリを指定してみる

### エクセルファイルに内容が書き込まれない

**原因**:
- JSONファイルのセルアドレスが設定ファイルと一致していない
- エクセルのシート名が間違っている

**解決方法**:
1. JSONファイルのセルアドレスが設定ファイルの `cell_mapping` と一致していることを確認
2. `portfolio_config.json` の `excel_template.sheet` が正しいシート名であることを確認

## 注意事項

- **エクセルテンプレート**: テンプレートファイルは上書きされません。常にコピーが作成されます
- **JSONファイル**: 既存のJSONファイルがある場合、内容が追加・更新されます
- **プロンプトファイル**: プロンプトファイルは生成時に上書きされます
- **コードベース探索**: プロジェクトの構造に依存しないよう、動的ファイル探索を使用しています

## 今後の改善予定

- プロンプトファイルのバッチ処理機能
- エクセルテンプレートの自動検出
- より高度なセマンティック検索
- 複数プロジェクト対応

## 関連ドキュメント

- [仕様書](tasks/portfolio-generation-spec-v2.md)
- [実装計画](tasks/portfolio-generation-v2-implementation-plan.md)
