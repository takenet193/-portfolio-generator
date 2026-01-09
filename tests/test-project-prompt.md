# テスト用プロンプト: portfolio-generator プロジェクトのポートフォリオ生成

## 重要: このディレクトリについて

**このディレクトリは、portfolio-generator ツール自体の動作をテストするための「テスト用ディレクトリ」です。**

このディレクトリは、portfolio-generator プロジェクトのコピーであり、このツールを使って「このプロジェクト自体のポートフォリオ」を生成することで、ツールの動作を検証します。

## プロジェクト概要: portfolio-generator

### プロジェクトの目的

**portfolio-generator** は、Excelベースのポートフォリオ（職務経歴ポートフォリオなど）を自動生成するための汎用ツールです。

- 各プロジェクト固有の設定ファイル（`.cursor/portfolio_config.json`）と Excel テンプレートを用意すれば、どのプロジェクトでもポートフォリオを自動生成できる
- コードベースの情報を自動的に読み取り、AI を活用してポートフォリオの各セルに適切な内容を生成する
- 将来的には、自分の職務経歴ポートフォリオもこのツールで生成したいという目標がある

### 開発の経緯

このツールは、元々「定型作業支援ツール」というプロジェクトの中で開発されていました。そのプロジェクト内で、Excelベースのポートフォリオ自動生成機能が実装され、実際に使用されていました。

その後、**このポートフォリオ生成機能を独立した汎用ツールとして整理したい**という要望が生まれ、新しいリポジトリ `portfolio-generator` として分離・リファクタリングされました。

- 元プロジェクトから実装コードを移植
- パッケージ構造を整理（`src/portfolio/` 配下にモジュール化）
- 各プロジェクトで使えるように、設定ファイルとテンプレートを分離した構成に変更

### 主な機能とワークフロー

このツールは、以下の3段階のワークフローで動作します：

#### 1. プロンプト生成フェーズ
- `.cursor/portfolio_config.json` と `docs/portfolio-user-settings.md`（オプション）を読み込む
- コードベースを探索し、関連ファイルを読み込む（README.md、ARCHITECTURE.md、requirements.txt など）
- Git 履歴を取得（可能な場合）
- 各セルごとに、詳細なプロンプトファイル（Markdown）を `docs/portfolio-prompts/*.md` に生成
  - セルの説明、文字数制限、コードベースコンテキスト、Git履歴などが含まれる

#### 2. AI による内容生成フェーズ
- 生成されたプロンプトファイルを AI（Cursor AI など）に読み込ませる
- AI が各セルに対応する文章・内容を生成する
- 生成結果を `.cursor/portfolio-generated-content.json` に保存する

#### 3. Excel 出力フェーズ
- Excel テンプレートをコピーする
- JSON に保存された内容を各セルに書き込む
- 最終的なポートフォリオ Excel ファイルを出力する

### 技術スタック

- **言語**: Python 3
- **主要ライブラリ**:
  - `openpyxl` (>=3.1.0): Excel ファイルの操作
- **実行方法**:
  - `PYTHONPATH=src python -m portfolio.generate_portfolio_v2 --generate-prompts` （プロンプト生成）
  - `PYTHONPATH=src python -m portfolio.generate_portfolio_v2 --from-json .cursor/portfolio-generated-content.json` （Excel生成）

### プロジェクト構造

```
portfolio-generator/
├── README.md                    # プロジェクト概要
├── requirements.txt             # 依存ライブラリ（openpyxl のみ）
├── src/
│   └── portfolio/               # メインパッケージ
│       ├── generate_portfolio_v2.py  # CLI エントリポイント
│       ├── config_loader.py     # 設定ファイル読み込み
│       ├── excel_writer.py      # Excel 書き込み
│       ├── file_discovery.py    # ファイル探索
│       ├── codebase_reader.py   # コードベース読み込み
│       ├── prompt_generator.py  # プロンプト生成
│       ├── content_storage.py   # JSON 読み書き
│       └── ...                  # その他のモジュール
├── docs/
│   └── user-guide.md            # ユーザーガイド
└── examples/
    └── simple-config/           # サンプル設定
```

### 今後の展望

- **MCP 連携**: Git 履歴の取得を MCP（Model Context Protocol）経由で行うようにする
- **テンプレートなし生成**: Excel テンプレートがなくても、まっさらなブックから必要なシート・セル構造を自動生成できるようにする
- **汎用化**: 様々なプロジェクトで使えるように、設定ファイルとテンプレートの分離を徹底する

### テスト手順（このディレクトリでの作業）

このテスト用ディレクトリでは、以下の手順で portfolio-generator ツールの動作を検証してください：

1. **設定ファイルの確認**
   - `.cursor/portfolio_config.json` が存在し、適切に設定されているか確認
   - Excel テンプレートファイル（`portfolio_config.json` で指定されたファイル名）がプロジェクト直下に存在するか確認

2. **プロンプト生成の実行**
   ```bash
   PYTHONPATH=src python -m portfolio.generate_portfolio_v2 --generate-prompts --config .cursor/portfolio_config.json
   ```
   - `docs/portfolio-prompts/*.md` にプロンプトファイルが生成されることを確認

3. **AI による内容生成**
   - 生成されたプロンプトファイルを読み込み、各セルに対応する内容を生成
   - 生成結果を `.cursor/portfolio-generated-content.json` に保存
   - JSON の形式は、`content_storage.py` の `ContentStorage` クラスの仕様に従う

4. **Excel 出力の実行**
   ```bash
   PYTHONPATH=src python -m portfolio.generate_portfolio_v2 --from-json .cursor/portfolio-generated-content.json --config .cursor/portfolio_config.json
   ```
   - ポートフォリオ Excel ファイルが生成されることを確認
   - 各セルに適切な内容が書き込まれていることを確認

5. **エラーハンドリングの確認**
   - Git 履歴が取得できない場合の挙動（現在日時をフォールバックする設定があるか）
   - 設定ファイルやテンプレートファイルが見つからない場合のエラーメッセージ

### 期待される成果物

このテストが成功すれば、以下の成果物が得られます：

- **生成されたプロンプトファイル群** (`docs/portfolio-prompts/*.md`)
- **生成されたコンテンツ JSON** (`.cursor/portfolio-generated-content.json`)
- **最終的なポートフォリオ Excel ファイル** (プロジェクト名_ポートフォリオ.xlsx など)

これらの成果物は、portfolio-generator ツール自体の紹介資料としても活用できます。

---

**注意**: このプロンプトは、テスト用ディレクトリの AI に渡すためのものです。実際のテスト実行時には、このプロンプトの内容を参考にしながら、上記の手順に従ってツールを実行してください。







