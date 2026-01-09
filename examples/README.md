## examples ディレクトリについて

このディレクトリには、本ツールの使い方をイメージしやすくするための
**最小限のサンプル構成** を配置します。

### `simple-config/` サンプル

`simple-config/` は、1 つのシートに少数のセルだけを書き込むことを想定した
シンプルな設定例です。

構成:

- `simple-config/ポートフォリオ_Template_sample.xlsx`
  - ダミーの Excel テンプレートファイルです。
  - 実際の運用では、ここにレイアウト済みのポートフォリオテンプレートを置きます。
- `simple-config/.cursor/portfolio_config.json`
  - 本ツールが読み込む設定ファイルのサンプルです。
  - Excel テンプレート名・シート名・セルごとのマッピング情報などを定義します。

### `portfolio_config.json` が読み込まれる想定

将来的に、CLI から次のような流れで利用されることを想定しています。

1. プロジェクトルート（この `examples/simple-config` と同等の構成）に移動する。
2. `.cursor/portfolio_config.json` を、`src/portfolio_generator/config_loader.py` のロジックで読み込む。
3. 読み込んだ設定をもとに:
   - プロンプト生成モジュール（`prompt_generator.py`）がプロンプト Markdown を生成
   - Excel 出力モジュール（`excel_writer.py`）がテンプレートに内容を書き込む

現時点では実装途中のため、これらはあくまで **構造と想定フローのサンプル** として
参照してください。









