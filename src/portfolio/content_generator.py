"""
ポートフォリオ自動生成システムの内容生成モジュール
AIによる文脈理解と文章生成、変換ルールの適用
"""

import logging
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ContentGenerationError(Exception):
    """内容生成エラー"""

    pass


class TextTransformer:
    """テキスト変換ルールを適用するクラス"""

    @staticmethod
    def summarize_to_length(
        text: str, max_chars: int = 500, min_chars: int = 200
    ) -> str:
        """
        指定された文字数に要約する

        Args:
            text: 元のテキスト
            max_chars: 最大文字数
            min_chars: 最小文字数（オプション）

        Returns:
            要約されたテキスト
        """
        if len(text) <= max_chars:
            return text

        # 段落単位で切り詰める
        paragraphs = text.split("\n\n")
        result = []
        current_length = 0

        for para in paragraphs:
            para_length = len(para)
            if current_length + para_length + 2 <= max_chars:  # +2は改行文字
                result.append(para)
                current_length += para_length + 2
            else:
                # 最後の段落を部分切り詰め
                remaining = max_chars - current_length - 2
                if remaining > min_chars // 2:
                    result.append(para[:remaining] + "...")
                break

        summary = "\n\n".join(result)

        # 最小文字数未満の場合は最初の部分を返す
        if len(summary) < min_chars:
            summary = text[:max_chars] + "..." if len(text) > max_chars else text

        return summary

    @staticmethod
    def first_paragraph(text: str, max_chars: int = 50) -> str:
        """
        最初の段落を抽出

        Args:
            text: 元のテキスト
            max_chars: 最大文字数

        Returns:
            最初の段落（指定文字数まで）
        """
        # 段落を分割
        paragraphs = text.split("\n\n")
        if paragraphs:
            first_para = paragraphs[0].strip()

            # 文字数制限
            if len(first_para) > max_chars:
                # 文の区切りで切り詰め
                sentences = re.split(r"[。．\.\n]", first_para)
                result = ""
                for sentence in sentences:
                    if len(result) + len(sentence) <= max_chars:
                        result += sentence + "。"
                    else:
                        break
                return result[:max_chars] if result else first_para[:max_chars]

            return first_para

        return text[:max_chars] if len(text) > max_chars else text

    @staticmethod
    def date_format(date_str: str, format_str: str = "%Y年/%m月/%d日") -> str:
        """
        日付を指定形式に変換

        Args:
            date_str: 日付文字列（ISO形式など）
            format_str: 変換後の形式

        Returns:
            フォーマットされた日付文字列
        """
        try:
            # 様々な形式に対応
            formats_to_try = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
            ]

            dt = None
            for fmt in formats_to_try:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue

            if dt is None:
                logger.warning(f"日付形式が解析できませんでした: {date_str}")
                return date_str

            return dt.strftime(format_str)

        except Exception as e:
            logger.error(f"日付変換エラー: {date_str}, {e}")
            return date_str

    @staticmethod
    def extract_technologies(text: str, exclude_list: list[str] | None = None) -> str:
        """
        技術リストを抽出（requirements.txtなどから）

        Args:
            text: テキスト（requirements.txtの内容など）
            exclude_list: 除外する技術名のリスト

        Returns:
            カンマ区切りの技術リスト
        """
        if exclude_list is None:
            exclude_list = ["pytest", "pytest-cov", "ruff", "black", "mypy"]

        technologies: list[str] = []

        # requirements.txt形式から技術を抽出
        for line in text.splitlines():
            line = line.strip()

            # コメント行をスキップ
            if line.startswith("#") or not line:
                continue

            # パッケージ名を抽出（例: "package>=1.0" -> "package"）
            package = (
                line.split(">=")[0].split("==")[0].split("<")[0].split("~")[0].strip()
            )

            # 除外リストに含まれていない場合のみ追加
            if package and package.lower() not in [e.lower() for e in exclude_list]:
                technologies.append(package)

        return ", ".join(technologies)


class ContentGenerator:
    """内容生成を管理するクラス"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        内容生成器を初期化

        Args:
            config: 設定辞書（オプション）
        """
        self.config = config or {}
        self.transformer = TextTransformer()

    def generate_content(
        self,
        cell_description: str,
        codebase_context: dict[str, str],
        transform: str | None = None,
        max_chars: int | None = None,
    ) -> str:
        """
        セルの内容を生成

        Args:
            cell_description: セルの説明
            codebase_context: コードベースのコンテキスト（ファイルパス -> 内容）
            transform: 変換ルール名（オプション）
            max_chars: 最大文字数（オプション）

        Returns:
            生成された内容
        """
        # コードベースから関連情報を抽出
        # 実際のAIによる生成はCursorの機能を使用
        # ここでは基本的な要約のみを提供

        # すべてのファイル内容を結合
        all_content = "\n\n".join(
            [f"=== {path} ===\n{content}" for path, content in codebase_context.items()]
        )

        # 変換ルールの適用
        if transform == "summarize_to_length":
            max_len = max_chars or 500
            return self.transformer.summarize_to_length(all_content, max_len)

        elif transform == "first_paragraph":
            max_len = max_chars or 50
            return self.transformer.first_paragraph(all_content, max_len)

        elif transform == "extract_technologies":
            exclude = (
                self.config.get("text_transforms", {})
                .get("extract_technologies", {})
                .get("exclude", [])
            )
            return self.transformer.extract_technologies(all_content, exclude)

        # デフォルト: 最初の段落を返す
        return self.transformer.first_paragraph(all_content, max_chars or 50)

    def apply_transform(
        self,
        text: str,
        transform_name: str,
        transform_config: dict[str, Any] | None = None,
    ) -> str:
        """
        変換ルールを適用

        Args:
            text: 変換対象のテキスト
            transform_name: 変換ルール名
            transform_config: 変換ルールの設定

        Returns:
            変換後のテキスト
        """
        transform_config = transform_config or {}

        if transform_name == "summarize_to_length":
            max_chars = transform_config.get("max_chars", 500)
            min_chars = transform_config.get("min_chars", 200)
            return self.transformer.summarize_to_length(text, max_chars, min_chars)

        elif transform_name == "first_paragraph":
            max_chars = transform_config.get("max_chars", 50)
            return self.transformer.first_paragraph(text, max_chars)

        elif transform_name == "date_format":
            format_str = transform_config.get("format", "%Y年/%m月/%d日")
            return self.transformer.date_format(text, format_str)

        elif transform_name == "extract_technologies":
            exclude = transform_config.get("exclude", [])
            return self.transformer.extract_technologies(text, exclude)

        # 未定義の変換ルールはそのまま返す
        logger.warning(f"未定義の変換ルール: {transform_name}")
        return text
