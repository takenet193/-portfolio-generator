"""
ポートフォリオ生成システムのユーザー設定（Markdown）読み込みモジュール

docs/portfolio-user-settings.md から以下の情報を読み込むことを想定:
- 共通ルール（全セル共通のトーンなど）
- セル別の最大文字数オーバーライド
- セル別のAIへの追加指示
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CellUserSetting:
    """セル単位のユーザー設定"""

    max_chars: int | None = None
    instructions: list[str] = field(default_factory=list)


@dataclass
class UserSettings:
    """ユーザー設定全体"""

    global_rules: list[str] = field(default_factory=list)
    cell_settings: dict[str, CellUserSetting] = field(default_factory=dict)

    def get_cell_setting(self, cell_name: str) -> CellUserSetting | None:
        """セル名に対応する設定を取得"""
        return self.cell_settings.get(cell_name)


def _parse_max_chars(line: str) -> int | None:
    """
    「最大文字数（デフォルト: 500）: 400」のような行から数値部分を抽出

    数値が見つからない場合は None を返す。
    """
    # 行の中で「最後に出てくる数字」を採用する。
    # 例: "- 最大文字数（デフォルト: 500）: 400" -> 400 を取得したい。
    last_match: re.Match[str] | None = None
    for m in re.finditer(r"(\d+)", line):
        last_match = m

    if not last_match:
        return None

    try:
        return int(last_match.group(1))
    except ValueError:
        return None


def load_user_settings(
    project_root: str, settings_path: str | None = None
) -> UserSettings | None:
    """
    ユーザー設定Markdownを読み込んでパースする

    Args:
        project_root: プロジェクトルートディレクトリ
        settings_path: 明示的に指定された設定ファイルパス
                       None の場合は docs/portfolio-user-settings.md を探索

    Returns:
        UserSettings インスタンス。ファイルが存在しない場合は None。
    """
    if settings_path is None:
        settings_path = os.path.join(project_root, "docs", "portfolio-user-settings.md")

    settings_path = os.path.abspath(settings_path)

    if not os.path.exists(settings_path):
        logger.info(f"ユーザー設定ファイルが見つかりません: {settings_path}")
        return None

    logger.info(f"ユーザー設定ファイルを読み込みます: {settings_path}")

    try:
        with open(settings_path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        logger.warning(f"ユーザー設定ファイルの読み込みに失敗しました: {e}")
        return None

    user_settings = UserSettings()

    in_global_section = False
    in_cells_section = False
    current_cell_name: str | None = None
    in_ai_instructions = False

    for raw_line in lines:
        line = raw_line.rstrip("\n")

        # セクションの開始/終了判定
        if line.startswith("## "):
            header = line[3:].strip()
            in_ai_instructions = False

            if header.startswith("共通ルール"):
                in_global_section = True
                in_cells_section = False
                continue

            if header.startswith("セル別設定"):
                in_cells_section = True
                in_global_section = False
                current_cell_name = None
                continue

        # セル見出し（例: "### 背景 (D9, 結合セル D9:L14)"）
        if in_cells_section and line.startswith("### "):
            in_ai_instructions = False
            title = line[4:].strip()
            # 括弧より前をセル名とみなす
            cell_name = title.split("(", maxsplit=1)[0].strip()
            current_cell_name = cell_name
            if current_cell_name not in user_settings.cell_settings:
                user_settings.cell_settings[current_cell_name] = CellUserSetting()
            continue

        # 共通ルール内の箇条書き
        if in_global_section and line.lstrip().startswith("- "):
            item = line.lstrip()[2:].strip()
            if item:
                user_settings.global_rules.append(item)
            continue

        # セル別設定の中身
        if in_cells_section and current_cell_name:
            cell_setting = user_settings.cell_settings[current_cell_name]

            stripped = line.lstrip()

            # 最大文字数行
            if "最大文字数" in stripped and "デフォルト" in stripped:
                max_chars = _parse_max_chars(stripped)
                if max_chars is not None:
                    cell_setting.max_chars = max_chars
                continue

            # 「AIへの指示」セクションの開始検出
            if "AIへの指示" in stripped:
                in_ai_instructions = True
                continue

            # 「AIへの指示」配下の箇条書き
            if in_ai_instructions and stripped.startswith("- "):
                instr = stripped[2:].strip()
                if instr:
                    cell_setting.instructions.append(instr)
                continue

            # 空行や区切り線でAI指示セクションを終了
            if in_ai_instructions and (not stripped or stripped.startswith("---")):
                in_ai_instructions = False
                continue

    logger.info(
        f"ユーザー設定を読み込みました: 共通ルール {len(user_settings.global_rules)} 件, "
        f"セル別設定 {len(user_settings.cell_settings)} 件"
    )

    return user_settings


