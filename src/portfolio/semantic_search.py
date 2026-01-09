"""
ポートフォリオ自動生成システムのセマンティック検索インターフェース
実際の検索はCursorのcodebase_searchツールを使用（このモジュールはインターフェースのみ）
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SemanticSearchInterface:
    """
    セマンティック検索のインターフェースクラス

    実際の検索はCursorのcodebase_searchツールを使用するため、
    このクラスは検索クエリの生成と結果の解析を提供します。
    """

    @staticmethod
    def generate_search_query(
        cell_description: str, excel_instruction: str = ""
    ) -> str:
        """
        セル説明とエクセル指示から検索クエリを生成

        Args:
            cell_description: セルの説明（設定ファイルのdescriptionフィールド）
            excel_instruction: エクセルの指示（オプション）

        Returns:
            検索クエリ文字列
        """
        if excel_instruction:
            query = f"{excel_instruction} {cell_description}"
        else:
            query = cell_description

        logger.debug(f"検索クエリを生成しました: {query}")
        return query

    @staticmethod
    def format_query_for_codebase_search(
        cell_description: str, context: str = ""
    ) -> str:
        """
        Cursorのcodebase_search用にクエリをフォーマット

        Args:
            cell_description: セルの説明
            context: 追加のコンテキスト情報

        Returns:
            フォーマットされた検索クエリ
        """
        # 質問形式のクエリに変換
        query_parts = []

        if context:
            query_parts.append(context)

        # セル説明から検索に適した形式に変換
        query_parts.append(f"How is {cell_description} implemented or described?")

        query = " ".join(query_parts)
        logger.debug(f"codebase_search用クエリ: {query}")
        return query

    @staticmethod
    def extract_files_from_search_results(
        search_results: list[dict[str, Any]] | None,
    ) -> list[str]:
        """
        セマンティック検索の結果からファイルパスを抽出

        Args:
            search_results: 検索結果（Cursorのcodebase_searchの形式を想定）

        Returns:
            ファイルパスのリスト
        """
        if not search_results:
            logger.debug("検索結果が空です")
            return []

        file_paths: list[str] = []
        seen_files: set[str] = set()

        # 検索結果からファイルパスを抽出
        # 実際の形式はCursorのcodebase_searchの出力に依存
        for result in search_results:
            # 複数の形式に対応
            file_path = None

            if isinstance(result, dict):
                # 辞書形式の場合
                file_path = (
                    result.get("file") or result.get("path") or result.get("filepath")
                )
            elif isinstance(result, str):
                # 文字列形式の場合
                file_path = result

            if file_path and file_path not in seen_files:
                file_paths.append(file_path)
                seen_files.add(file_path)

        logger.debug(f"検索結果から {len(file_paths)} ファイルを抽出しました")
        return file_paths


def get_relevant_files_for_cell(
    cell_description: str,
    excel_instruction: str = "",
    codebase_search_func: Any = None,
    target_directories: list[str] | None = None,
) -> list[str]:
    """
    エクセルセルの解説に基づいて、関連ファイルを動的に特定

    Args:
        cell_description: セルの説明
        excel_instruction: エクセルの指示（オプション）
        codebase_search_func: セマンティック検索関数（Cursorのcodebase_searchなど）
        target_directories: 検索対象のディレクトリ（Noneの場合は全体）

    Returns:
        関連ファイルのパスリスト
    """
    interface = SemanticSearchInterface()

    # 検索クエリを生成
    query = interface.format_query_for_codebase_search(
        cell_description, excel_instruction
    )

    # セマンティック検索を実行（Cursorの機能を使用）
    if codebase_search_func is None:
        logger.warning(
            "codebase_search_funcが提供されていません。"
            "空のリストを返します。実際の使用時にはCursorのcodebase_searchを使用してください。"
        )
        return []

    try:
        search_results = codebase_search_func(
            query=query,
            target_directories=target_directories or [],
        )

        # 検索結果からファイルパスを抽出
        file_paths = interface.extract_files_from_search_results(search_results)

        return file_paths

    except Exception as e:
        logger.error(f"セマンティック検索中にエラーが発生しました: {e}")
        return []
