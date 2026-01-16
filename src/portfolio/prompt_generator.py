"""
ポートフォリオ自動生成システムのプロンプトファイル生成モジュール
各セルごとにAI用のプロンプトファイルを生成
"""

import logging
import os
from pathlib import Path
from typing import Any

from .git_history import generate_development_history_markdown
from .user_settings import CellUserSetting, UserSettings, load_user_settings

logger = logging.getLogger(__name__)


class PromptGenerationError(Exception):
    """プロンプト生成エラー"""

    pass


class PromptGenerator:
    """プロンプトファイルを生成するクラス"""

    def __init__(
        self,
        config: Any,
        codebase_context: Any,
        project_root: str,
        user_settings: UserSettings | None = None,
    ):
        """
        プロンプト生成器を初期化

        Args:
            config: PortfolioConfigインスタンス
            codebase_context: CodebaseContextインスタンス
            project_root: プロジェクトルートディレクトリ
            user_settings: ユーザー設定（Markdownから読み込んだもの）
        """
        self.config = config
        self.codebase_context = codebase_context
        self.project_root = project_root
        self.user_settings = user_settings

    def generate_all_prompts(self, output_dir: str) -> list[str]:
        """
        すべてのセルに対してプロンプトファイルを生成

        Args:
            output_dir: プロンプトファイルの出力ディレクトリ

        Returns:
            生成されたプロンプトファイルのパスのリスト
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        generated_files: list[str] = []

        for cell_name, cell_config in self.config.cell_mapping.items():
            try:
                cell_user_setting: CellUserSetting | None = None
                if self.user_settings:
                    cell_user_setting = self.user_settings.get_cell_setting(cell_name)

                prompt_file = self.generate_prompt_for_cell(
                    cell_name,
                    cell_config,
                    output_path,
                    cell_user_setting,
                )
                if prompt_file:
                    generated_files.append(prompt_file)
                    logger.info(f"プロンプトファイルを生成しました: {prompt_file}")
            except Exception as e:
                logger.warning(
                    f"セル '{cell_name}' のプロンプト生成中にエラーが発生しました: {e}"
                )
                continue

        logger.info(f"合計 {len(generated_files)} 個のプロンプトファイルを生成しました")
        return generated_files

    def generate_prompt_for_cell(
        self,
        cell_name: str,
        cell_config: dict[str, Any],
        output_dir: Path,
        cell_user_setting: CellUserSetting | None = None,
    ) -> str | None:
        """
        指定されたセルのプロンプトファイルを生成

        Args:
            cell_name: セル名（例: "背景", "目的"）
            cell_config: セル設定の辞書
            output_dir: 出力ディレクトリ

        Returns:
            生成されたプロンプトファイルのパス、失敗した場合はNone
        """
        cell_address = cell_config.get("cell", "")
        description = cell_config.get("description", "")
        base_max_chars = cell_config.get("max_chars") or cell_config.get(
            "estimated_chars"
        )
        # ユーザー設定による最大文字数のオーバーライド
        user_max_chars = cell_user_setting.max_chars if cell_user_setting else None
        max_chars = user_max_chars or base_max_chars
        transform = cell_config.get("transform")
        codebase_sources = cell_config.get("codebase_sources", [])

        if not cell_address:
            logger.warning(f"セル '{cell_name}' にセルアドレスが設定されていません")
            return None

        # プロンプトファイル名を生成（ファイル名に使えない文字を置換）
        safe_cell_name = (
            cell_name.replace("/", "_").replace("\\", "_").replace(":", "_")
        )
        prompt_filename = f"{safe_cell_name}.md"
        prompt_file_path = output_dir / prompt_filename

        # ユーザー共通ルール・セル別指示を取得
        global_rules: list[str] = []
        cell_instructions: list[str] = []
        if self.user_settings:
            global_rules = self.user_settings.global_rules
            if cell_user_setting:
                cell_instructions = cell_user_setting.instructions

        # プロンプト内容を生成
        prompt_content = self._build_prompt_content(
            cell_name,
            cell_address,
            description,
            max_chars,
            transform,
            codebase_sources,
            global_rules,
            cell_instructions,
        )

        # ファイルに書き込み
        try:
            with open(prompt_file_path, "w", encoding="utf-8") as f:
                f.write(prompt_content)
            return str(prompt_file_path)
        except Exception as e:
            logger.error(
                f"プロンプトファイルの書き込みに失敗しました: {prompt_file_path}, {e}"
            )
            raise PromptGenerationError(
                f"プロンプトファイルの書き込みに失敗: {e}"
            ) from e

    def _build_prompt_content(
        self,
        cell_name: str,
        cell_address: str,
        description: str,
        max_chars: int | None,
        transform: str | None,
        codebase_sources: list[str],
        global_rules: list[str] | None = None,
        cell_instructions: list[str] | None = None,
    ) -> str:
        """
        プロンプト内容を構築

        Args:
            cell_name: セル名
            cell_address: セルアドレス
            description: セルの説明
            max_chars: 最大文字数
            transform: 変換ルール
            codebase_sources: コードベースソースのリスト

        Returns:
            プロンプト内容（Markdown形式）
        """
        lines: list[str] = []

        if global_rules is None:
            global_rules = []
        if cell_instructions is None:
            cell_instructions = []

        # ヘッダー
        lines.append(f"# セル: {cell_name} ({cell_address})")
        lines.append("")
        lines.append("## 説明")
        lines.append(description)
        lines.append("")

        # 文字数制限
        if max_chars:
            lines.append("## 文字数制限")
            lines.append(f"最大: {max_chars}文字")
            lines.append("")

        # ユーザー共通ルール
        if global_rules:
            lines.append("## ユーザー共通ルール（全セル共通）")
            for rule in global_rules:
                lines.append(f"- {rule}")
            lines.append("")

        # セル固有のユーザー指示
        if cell_instructions:
            lines.append("## ユーザーからの追加指示（このセル固有）")
            for instr in cell_instructions:
                lines.append(f"- {instr}")
            lines.append("")

        # 変換ルール
        if transform:
            lines.append("## 変換ルール")
            lines.append(f"`{transform}`")
            lines.append("")

        # コードベースソース
        if codebase_sources:
            lines.append("## 参照すべきコードベースソース")
            for source in codebase_sources:
                lines.append(f"- `{source}`")
            lines.append("")

        # コードベースコンテキスト
        lines.append("## コードベースコンテキスト")
        lines.append("")

        # 関連するファイルの内容を取得
        all_contents = self.codebase_context.get_all_contents()

        # codebase_sourcesに基づいて関連ファイルを抽出
        relevant_files, git_content = self._get_relevant_files(
            codebase_sources, all_contents
        )

        # 関連ファイルの内容を最初に配置
        if relevant_files:
            lines.append("### 関連ファイルの内容")
            lines.append("")
            for file_path, content in relevant_files.items():
                lines.append(f"#### {file_path}")
                lines.append("")
                # 内容が長すぎる場合は最初の部分だけ表示
                if len(content) > 5000:
                    lines.append("```")
                    lines.append(content[:5000])
                    lines.append("...")
                    lines.append("```")
                    lines.append(
                        f"*（ファイルの一部のみ表示。全内容は {len(content)} 文字）*"
                    )
                else:
                    lines.append("```")
                    lines.append(content)
                    lines.append("```")
                lines.append("")

        # Git履歴を最後に配置（補足情報・開発の文脈として）
        if git_content:
            lines.append("### Git開発履歴")
            lines.append("")
            lines.append(git_content)
            lines.append("")

        if not relevant_files and not git_content:
            lines.append("*関連ファイルが見つかりませんでした。*")
            lines.append("")

        # 生成指示
        lines.append("## 生成指示")
        lines.append("")
        
        # 言語設定の取得と反映
        language = self.config.writing_language if hasattr(self.config, 'writing_language') else "ja"
        # 言語の日本語名マッピング（拡張可能、カスタム言語に対応）
        language_names = {
            "ja": "日本語",
            "en": "英語",
            "zh": "中国語",
            "zh-CN": "簡体字中国語",
            "zh-TW": "繁体字中国語",
            "ko": "韓国語",
            "fr": "フランス語",
            "de": "ドイツ語",
            "es": "スペイン語",
            "pt": "ポルトガル語",
            "it": "イタリア語",
            "ru": "ロシア語",
        }
        # 辞書にない場合はそのまま使用（カスタム言語に対応）
        language_name = language_names.get(language.lower(), language)
        
        # トーンとオーディエンスの取得
        tone = self.config.writing_tone if hasattr(self.config, 'writing_tone') else "polite"
        audience = self.config.writing_audience if hasattr(self.config, 'writing_audience') else ""
        
        # 言語指定を追加
        if language.lower() in language_names:
            lines.append(f"**生成言語**: {language_name} ({language})")
        else:
            # カスタム言語の場合はそのまま表示
            lines.append(f"**生成言語**: {language}")
        if tone:
            # トーンの日本語名マッピング（拡張可能）
            tone_names = {
                "polite": "丁寧",
                "casual": "カジュアル",
                "formal": "フォーマル",
                "professional": "プロフェッショナル",
                "friendly": "フレンドリー",
                "technical": "技術的",
                "concise": "簡潔",
                "detailed": "詳細",
                "persuasive": "説得力のある",
                "business": "ビジネス",
                "academic": "学術的",
                "plain": "プレーン（常体）",
            }
            # 辞書にない場合はそのまま使用（カスタムトーンに対応）
            tone_name = tone_names.get(tone.lower(), tone)
            lines.append(f"**文章のトーン**: {tone_name}")
            # plainトーンの場合、常体で書く旨を明示
            if tone.lower() == "plain":
                lines.append("  - 常体（である調）で記述してください。ですます調（敬語）は使用せず、簡潔でシンプルな文体で記述してください。")
        if audience:
            lines.append(f"**ターゲット読者**: {audience}")
        lines.append("")
        
        lines.append(
            "上記の情報を基に、セルの説明に従って適切な内容を生成してください。"
        )
        # 言語指定の指示（日本語以外、またはカスタム言語の場合）
        if language.lower() != "ja":
            if language.lower() in language_names:
                lines.append(f"生成する内容は{language_name}で記述してください。")
            else:
                lines.append(f"生成する内容は{language}で記述してください。")
        lines.append("")
        lines.append(
            "生成した内容を以下のJSON形式で `.cursor/portfolio-generated-content.json` に保存してください。"
        )
        lines.append("")
        lines.append("```json")
        lines.append("{")
        lines.append(f'  "{cell_name}": {{')
        lines.append(f'    "cell": "{cell_address}",')
        lines.append('    "content": "生成した内容をここに記載"')
        lines.append("  }")
        lines.append("}")
        lines.append("```")
        lines.append("")
        lines.append(
            "**注意**: 既存のJSONファイルがある場合は、その内容を保持したまま、このセルの情報を追加または更新してください。"
        )

        return "\n".join(lines)

    def _get_relevant_files(
        self, codebase_sources: list[str], all_contents: dict[str, str]
    ) -> tuple[dict[str, str], str]:
        """
        コードベースソースに基づいて関連ファイルを抽出

        Args:
            codebase_sources: コードベースソースのリスト（例: ["README.md", "semantic_search"]）
            all_contents: すべてのファイル内容の辞書

        Returns:
            (関連ファイルの辞書, Git履歴のマークダウン)のタプル
        """
        relevant_files: dict[str, str] = {}
        git_content = ""

        for source in codebase_sources:
            if source == "semantic_search":
                # セマンティック検索の場合はすべてのファイルを含める
                relevant_files.update(all_contents)
            elif source == "git":
                # Git履歴を取得
                try:
                    git_content = generate_development_history_markdown(
                        self.project_root, max_commits=50, include_file_details=True
                    )
                    logger.debug("Git履歴を取得しました")
                except Exception as e:
                    logger.warning(f"Git履歴の取得に失敗しました: {e}")
                    git_content = "## Git履歴\n\nGit履歴の取得に失敗しました。\n"
            else:
                # ファイル名またはパターンで検索
                for file_path, content in all_contents.items():
                    if source in file_path or os.path.basename(file_path) == source:
                        if file_path not in relevant_files:
                            relevant_files[file_path] = content

        return relevant_files, git_content


def generate_prompts(
    config: Any,
    codebase_context: Any,
    project_root: str,
    output_dir: str | None = None,
    user_settings_path: str | None = None,
) -> list[str]:
    """
    プロンプトファイルを生成する便利関数

    Args:
        config: PortfolioConfigインスタンス
        codebase_context: CodebaseContextインスタンス
        project_root: プロジェクトルートディレクトリ
        output_dir: 出力ディレクトリ（Noneの場合は docs/portfolio-prompts/）

    Returns:
        生成されたプロンプトファイルのパスのリスト
    """
    if output_dir is None:
        output_dir = os.path.join(project_root, "docs", "portfolio-prompts")

    # ユーザー設定（Markdown）の読み込み
    user_settings = load_user_settings(project_root, user_settings_path)

    generator = PromptGenerator(
        config, codebase_context, project_root, user_settings=user_settings
    )
    return generator.generate_all_prompts(output_dir)
