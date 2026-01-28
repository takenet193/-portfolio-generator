## ポートフォリオ生成マスタープロンプト

以下の文章を、そのまま AI（Cursor など）のプロンプト欄にコピペして使ってください。

```markdown
@.cursor/portfolio_config.json の設定にもとづき、docs/portfolio-prompts/*.md とコードベースを参照して `.cursor/portfolio-generated-content.json` を作り直し、その内容を使ってポートフォリオの Excel ファイルを生成してください。プロンプトファイルがまだ無い場合は、先に `PYTHONPATH=src python -m portfolio.generate_portfolio_v2 --generate-prompts --verbose` を実行してから同じ処理を行ってください。最後に、生成に使った `.cursor/portfolio-generated-content.json` の内容と、出力された Excel ファイル名を教えてください。
```