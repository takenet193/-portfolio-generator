"""
ポートフォリオ自動生成システムの設定ファイル読み込みモジュール
"""

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class ConfigLoadError(Exception):
    """設定ファイル読み込みエラー"""

    pass


class PortfolioConfig:
    """ポートフォリオ設定を管理するクラス"""

    def __init__(self, config_path: str | None = None):
        """
        設定ファイルを読み込む

        Args:
            config_path: 設定ファイルのパス（Noneの場合はデフォルトパスを使用）

        Raises:
            ConfigLoadError: 設定ファイルの読み込みに失敗した場合
        """
        if config_path is None:
            # デフォルトパス: プロジェクトルートの.cursor/portfolio_config.json
            base_dir = os.getcwd()
            config_path = os.path.join(base_dir, ".cursor", "portfolio_config.json")

        self.config_path = os.path.abspath(config_path)
        self.config_data: dict[str, Any] = {}

        self._load_config()
        self._validate_config()

    def _load_config(self) -> None:
        """設定ファイルを読み込む"""
        try:
            if not os.path.exists(self.config_path):
                raise ConfigLoadError(
                    f"設定ファイルが見つかりません: {self.config_path}"
                )

            with open(self.config_path, encoding="utf-8") as f:
                self.config_data = json.load(f)

            logger.info(f"設定ファイルを読み込みました: {self.config_path}")

        except json.JSONDecodeError as e:
            raise ConfigLoadError(
                f"設定ファイルのJSON形式が不正です: {self.config_path}, エラー: {e}"
            ) from e
        except Exception as e:
            raise ConfigLoadError(
                f"設定ファイルの読み込みに失敗しました: {self.config_path}, エラー: {e}"
            ) from e

    def _validate_config(self) -> None:
        """設定ファイルの必須フィールドをバリデーション"""
        required_fields = ["version", "excel_template", "cell_mapping"]

        for field in required_fields:
            if field not in self.config_data:
                raise ConfigLoadError(
                    f"設定ファイルに必須フィールド '{field}' が存在しません"
                )

        # excel_templateのバリデーション
        excel_template = self.config_data.get("excel_template", {})
        if not isinstance(excel_template, dict):
            raise ConfigLoadError("excel_templateは辞書型である必要があります")

        if "file" not in excel_template:
            raise ConfigLoadError("excel_templateに'file'フィールドが存在しません")

        # cell_mappingのバリデーション
        cell_mapping = self.config_data.get("cell_mapping", {})
        if not isinstance(cell_mapping, dict):
            raise ConfigLoadError("cell_mappingは辞書型である必要があります")

        logger.debug("設定ファイルのバリデーションが完了しました")

    @property
    def version(self) -> str:
        """設定ファイルのバージョン"""
        return self.config_data.get("version", "1.0")

    @property
    def description(self) -> str:
        """設定ファイルの説明"""
        return self.config_data.get("description", "")

    @property
    def excel_template(self) -> dict[str, Any]:
        """エクセルテンプレート情報"""
        return self.config_data.get("excel_template", {})

    @property
    def excel_template_file(self) -> str:
        """エクセルテンプレートファイル名"""
        return self.excel_template.get("file", "")

    @property
    def excel_template_sheet(self) -> str:
        """エクセルテンプレートのシート名"""
        return self.excel_template.get("sheet", "フォーマット")

    @property
    def cell_mapping(self) -> dict[str, Any]:
        """セルマッピング情報"""
        return self.config_data.get("cell_mapping", {})

    @property
    def data_sources(self) -> dict[str, Any]:
        """データソース設定"""
        return self.config_data.get("data_sources", {})

    @property
    def text_transforms(self) -> dict[str, Any]:
        """テキスト変換ルール"""
        return self.config_data.get("text_transforms", {})

    def get_cell_config(self, cell_name: str) -> dict[str, Any] | None:
        """
        指定されたセル名の設定を取得

        Args:
            cell_name: セル名（例: "背景", "目的"）

        Returns:
            セル設定の辞書、存在しない場合はNone
        """
        return self.cell_mapping.get(cell_name)

    def get_excel_template_path(self, project_root: str | None = None) -> str:
        """
        エクセルテンプレートファイルの絶対パスを取得

        Args:
            project_root: プロジェクトルートディレクトリ（Noneの場合は設定ファイルのディレクトリを使用）

        Returns:
            エクセルテンプレートファイルの絶対パス
        """
        if project_root is None:
            # 設定ファイルと同じディレクトリを基準にする
            project_root = os.path.dirname(os.path.dirname(self.config_path))

        template_file = self.excel_template_file

        # 絶対パスの場合
        if os.path.isabs(template_file):
            return template_file

        # 相対パスの場合
        return os.path.abspath(os.path.join(project_root, template_file))












