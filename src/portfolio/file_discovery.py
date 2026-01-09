"""
ポートフォリオ自動生成システムのファイル探索モジュール
パターンマッチングとディレクトリ構造認識による動的なファイル探索
"""

import fnmatch
import logging
import os

logger = logging.getLogger(__name__)


class FileDiscoveryError(Exception):
    """ファイル探索エラー"""

    pass


# ファイル名パターン（優先度順）
DOCUMENTATION_PATTERNS = [
    # プロジェクト概要系（最も優先）
    ("README*", "プロジェクト全体の説明"),
    ("readme*", "プロジェクト全体の説明"),
    ("README.*", "プロジェクト全体の説明"),
    # アーキテクチャ・設計系
    ("ARCHITECTURE*", "システム設計の詳細"),
    ("architecture*", "システム設計の詳細"),
    ("DESIGN*", "システム設計の詳細"),
    ("設計*", "システム設計の詳細"),
    # 変更履歴・ログ系
    ("CHANGELOG*", "変更履歴"),
    ("CHANGES*", "変更履歴"),
    ("HISTORY*", "変更履歴"),
    # 計画・目的系
    ("plan*.json", "タスク計画・目的"),
    ("*.plan.json", "タスク計画・目的"),
    ("ROADMAP*", "開発計画"),
    ("roadmap*", "開発計画"),
    # 技術仕様系
    ("requirements*.txt", "使用技術"),
    ("package.json", "使用技術"),
    ("Pipfile", "使用技術"),
    ("pyproject.toml", "プロジェクト設定"),
]

# 除外するパターン
EXCLUDE_PATTERNS = [
    # 実行ファイル・バイナリ
    "*.exe",
    "*.pyc",
    "__pycache__/**",
    "**/__pycache__/**",
    "build/**",
    "dist/**",
    "*.so",
    "*.dll",
    # ログ・データファイル
    "*.log",
    "data/**",
    "**/data/**",
    # 設定ファイル（一部）
    ".env",
    ".git/**",
    "**/.git/**",
    # テストファイル
    "tests/**",
    "**/tests/**",
    "test_*.py",
    # ドキュメント生成物（旧方式のレポート）
    "docs/reports/*.md",
    # MCP設定
    "mcp_setup/**",
    "**/mcp_setup/**",
    # スクリプト（配布用、CI用）
    "scripts/build-*.ps1",
    "scripts/build-*.sh",
    "scripts/ci-check.*",
]


def should_exclude_file(file_path: str, project_root: str) -> bool:
    """
    ファイルを除外すべきか判定

    Args:
        file_path: ファイルパス（絶対パスまたは相対パス）
        project_root: プロジェクトルートディレクトリ

    Returns:
        除外すべき場合はTrue
    """
    # プロジェクトルートからの相対パスに変換
    try:
        abs_file_path = os.path.abspath(file_path)
        abs_project_root = os.path.abspath(project_root)
        relative_path = os.path.relpath(abs_file_path, abs_project_root)
    except ValueError:
        # 相対パスに変換できない場合（別ドライブなど）は除外しない
        return False

    # 正規化（パスセパレータを統一）
    normalized_path = relative_path.replace("\\", "/")

    # 除外パターンとマッチするかチェック
    for pattern in EXCLUDE_PATTERNS:
        # globパターンマッチング
        if fnmatch.fnmatch(normalized_path, pattern) or fnmatch.fnmatch(
            os.path.basename(normalized_path), pattern
        ):
            return True

    # ディレクトリ名もチェック
    path_parts = normalized_path.split("/")
    for part in path_parts:
        for pattern in EXCLUDE_PATTERNS:
            if fnmatch.fnmatch(part, pattern):
                return True

    return False


def find_files_by_pattern(
    project_root: str, pattern: str, description: str = ""
) -> list[str]:
    """
    パターンに一致するファイルを探索

    Args:
        project_root: プロジェクトルートディレクトリ
        pattern: ファイル名パターン（ワイルドカード対応）
        description: パターンの説明（ログ用）

    Returns:
        見つかったファイルのパスリスト（絶対パス）
    """
    found_files: list[str] = []
    project_root = os.path.abspath(project_root)

    try:
        for root, dirs, files in os.walk(project_root):
            # 除外すべきディレクトリをスキップ
            dirs[:] = [
                d
                for d in dirs
                if not should_exclude_file(os.path.join(root, d), project_root)
            ]

            for file in files:
                file_path = os.path.join(root, file)

                # 除外チェック
                if should_exclude_file(file_path, project_root):
                    continue

                # パターンマッチング
                if fnmatch.fnmatch(file, pattern):
                    found_files.append(os.path.abspath(file_path))

    except Exception as e:
        logger.error(f"ファイル探索中にエラーが発生しました: {e}")
        raise FileDiscoveryError(f"ファイル探索エラー: {e}") from e

    if description:
        logger.debug(
            f"パターン '{pattern}' ({description}) で {len(found_files)} ファイルを発見"
        )

    return found_files


def discover_documentation_files(project_root: str) -> list[str]:
    """
    ドキュメントファイルを探索

    Args:
        project_root: プロジェクトルートディレクトリ

    Returns:
        見つかったドキュメントファイルのパスリスト（優先度順）
    """
    all_files: list[str] = []
    seen_files: set[str] = set()

    # 各パターンで探索
    for pattern, description in DOCUMENTATION_PATTERNS:
        files = find_files_by_pattern(project_root, pattern, description)
        for file_path in files:
            if file_path not in seen_files:
                all_files.append(file_path)
                seen_files.add(file_path)

    return all_files


def discover_project_structure(project_root: str) -> dict[str, list[str]]:
    """
    プロジェクトのディレクトリ構造を自動認識

    Args:
        project_root: プロジェクトルートディレクトリ

    Returns:
        構造情報を含む辞書:
        {
            "documentation_dirs": [...],
            "source_dirs": [...],
            "config_files": [...],
            "main_entry_points": [...]
        }
    """
    project_root = os.path.abspath(project_root)
    structure: dict[str, list[str]] = {
        "documentation_dirs": [],
        "source_dirs": [],
        "config_files": [],
        "main_entry_points": [],
    }

    if not os.path.exists(project_root):
        logger.warning(f"プロジェクトルートが存在しません: {project_root}")
        return structure

    try:
        # ルートディレクトリの内容を取得
        for item in os.listdir(project_root):
            item_path = os.path.join(project_root, item)

            # 除外チェック
            if should_exclude_file(item_path, project_root):
                continue

            # ディレクトリチェック
            if os.path.isdir(item_path):
                item_lower = item.lower()

                # ドキュメントディレクトリ
                if any(
                    keyword in item_lower
                    for keyword in ["doc", "readme", "spec", "design", "docs"]
                ):
                    structure["documentation_dirs"].append(item_path)

                # ソースコードディレクトリ
                if item_lower in ["src", "lib", "app", "source", "main"]:
                    structure["source_dirs"].append(item_path)

            # ファイルチェック
            elif os.path.isfile(item_path):
                item_lower = item.lower()

                # 設定ファイル
                if any(
                    item_lower.endswith(ext)
                    for ext in [".json", ".yaml", ".yml", ".toml", ".ini"]
                ):
                    if item_lower not in ["package.json", "pyproject.toml"]:
                        structure["config_files"].append(item_path)

                # メインエントリーポイント
                if item_lower in ["main.py", "index.py", "app.py", "__main__.py"]:
                    structure["main_entry_points"].append(item_path)

        # 共通のソースコードディレクトリもチェック
        common_source_dirs = ["src", "lib", "app", "source", "main"]
        for dir_name in common_source_dirs:
            dir_path = os.path.join(project_root, dir_name)
            if (
                os.path.exists(dir_path)
                and os.path.isdir(dir_path)
                and dir_path not in structure["source_dirs"]
            ):
                structure["source_dirs"].append(dir_path)

    except Exception as e:
        logger.error(f"プロジェクト構造の認識中にエラーが発生しました: {e}")
        raise FileDiscoveryError(f"プロジェクト構造認識エラー: {e}") from e

    logger.debug(
        f"プロジェクト構造を認識しました: "
        f"ドキュメントディレクトリ={len(structure['documentation_dirs'])}, "
        f"ソースディレクトリ={len(structure['source_dirs'])}, "
        f"設定ファイル={len(structure['config_files'])}, "
        f"メインエントリーポイント={len(structure['main_entry_points'])}"
    )

    return structure


def calculate_file_importance(
    file_path: str,
    project_root: str,
    cell_description: str = "",
    excel_instruction: str = "",
) -> float:
    """
    ファイルの重要度をスコアリング（0.0-1.0）

    Args:
        file_path: ファイルパス
        project_root: プロジェクトルートディレクトリ
        cell_description: セルの説明（オプション、将来の拡張用）
        excel_instruction: エクセルの指示（オプション、将来の拡張用）

    Returns:
        重要度スコア（0.0-1.0）
    """
    score = 0.0
    project_root = os.path.abspath(project_root)

    try:
        # 1. ファイル名の重要度
        filename = os.path.basename(file_path).lower()

        # ドキュメントファイルは高スコア
        if any(
            keyword in filename
            for keyword in ["readme", "architecture", "design", "changelog"]
        ):
            score += 0.4

        # メインファイルは高スコア
        if any(keyword in filename for keyword in ["main", "index", "app"]):
            score += 0.3

        # 2. ディレクトリ位置の重要度
        try:
            rel_path = os.path.relpath(file_path, project_root)
            # ルート直下または浅い階層は重要
            depth = len(rel_path.split(os.sep))
            if depth <= 2:  # ルート直下または1階層下
                score += 0.2
        except ValueError:
            # 相対パスに変換できない場合はスキップ
            pass

        # 3. ファイルサイズ（適度なサイズが良い）
        try:
            size = os.path.getsize(file_path)
            if 1000 < size < 100000:  # 1KB-100KB
                score += 0.1
            elif size > 1000000:  # 1MB以上は低スコア
                score -= 0.1
        except OSError:
            # ファイルサイズ取得失敗はスキップ
            pass

    except Exception as e:
        logger.warning(
            f"ファイル重要度の計算中にエラーが発生しました: {file_path}, {e}"
        )

    return max(0.0, min(score, 1.0))


def get_prioritized_files(
    file_list: list[str], project_root: str, max_files: int = 10
) -> list[str]:
    """
    ファイルリストを重要度順にソートして返す

    Args:
        file_list: ファイルパスのリスト
        project_root: プロジェクトルートディレクトリ
        max_files: 返す最大ファイル数

    Returns:
        重要度順にソートされたファイルリスト
    """
    file_scores: list[tuple[str, float]] = []

    for file_path in file_list:
        score = calculate_file_importance(file_path, project_root)
        file_scores.append((file_path, score))

    # スコア順にソート（降順）
    file_scores.sort(key=lambda x: x[1], reverse=True)

    # 上位Nファイルを返す
    return [file_path for file_path, _ in file_scores[:max_files]]
