#!/usr/bin/env python3
"""
ポートフォリオ自動生成システム v2.0
コードベースから直接情報を抽出してエクセルに自動入力

使い方（新リポジトリ構成）:
    # 例: 開発環境で src を PYTHONPATH に追加して実行
    PYTHONPATH=src python -m portfolio.generate_portfolio_v2
    PYTHONPATH=src python -m portfolio.generate_portfolio_v2 --config .cursor/portfolio_config.json --output ポートフォリオ_出力.xlsx
"""

import argparse
import logging
import os
import sys

from portfolio.codebase_reader import build_context_from_files
from portfolio.config_loader import PortfolioConfig
from portfolio.content_generator import ContentGenerator
from portfolio.content_storage import load_content_from_json
from portfolio.excel_writer import ExcelWriter
from portfolio.file_discovery import (
    discover_documentation_files,
    discover_project_structure,
    get_prioritized_files,
)
from portfolio.prompt_generator import generate_prompts

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """ロギングレベルを設定"""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("詳細ログモードを有効にしました")


def generate_prompts_mode(
    config_path: str | None = None,
    project_root: str | None = None,
    prompts_dir: str | None = None,
    verbose: bool = False,
) -> int:
    """
    プロンプトファイル生成モード

    Args:
        config_path: 設定ファイルのパス
        project_root: プロジェクトルートディレクトリ
        prompts_dir: プロンプトファイルの出力ディレクトリ
        verbose: 詳細ログを有効にする

    Returns:
        終了コード（0: 成功、1: エラー）
    """
    setup_logging(verbose)

    try:
        # 1. 設定ファイルの読み込み
        logger.info("設定ファイルを読み込んでいます...")
        config = PortfolioConfig(config_path)
        logger.info(f"設定ファイルを読み込みました: {config.version}")

        # プロジェクトルートの設定
        if project_root is None:
            project_root = os.getcwd()
        project_root = os.path.abspath(project_root)
        logger.info(f"プロジェクトルート: {project_root}")

        # 2. ファイル探索とコンテキスト構築
        logger.info("コードベースを探索しています...")
        documentation_files = discover_documentation_files(project_root)
        structure = discover_project_structure(project_root)

        # 優先度の高いファイルを選択
        all_files = documentation_files + structure["main_entry_points"]
        prioritized_files = get_prioritized_files(all_files, project_root, max_files=10)

        logger.info(f"{len(prioritized_files)} ファイルを読み込みます...")

        # 3. コードベースの読み込み
        context = build_context_from_files(prioritized_files, project_root)
        logger.info(f"コンテキストを構築しました: {len(context.files)} ファイル")

        # 4. プロンプトファイルの生成
        logger.info("プロンプトファイルを生成しています...")
        if prompts_dir is None:
            prompts_dir = os.path.join(project_root, "docs", "portfolio-prompts")

        generated_files = generate_prompts(config, context, project_root, prompts_dir)

        logger.info(
            f"プロンプトファイルを生成しました: {len(generated_files)} ファイル"
        )
        logger.info(f"プロンプトファイルの場所: {prompts_dir}")
        logger.info("")
        logger.info("次のステップ:")
        logger.info(
            "1. 生成されたプロンプトファイルを確認してください（docs/portfolio-prompts/）"
        )
        logger.info(
            "2. Cursor AIで各プロンプトファイルを読み込み、内容を生成してください"
        )
        logger.info(
            "3. 生成した内容を .cursor/portfolio-generated-content.json に保存してください"
        )
        logger.info(
            "4. PYTHONPATH=src python -m portfolio.generate_portfolio_v2 "
            "--from-json .cursor/portfolio-generated-content.json を実行してください"
        )

        return 0

    except Exception as e:
        logger.error(f"プロンプト生成中にエラーが発生しました: {e}", exc_info=True)
        return 1


def generate_portfolio_from_json(
    json_path: str,
    config_path: str | None = None,
    output_path: str | None = None,
    project_root: str | None = None,
    verbose: bool = False,
) -> int:
    """
    JSONファイルからポートフォリオを生成

    Args:
        json_path: 生成済み内容のJSONファイルのパス
        config_path: 設定ファイルのパス
        output_path: 出力ファイルのパス
        project_root: プロジェクトルートディレクトリ
        verbose: 詳細ログを有効にする

    Returns:
        終了コード（0: 成功、1: エラー）
    """
    setup_logging(verbose)

    try:
        # 1. 設定ファイルの読み込み
        logger.info("設定ファイルを読み込んでいます...")
        config = PortfolioConfig(config_path)
        logger.info(f"設定ファイルを読み込みました: {config.version}")

        # プロジェクトルートの設定
        if project_root is None:
            project_root = os.getcwd()
        project_root = os.path.abspath(project_root)
        logger.info(f"プロジェクトルート: {project_root}")

        # 2. JSONファイルから内容を読み込み
        logger.info(f"JSONファイルを読み込んでいます: {json_path}")
        cell_data = load_content_from_json(json_path)
        logger.info(f"{len(cell_data)} 個のセルデータを読み込みました")

        if not cell_data:
            logger.warning("JSONファイルにセルデータが含まれていません")
            return 1

        # 3. エクセルテンプレートのパスを取得
        template_path = config.get_excel_template_path(project_root)
        if not os.path.exists(template_path):
            logger.error(f"テンプレートファイルが見つかりません: {template_path}")
            return 1

        # 4. 出力パスの設定
        if output_path is None:
            project_name = os.path.basename(project_root)
            output_path = os.path.join(
                project_root, f"{project_name}_ポートフォリオ.xlsx"
            )
        output_path = os.path.abspath(output_path)
        logger.info(f"出力パス: {output_path}")

        # 5. エクセルライターの初期化
        logger.info("エクセルファイルを準備しています...")
        excel_writer = ExcelWriter(
            template_path, output_path, config.excel_template_sheet
        )

        # 6. エクセルに書き込み
        logger.info("セルに内容を書き込んでいます...")
        excel_writer.write_cells(cell_data)
        excel_writer.save()
        excel_writer.close()

        logger.info(f"ポートフォリオを生成しました: {output_path}")
        return 0

    except Exception as e:
        logger.error(
            f"JSONファイルからのポートフォリオ生成中にエラーが発生しました: {e}",
            exc_info=True,
        )
        return 1


def generate_portfolio(
    config_path: str | None = None,
    output_path: str | None = None,
    project_root: str | None = None,
    verbose: bool = False,
) -> int:
    """
    ポートフォリオを生成

    Args:
        config_path: 設定ファイルのパス
        output_path: 出力ファイルのパス
        project_root: プロジェクトルートディレクトリ
        verbose: 詳細ログを有効にする

    Returns:
        終了コード（0: 成功、1: エラー）
    """
    setup_logging(verbose)

    try:
        # 1. 設定ファイルの読み込み
        logger.info("設定ファイルを読み込んでいます...")
        config = PortfolioConfig(config_path)
        logger.info(f"設定ファイルを読み込みました: {config.version}")

        # プロジェクトルートの設定
        if project_root is None:
            project_root = os.getcwd()
        project_root = os.path.abspath(project_root)
        logger.info(f"プロジェクトルート: {project_root}")

        # 出力パスの設定
        if output_path is None:
            # デフォルト: プロジェクト名_ポートフォリオ.xlsx
            project_name = os.path.basename(project_root)
            output_path = os.path.join(
                project_root, f"{project_name}_ポートフォリオ.xlsx"
            )
        output_path = os.path.abspath(output_path)
        logger.info(f"出力パス: {output_path}")

        # 2. エクセルテンプレートのパスを取得
        template_path = config.get_excel_template_path(project_root)
        if not os.path.exists(template_path):
            logger.error(f"テンプレートファイルが見つかりません: {template_path}")
            return 1

        # 3. ファイル探索とコンテキスト構築
        logger.info("コードベースを探索しています...")
        documentation_files = discover_documentation_files(project_root)
        structure = discover_project_structure(project_root)

        # 優先度の高いファイルを選択
        all_files = documentation_files + structure["main_entry_points"]
        prioritized_files = get_prioritized_files(all_files, project_root, max_files=10)

        logger.info(f"{len(prioritized_files)} ファイルを読み込みます...")

        # 4. コードベースの読み込み
        context = build_context_from_files(prioritized_files, project_root)
        logger.info(f"コンテキストを構築しました: {len(context.files)} ファイル")

        # 5. エクセルライターの初期化
        logger.info("エクセルファイルを準備しています...")
        excel_writer = ExcelWriter(
            template_path, output_path, config.excel_template_sheet
        )

        # 6. 各セルに内容を生成して書き込み
        logger.info("セルに内容を書き込んでいます...")
        content_generator = ContentGenerator(config.config_data)

        cell_data: dict[str, str | int | float] = {}

        for cell_name, cell_config in config.cell_mapping.items():
            try:
                cell_address = cell_config.get("cell", "")
                description = cell_config.get("description", "")
                transform = cell_config.get("transform")
                max_chars = cell_config.get("max_chars") or cell_config.get(
                    "estimated_chars"
                )

                if not cell_address:
                    logger.warning(f"セルアドレスが設定されていません: {cell_name}")
                    continue

                # 内容を生成（現在は簡易実装）
                # 実際の実装では、セマンティック検索とAI生成を使用
                content = content_generator.generate_content(
                    description,
                    context.get_all_contents(),
                    transform,
                    max_chars,
                )

                cell_data[cell_address] = content
                logger.debug(f"セル {cell_address} ({cell_name}) に内容を生成しました")

            except Exception as e:
                logger.warning(f"セル {cell_name} の生成中にエラーが発生しました: {e}")
                # 続行（部分的な失敗を許容）

        # 7. エクセルに書き込み
        excel_writer.write_cells(cell_data)
        excel_writer.save()
        excel_writer.close()

        logger.info(f"ポートフォリオを生成しました: {output_path}")
        return 0

    except Exception as e:
        logger.error(f"ポートフォリオ生成中にエラーが発生しました: {e}", exc_info=True)
        return 1


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="コードベースから直接情報を抽出してポートフォリオを生成"
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=".cursor/portfolio_config.json",
        help="設定ファイルのパス（デフォルト: .cursor/portfolio_config.json）",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="出力ファイルのパス（デフォルト: プロジェクト名_ポートフォリオ.xlsx）",
    )
    parser.add_argument(
        "--project-root",
        "-p",
        type=str,
        default=None,
        help="プロジェクトルートディレクトリ（デフォルト: 現在のディレクトリ）",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="詳細なログを出力",
    )
    parser.add_argument(
        "--generate-prompts",
        action="store_true",
        help="プロンプトファイルを生成する（エクセルファイルは生成しない）",
    )
    parser.add_argument(
        "--from-json",
        type=str,
        default=None,
        help="生成済み内容のJSONファイルからエクセルを生成",
    )
    parser.add_argument(
        "--prompts-dir",
        type=str,
        default=None,
        help="プロンプトファイルの出力ディレクトリ（--generate-prompts使用時、デフォルト: docs/portfolio-prompts/）",
    )

    args = parser.parse_args()

    # プロンプト生成モード
    if args.generate_prompts:
        exit_code = generate_prompts_mode(
            config_path=args.config,
            project_root=args.project_root,
            prompts_dir=args.prompts_dir,
            verbose=args.verbose,
        )
        return exit_code

    # JSONファイルから生成モード
    if args.from_json:
        exit_code = generate_portfolio_from_json(
            json_path=args.from_json,
            config_path=args.config,
            output_path=args.output,
            project_root=args.project_root,
            verbose=args.verbose,
        )
        return exit_code

    # 通常モード（簡易実装を使用）
    exit_code = generate_portfolio(
        config_path=args.config,
        output_path=args.output,
        project_root=args.project_root,
        verbose=args.verbose,
    )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
