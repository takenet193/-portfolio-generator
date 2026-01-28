# セマンティック検索実装計画

## 現状の問題点

### 1. セマンティック検索が未実装
- `semantic_search.py`にはインターフェースは実装されているが、実際には使用されていない
- `prompt_generator.py`の`_get_relevant_files()`で`semantic_search`が指定されても、単に全ファイルを含めるだけの簡易実装
- セルごとの説明に基づいた動的なファイル選択ができない

### 2. 精度への影響
- ルールベースで選ばれた10ファイルを全セルで共有している
- セルごとの説明（例：「業界の現状、課題」）に基づいて関連ファイルを動的に発見できない
- 設定ファイルで明示的に指定されたファイルのみ使用可能

### 3. 現在の実装箇所

#### `src/portfolio/prompt_generator.py` (382-384行目)
```python
if source == "semantic_search":
    # セマンティック検索の場合はすべてのファイルを含める
    relevant_files.update(all_contents)
```

#### `src/portfolio/semantic_search.py`
- `get_relevant_files_for_cell()`関数は定義されているが、どこからも呼び出されていない
- `codebase_search_func`パラメータが必要だが、実際には渡されていない

## 実装の課題

### 最大の課題: Cursorのセマンティック検索結果をPython側に渡す方法（採用方針: 選択肢4）

**選択肢1**: Pythonスクリプトから直接呼び出す
- メリット: 完全自動化が可能
- デメリット: 呼び出し方法の実装が必要（CursorのAPI/CLI経由？）
- 現状: コードベースに直接呼び出す方法の記載なし

**選択肢2**: プロンプトに検索指示を含める（現在のワークフローに合う）
- メリット: 既存のワークフローを維持できる
- デメリット: 手動でCursor AIを使う必要がある
- 実装: プロンプトファイルに「セマンティック検索を使用して関連ファイルを探してください」と指示を追加

**選択肢3**: ハイブリッドアプローチ（将来オプション）
- フォールバック付きで実装
- （可能なら）`codebase_search`が使える場合は使用
- 使えない場合は既存の全ファイルを含める方式にフォールバック

**選択肢4（採用）**: 検索結果を外部入力（JSON）として渡す（推奨）
- メリット: **Python CLI単体で完結**でき、Cursorの非公開仕様（スコア/順序保証なし）に依存しにくい
- デメリット: 検索結果JSONの生成は「人 or エージェント（Cursor側）」が必要
- 実装: `--semantic-search-results <path.json>` を追加し、セル名→候補ファイル配列を読み込んで再ランキング＆追加読み込みを行う

## 実装計画

### フェーズ1: 基本実装

#### 1.1 `prompt_generator.py`の修正

**修正箇所**: `_get_relevant_files()`メソッド

**変更内容**:
- `cell_description`パラメータを追加
- `codebase_search_func`パラメータを追加
- `semantic_search`指定時に`get_relevant_files_for_cell()`を呼び出す
- 検索結果からファイルパスを取得し、`all_contents`から該当ファイルを抽出

**実装例**:
```python
def _get_relevant_files(
    self, 
    codebase_sources: list[str], 
    all_contents: dict[str, str],
    cell_description: str = "",  # 追加
    codebase_search_func: Any = None,  # 追加
) -> tuple[dict[str, str], str]:
    relevant_files: dict[str, str] = {}
    git_content = ""

    for source in codebase_sources:
        if source == "semantic_search":
            if codebase_search_func and cell_description:
                # セマンティック検索を実行
                from portfolio.semantic_search import get_relevant_files_for_cell
                file_paths = get_relevant_files_for_cell(
                    cell_description=cell_description,
                    codebase_search_func=codebase_search_func,
                    target_directories=None,  # 全体を検索
                )
                # 検索結果からファイルを抽出
                for file_path in file_paths:
                    # 絶対パスと相対パスの両方に対応
                    for existing_path, content in all_contents.items():
                        if file_path in existing_path or existing_path.endswith(file_path):
                            if existing_path not in relevant_files:
                                relevant_files[existing_path] = content
                                break
                
                if not relevant_files:
                    logger.warning(
                        "セマンティック検索でファイルが見つかりませんでした。"
                        "フォールバックとして全ファイルを含めます。"
                    )
                    relevant_files.update(all_contents)
            else:
                # フォールバック: 全ファイルを含める
                logger.debug(
                    "codebase_search_funcが提供されていないため、"
                    "全ファイルを含めます（フォールバック）"
                )
                relevant_files.update(all_contents)
        # ... (既存の処理)
```

#### 1.2 `_build_prompt_content()`の修正

**修正箇所**: `_build_prompt_content()`メソッド

**変更内容**:
- `_get_relevant_files()`呼び出し時に`cell_description`と`codebase_search_func`を渡す

**実装例**:
```python
# codebase_sourcesに基づいて関連ファイルを抽出
relevant_files, git_content = self._get_relevant_files(
    codebase_sources, 
    all_contents,
    cell_description=description,  # 追加
    codebase_search_func=self.codebase_search_func,  # 追加
)
```

#### 1.3 `PromptGenerator`クラスの修正

**修正箇所**: `__init__()`メソッド

**変更内容**:
- `codebase_search_func`パラメータを追加（オプション）

**実装例**:
```python
def __init__(
    self,
    config: Any,
    codebase_context: Any,
    project_root: str,
    user_settings: UserSettings | None = None,
    codebase_search_func: Any = None,  # 追加
):
    self.config = config
    self.codebase_context = codebase_context
    self.project_root = project_root
    self.user_settings = user_settings
    self.codebase_search_func = codebase_search_func  # 追加
```

### フェーズ2: 統合

#### 2.1 `generate_prompts()`の修正

**修正箇所**: `generate_prompts()`関数

**変更内容**:
- `semantic_search_results_path`（JSONファイルパス）パラメータを追加
- JSONを読み込み、`PromptGenerator`に渡す（セル名→候補ファイル配列）
- （将来オプション）`codebase_search_func` DI は残してもよいが、案Aでは必須ではない

**実装例**:
```python
def generate_prompts(
    config: Any,
    codebase_context: Any,
    project_root: str,
    output_dir: str | None = None,
    user_settings_path: str | None = None,
    semantic_search_results_path: str | None = None,  # 追加（案A）
) -> list[str]:
    # ...
    semantic_search_results = None
    if semantic_search_results_path:
        # JSONを読み込む（セル名→候補ファイル配列）
        pass
    generator = PromptGenerator(
        config, 
        codebase_context, 
        project_root, 
        user_settings=user_settings,
        semantic_search_results=semantic_search_results,  # 追加（案A）
    )
    return generator.generate_all_prompts(output_dir)
```

#### 2.2 `generate_portfolio_v2.py`の修正

**修正箇所**: `generate_prompts_mode()`関数

**変更内容**:
- CLI引数 `--semantic-search-results` を追加（任意）
- 指定された場合は `generate_prompts()` に渡す
- 未指定の場合は従来フォールバック（初期10ファイル）で動作

**実装例**:
```python
def generate_prompts_mode(
    config_path: str | None = None,
    project_root: str | None = None,
    prompts_dir: str | None = None,
    verbose: bool = False,
    semantic_search_results_path: str | None = None,  # 追加（案A）
) -> int:
    # ...
    generated_files = generate_prompts(
        config, 
        context, 
        project_root, 
        prompts_dir,
        semantic_search_results_path=semantic_search_results_path,  # 追加（案A）
    )
```

### フェーズ3: 外部入力（`--semantic-search-results`）の仕様と運用

#### 3.1 JSONファイルのスキーマ（案A）

- 目的: 「セルごとの説明」に対して、Cursor側で `@Codebase` 等を使って候補ファイルを集め、その結果をPythonに渡す
- 形式: **セル名→候補ファイル配列**（順位順は参考情報として保持。スコアが取れない前提）

**最小スキーマ（推奨）**:

```json
{
  "目的": [
    "README.md",
    "ARCHITECTURE.md",
    "src/portfolio/generate_portfolio_v2.py"
  ],
  "課題": [
    "README.md",
    "docs/semantic-search-implementation-plan.md"
  ]
}
```

**拡張スキーマ（将来/ログ用途）**:

```json
{
  "目的": [
    { "path": "README.md", "rank": 0 },
    { "path": "ARCHITECTURE.md", "rank": 1 }
  ]
}
```

#### 3.2 運用フロー（案A）

1. Cursorで各セル（または重要セル）について `@Codebase` 検索を行い、候補ファイルパスを抽出
2. 上記JSONに保存（リポジトリ内なら例: `.cursor/semantic-search-results.json`）
3. Python実行時に渡す
   - 例: `python -m portfolio.generate_portfolio_v2 --generate-prompts --semantic-search-results .cursor/semantic-search-results.json`
4. Python側は「候補ファイル×ルール重要度」で再ランキングし、上位Nだけを読み込み＆プロンプトに含める

#### 3.3 `codebase_search`の出力形式確認について（案Aでは“参考”）

- 案AではPython側が Cursor の生レスポンスを直接扱わないため、**`codebase_search`の返却形式・順序保証の調査は必須ではない**  
- ただし、JSON生成を自動化したい場合（エージェントが結果を抽出する等）は、以下の調査は有用

#### 3.1 調査が必要な項目

1. **CursorのAPI/CLI経由での呼び出し**
   - Cursorのコマンドラインインターフェースがあるか
   - APIエンドポイントがあるか
   - 環境変数や設定ファイルから取得できるか

2. **Pythonモジュールとしての利用**
   - `cursor`パッケージがインストールされているか
   - インポート可能か

3. **外部コマンド経由**
   - `cursor`コマンドが利用可能か
   - サブプロセス経由で呼び出せるか

#### 3.2 **重要: `codebase_search`の出力形式の確認（未確認）**

**現状の問題点**:
- `codebase_search`の実際の出力形式が不明
- 順序が関連性順であるという根拠がない
- スコア情報が含まれているかどうか不明

**確認が必要な項目**:

1. **出力形式の確認**
   ```python
   # 実際の出力形式を確認するテストコード
   search_results = codebase_search_func(query="test query")
   print(f"出力の型: {type(search_results)}")
   print(f"出力の内容: {search_results}")
   print(f"最初の要素の型: {type(search_results[0]) if search_results else None}")
   print(f"最初の要素の内容: {search_results[0] if search_results else None}")
   ```

2. **順序の意味の確認**
   - 検索結果の順序が関連性順であるかどうか
   - 順序がランダムまたは別の基準（例: ファイル名順、更新日順）の可能性
   - 順序が関連性順でない場合、別の方法で関連性を判断する必要がある

3. **スコア情報の有無**
   - 検索結果に類似度スコアが含まれているか
   - スコアが含まれている場合、その形式（`score`, `relevance`, `similarity`など）
   - スコアが含まれていない場合、順位から推測する必要がある

**実装時の対応方針**:

- **ケース1: 順序が関連性順で、スコア情報がある場合**
  ```python
  # スコア情報を使用
  semantic_score = result.get("score", 0.0)
  ```

- **ケース2: 順序が関連性順だが、スコア情報がない場合**
  ```python
  # 順位からスコアを推測（逆数方式など）
  semantic_score = 1.0 / (index + 1)
  ```

- **ケース3: 順序が関連性順でない場合**
  ```python
  # 順序を無視し、すべての結果を同等に扱う
  # または、別の方法で関連性を判断する必要がある
  semantic_score = 0.5  # 固定値
  ```

**実装前の必須ステップ**:
1. 実際に`codebase_search`を呼び出して出力形式を確認
2. 複数のクエリで順序の一貫性を確認
3. スコア情報の有無を確認
4. 確認結果に基づいて実装方針を決定

#### 3.2 実装案（調査後）

```python
def get_codebase_search_function():
    """
    Cursorのcodebase_search関数を取得
    
    Returns:
        codebase_search関数、またはNone（取得できない場合）
    """
    # 方法1: モジュールからインポート
    try:
        from cursor import codebase_search
        return codebase_search
    except ImportError:
        pass
    
    # 方法2: 環境変数から取得
    import os
    cursor_search_path = os.getenv("CURSOR_CODEBASE_SEARCH")
    if cursor_search_path:
        # 外部モジュールとして読み込む
        pass
    
    # 方法3: 外部コマンド経由
    # subprocess経由でcursorコマンドを呼び出す
    # （実装は調査後）
    
    return None
```

### フェーズ4: エラーハンドリングとフォールバック

#### 4.1 エラーハンドリング

- セマンティック検索の実行中にエラーが発生した場合
- 検索結果が空の場合
- 検索結果のファイルが`all_contents`に存在しない場合

**実装**:
```python
try:
    file_paths = get_relevant_files_for_cell(...)
    if not file_paths:
        logger.warning("セマンティック検索でファイルが見つかりませんでした")
        # フォールバック
        relevant_files.update(all_contents)
except Exception as e:
    logger.error(f"セマンティック検索中にエラー: {e}")
    # フォールバック
    relevant_files.update(all_contents)
```

#### 4.2 ログ出力

- セマンティック検索が実行された場合
- フォールバックが使用された場合
- 検索結果のファイル数

### フェーズ5: テストと検証

#### 5.1 テストケース

1. **正常系**
   - `codebase_search_func`が提供された場合
   - 検索結果からファイルが正しく抽出される
   - `all_contents`から該当ファイルが取得される

2. **フォールバック**
   - `codebase_search_func`が`None`の場合
   - 検索結果が空の場合
   - エラーが発生した場合

3. **統合テスト**
   - 実際のプロンプト生成で動作確認
   - 複数のセルで異なる検索結果が得られるか

#### 5.2 検証項目

- セルごとに異なる関連ファイルが選択されるか
- 検索結果の精度が向上しているか
- フォールバックが正しく動作するか
- パフォーマンスへの影響

## 実装の優先順位

### 優先度: 高
1. `prompt_generator.py`の`_get_relevant_files()`を「外部入力候補（セル別）＋再ランキング＋上位N」対応に修正
2. `generate_portfolio_v2.py` に `--semantic-search-results` を追加し、`generate_prompts()`へ渡す
3. フォールバック戦略（未指定/該当セルなし/空）の実装

### 優先度: 中
4. JSONスキーマ拡張（`{path, rank}` 等）とログの整備
5. エラーハンドリングの強化

### 優先度: 低
6. パフォーマンス最適化
7. キャッシュ機能の追加

## 実装時の注意点

1. **後方互換性**
   - `codebase_search_func`が`None`の場合、既存の動作（全ファイルを含める）を維持
   - 既存の設定ファイルがそのまま動作する

2. **パフォーマンス**
   - セマンティック検索は時間がかかる可能性がある
   - 必要に応じてキャッシュを検討

3. **ログ出力**
   - デバッグ時に検索クエリと結果を確認できるように
   - フォールバックが使用された場合もログに記録

## 次のステップ

1. **`codebase_search`関数の取得方法の調査**
   - Cursorのドキュメントを確認
   - 実際に呼び出し可能かテスト

2. **最小実装の作成**
   - フォールバック付きで基本実装
   - 動作確認

3. **段階的な改善**
   - 検索精度の向上
   - パフォーマンス最適化

## 優先度・重み付けの改善案（将来の拡張）

### 改善案の概要

セマンティック検索の結果とファイル重要度スコアを組み合わせて、より精度の高いファイル選択を実現する。

### 改善案の詳細

#### 1. 2つのスコアの組み合わせ

**1.1 セマンティック検索スコア（Semantic Relevance Score）**
- **目的**: セルの説明との意味的関連性を表す
- **計算方法**: 
  - 検索結果にスコアが含まれている場合: そのスコアを使用
  - スコアが含まれていない場合: 順位から推測（**注意: 順序が関連性順であることを確認する必要がある**）
    ```python
    # 順位ベースのスコア（逆数方式）
    semantic_score = 1.0 / (index + 1)  # 1位: 1.0, 2位: 0.5, 3位: 0.33, ...
    ```

**1.2 ファイル重要度スコア（File Importance Score）**
- **目的**: ファイル自体の重要度を表す（既存の`calculate_file_importance()`を使用）
- **計算方法**: ファイル名、ディレクトリ位置、ファイルサイズから算出（0.0-1.0）

#### 2. 統合スコアの計算

```python
def calculate_combined_score(
    semantic_score: float,
    importance_score: float,
    semantic_weight: float = 0.7,
    importance_weight: float = 0.3,
) -> float:
    """
    セマンティック検索スコアとファイル重要度スコアを組み合わせ
    
    Args:
        semantic_score: セマンティック検索の関連性スコア（0.0-1.0）
        importance_score: ファイル重要度スコア（0.0-1.0）
        semantic_weight: セマンティック検索スコアの重み（デフォルト: 0.7）
        importance_weight: ファイル重要度スコアの重み（デフォルト: 0.3）
    
    Returns:
        統合スコア（0.0-1.0）
    """
    combined = (semantic_weight * semantic_score) + (importance_weight * importance_score)
    return max(0.0, min(1.0, combined))
```

#### 3. 実装前の注意点

**重要**: この改善案を実装する前に、以下を確認する必要がある：

1. **`codebase_search`の出力形式の確認**
   - 順序が関連性順であることを確認
   - スコア情報が含まれているかどうかを確認

2. **順序が関連性順でない場合の対応**
   - 順序を無視し、すべての結果を同等に扱う
   - または、別の方法で関連性を判断する

3. **実装の優先順位**
   - まず基本実装（フェーズ1-5）を完了
   - その後、出力形式を確認してから改善案を実装

### 実装の優先順位（改善案）

- **優先度: 低**（基本実装完了後）
  1. `codebase_search`の出力形式の確認
  2. 順序の意味の確認
  3. スコア情報の有無の確認
  4. 確認結果に基づく改善案の実装

### 推奨実装方針（実務向け）

結論として、**B（順位擬似スコア） + C（自前再ランキング）**のハイブリッドを推奨します。

#### 1) `codebase_search`結果の扱い（スコアがあれば使う／なければ順位で擬似スコア）

- Cursorは **数値スコア（similarity / relevance）を表に出さない**可能性が高く、また**順序が関連度順である保証も公開されていない**想定で設計します。
- ただし実務上は“関連度順っぽい並び”が多いので、**順序は「参考情報」**としてのみ利用し、最終決定は自前スコアで行います。

```python
# まず「実スコアが来るなら使う」
if isinstance(result, dict) and ("score" in result or "relevance" in result or "similarity" in result):
    semantic_score = float(result.get("score") or result.get("relevance") or result.get("similarity"))
else:
    # 順位から擬似スコア（例: 指数減衰）
    # rank=0が最上位
    semantic_score = exp(-alpha * rank)

# 代替（より単純）
# semantic_score = 1.0 / (rank + 1)
```

- **推奨**: 指数減衰（上位重視）
  - 例: `alpha = 0.7` 〜 `1.0`（初期値は0.8くらい）

#### 2) 既存のファイル重要度（ルール）と統合して再ランキング

- 本プロジェクトには `calculate_file_importance()`（0〜1）があるので、これと統合します。

```python
final_score = (w_rank * semantic_score) + (w_rule * file_importance)
```

- **推奨初期値**（README/ARCHITECTURE優遇を強めたい用途向け）
  - `w_rank = 0.4`
  - `w_rule = 0.6`

#### 3) LLMに渡すファイル数はトップNに制限

- **推奨**: `N = 5〜8`
  - Excelセルの説明→要約生成用途では、
    - README/ARCHITECTURE 等の上位ドキュメント
    - 実装の主要ファイル1〜2
    が入る程度が実務的に安定しやすいです。

#### 4) ログ（必須）: 仕様変更や品質劣化を検知できるようにする

- **出力先例**: `.cursor/semantic_search_debug.jsonl`（1検索=1行で追記）
- **記録フィールド例**:

```json
{"query":"...","rank":2,"rank_score":0.37,"file_importance":0.82,"final_score":0.63,"path":"src/portfolio/file_discovery.py"}
```

- これにより、
  - Cursor側のランキング挙動の変化
  - 検索結果の劣化
  を後から追跡できます。

#### 5) 設計Tips（壊れにくさ重視）

- **スコアが来たら使う分岐を先に用意**（将来の仕様変更に強い）
- `codebase_search_func` は **ブラックボックス扱い**にし、最終的な採否は `final_score` で決める
- 可能なら **同一クエリの結果をキャッシュ**（性能と再現性のため）

### 実装反映ポイント（どこを直すか）

- `src/portfolio/semantic_search.py`
  - `extract_files_from_search_results()` を「パス一覧」だけでなく、
    - **(path, rank, semantic_score?)** を保持できる形に拡張
- `src/portfolio/prompt_generator.py`
  - 取得候補を `calculate_file_importance()` と統合して **再ランキング**
  - 上位Nだけを最終コンテキストに採用
- ログ出力
  - `.cursor/semantic_search_debug.jsonl` を追記（オプションで有効化してもよい）

## 参考情報

- `src/portfolio/semantic_search.py`: セマンティック検索のインターフェース
- `src/portfolio/prompt_generator.py`: プロンプト生成の実装
- `src/portfolio/generate_portfolio_v2.py`: メインスクリプト
- `src/portfolio/file_discovery.py`: ファイル重要度スコアの計算
