"""
ポートフォリオ自動生成システムのコードベース読み込みモジュール
ファイルリストを受け取り、順次読み込んでコンテキスト情報を構築
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# 読み込むファイルの最大サイズ（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024


class CodebaseReadError(Exception):
    """コードベース読み込みエラー"""

    pass


class CodebaseContext:
    """コードベースのコンテキスト情報を保持するクラス"""

    def __init__(self):
        """コンテキストを初期化"""
        self.files: dict[str, str] = {}  # ファイルパス -> ファイル内容
        self.metadata: dict[str, dict[str, Any]] = {}  # ファイルパス -> メタデータ

    def add_file(
        self, file_path: str, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """
        ファイルをコンテキストに追加

        Args:
            file_path: ファイルパス
            content: ファイル内容
            metadata: メタデータ（ファイルサイズ、行数など）
        """
        self.files[file_path] = content
        self.metadata[file_path] = metadata or {}

    def get_content(self, file_path: str) -> str | None:
        """
        指定されたファイルの内容を取得

        Args:
            file_path: ファイルパス

        Returns:
            ファイル内容、存在しない場合はNone
        """
        return self.files.get(file_path)

    def get_all_contents(self) -> dict[str, str]:
        """
        すべてのファイル内容を取得

        Returns:
            ファイルパスをキー、内容をバリューとする辞書
        """
        return self.files.copy()

    def get_summary(self) -> dict[str, Any]:
        """
        コンテキストのサマリーを取得

        Returns:
            サマリー情報
        """
        return {
            "total_files": len(self.files),
            "total_size": sum(
                self.metadata.get(path, {}).get("size", 0) for path in self.files
            ),
            "files": list(self.files.keys()),
        }


def read_file_content(
    file_path: str, max_size: int = MAX_FILE_SIZE
) -> tuple[str, dict[str, Any]]:
    """
    ファイルの内容を読み込む

    Args:
        file_path: ファイルパス
        max_size: 読み込む最大サイズ（バイト）

    Returns:
        (ファイル内容, メタデータ)のタプル

    Raises:
        CodebaseReadError: ファイルの読み込みに失敗した場合
    """
    if not os.path.exists(file_path):
        raise CodebaseReadError(f"ファイルが存在しません: {file_path}")

    try:
        # ファイルサイズをチェック
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            logger.warning(
                f"ファイルサイズが大きすぎます（{file_size}バイト）。"
                f"最大サイズ（{max_size}バイト）を超えています: {file_path}"
            )
            # ファイルの最初の部分だけを読み込む
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read(max_size)
                logger.info(
                    f"ファイルの最初の{max_size}バイトを読み込みました: {file_path}"
                )
        else:
            # 通常の読み込み
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

        # メタデータを構築
        metadata = {
            "size": file_size,
            "lines": len(content.splitlines()),
            "encoding": "utf-8",
        }

        return content, metadata

    except UnicodeDecodeError as e:
        logger.error(f"ファイルのエンコーディングエラー: {file_path}, {e}")
        raise CodebaseReadError(f"ファイルのエンコーディングエラー: {file_path}") from e
    except PermissionError as e:
        logger.error(f"ファイルの読み込み権限がありません: {file_path}, {e}")
        raise CodebaseReadError(
            f"ファイルの読み込み権限がありません: {file_path}"
        ) from e
    except Exception as e:
        logger.error(f"ファイルの読み込みに失敗しました: {file_path}, {e}")
        raise CodebaseReadError(f"ファイルの読み込みに失敗しました: {file_path}") from e


def build_context_from_files(
    file_list: list[str], project_root: str | None = None
) -> CodebaseContext:
    """
    ファイルリストからコンテキストを構築

    Args:
        file_list: ファイルパスのリスト
        project_root: プロジェクトルートディレクトリ（相対パスの解決用）

    Returns:
        構築されたコンテキスト
    """
    context = CodebaseContext()
    project_root = project_root or os.getcwd()

    for file_path in file_list:
        try:
            # 絶対パスに変換
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(os.path.join(project_root, file_path))

            # ファイルを読み込む
            content, metadata = read_file_content(file_path)

            # コンテキストに追加
            context.add_file(file_path, content, metadata)

            logger.debug(
                f"ファイルをコンテキストに追加しました: {os.path.basename(file_path)}"
            )

        except CodebaseReadError as e:
            logger.warning(
                f"ファイルの読み込みをスキップしました: {file_path}, エラー: {e}"
            )
            # エラーがあっても続行（部分的な失敗を許容）

    logger.info(
        f"コンテキストを構築しました: {len(context.files)}/{len(file_list)} ファイルを読み込み"
    )

    return context


def read_codebase_files(
    file_list: list[str], project_root: str | None = None, max_files: int | None = None
) -> CodebaseContext:
    """
    コードベースファイルを読み込んでコンテキストを構築

    Args:
        file_list: ファイルパスのリスト（重要度順にソートされていることを推奨）
        project_root: プロジェクトルートディレクトリ
        max_files: 読み込む最大ファイル数（Noneの場合はすべて）

    Returns:
        構築されたコンテキスト
    """
    # ファイル数の制限
    if max_files is not None and max_files > 0:
        file_list = file_list[:max_files]
        logger.debug(f"ファイル数を制限しました: 最大{max_files}ファイル")

    return build_context_from_files(file_list, project_root)












