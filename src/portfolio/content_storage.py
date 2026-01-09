"""
ポートフォリオ自動生成システムの内容保存・読み込みモジュール
生成された内容をJSONファイルに保存・読み込み
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ContentStorageError(Exception):
    """内容保存エラー"""

    pass


class ContentStorage:
    """生成された内容をJSONファイルに保存・読み込みするクラス"""

    def __init__(self, json_path: str):
        """
        内容ストレージを初期化

        Args:
            json_path: JSONファイルのパス
        """
        self.json_path = os.path.abspath(json_path)
        self.data: dict[str, Any] = {}

    def load(self) -> dict[str, str | int | float]:
        """
        JSONファイルから内容を読み込む

        Returns:
            セルアドレスをキー、内容をバリューとする辞書
        """
        if not os.path.exists(self.json_path):
            logger.warning(f"JSONファイルが見つかりません: {self.json_path}")
            return {}

        try:
            with open(self.json_path, encoding="utf-8") as f:
                self.data = json.load(f)

            logger.info(f"JSONファイルを読み込みました: {self.json_path}")

            # cellsセクションから、セルアドレスをキーとする辞書に変換
            cell_data: dict[str, str | int | float] = {}
            cells = self.data.get("cells", {})

            for _cell_name, cell_info in cells.items():
                if isinstance(cell_info, dict):
                    cell_address = cell_info.get("cell", "")
                    content = cell_info.get("content", "")
                    if cell_address:
                        cell_data[cell_address] = content

            logger.info(f"{len(cell_data)} 個のセルデータを読み込みました")
            return cell_data

        except json.JSONDecodeError as e:
            raise ContentStorageError(
                f"JSONファイルの形式が不正です: {self.json_path}, エラー: {e}"
            ) from e
        except Exception as e:
            raise ContentStorageError(
                f"JSONファイルの読み込みに失敗しました: {self.json_path}, エラー: {e}"
            ) from e

    def save_cell(self, cell_name: str, cell_address: str, content: str) -> None:
        """
        単一セルの内容をJSONファイルに保存（既存の内容を更新）

        Args:
            cell_name: セル名（例: "背景", "目的"）
            cell_address: セルアドレス（例: "D9"）
            content: 生成された内容
        """
        # 既存のデータを読み込む（存在する場合）
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

        # cellsセクションを初期化（存在しない場合）
        if "cells" not in self.data:
            self.data["cells"] = {}

        # セル情報を更新
        self.data["cells"][cell_name] = {
            "cell": cell_address,
            "content": content,
            "generated_by": "cursor-ai",
            "generated_at": datetime.now().isoformat(),
        }

        # メタデータを更新
        self.data["generated_at"] = datetime.now().isoformat()
        self.data["version"] = "2.0"

        # ファイルに保存
        self._save()

    def save_all(self, cell_data: dict[str, dict[str, str]]) -> None:
        """
        複数セルの内容を一括でJSONファイルに保存

        Args:
            cell_data: セル名をキー、{"cell": "D9", "content": "..."} をバリューとする辞書
        """
        # 既存のデータを読み込む（存在する場合）
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

        # cellsセクションを初期化（存在しない場合）
        if "cells" not in self.data:
            self.data["cells"] = {}

        # すべてのセル情報を更新
        for cell_name, cell_info in cell_data.items():
            cell_address = cell_info.get("cell", "")
            content = cell_info.get("content", "")
            if cell_address:
                self.data["cells"][cell_name] = {
                    "cell": cell_address,
                    "content": content,
                    "generated_by": "cursor-ai",
                    "generated_at": datetime.now().isoformat(),
                }

        # メタデータを更新
        self.data["generated_at"] = datetime.now().isoformat()
        self.data["version"] = "2.0"

        # ファイルに保存
        self._save()

    def _save(self) -> None:
        """データをJSONファイルに保存"""
        try:
            # 出力ディレクトリが存在しない場合は作成
            output_dir = os.path.dirname(self.json_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.debug(f"出力ディレクトリを作成しました: {output_dir}")

            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)

            logger.info(f"JSONファイルを保存しました: {self.json_path}")

        except Exception as e:
            raise ContentStorageError(
                f"JSONファイルの保存に失敗しました: {self.json_path}, エラー: {e}"
            ) from e

    def get_cell_content(self, cell_address: str) -> str | None:
        """
        指定されたセルアドレスの内容を取得

        Args:
            cell_address: セルアドレス（例: "D9"）

        Returns:
            内容、見つからない場合はNone
        """
        cells = self.data.get("cells", {})
        for _cell_name, cell_info in cells.items():
            if isinstance(cell_info, dict) and cell_info.get("cell") == cell_address:
                return cell_info.get("content")
        return None


def load_content_from_json(json_path: str) -> dict[str, str | int | float]:
    """
    JSONファイルから内容を読み込む便利関数

    Args:
        json_path: JSONファイルのパス

    Returns:
        セルアドレスをキー、内容をバリューとする辞書
    """
    storage = ContentStorage(json_path)
    return storage.load()
