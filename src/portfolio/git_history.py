"""
ポートフォリオ自動生成システムのGit履歴読み込みモジュール
Git履歴を取得し、時系列で開発の様子をマークダウン形式で文書化
"""

import logging
import os
import subprocess
from collections import defaultdict
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class GitHistoryError(Exception):
    """Git履歴取得エラー"""

    pass


class CommitInfo:
    """コミット情報を保持するクラス"""

    def __init__(
        self,
        hash: str,
        date: str,
        author: str,
        message: str,
        files_changed: list[str],
    ):
        self.hash = hash
        self.date = date
        self.author = author
        self.message = message
        self.files_changed = files_changed

    def __repr__(self) -> str:
        return f"CommitInfo(hash={self.hash[:7]}, date={self.date}, message={self.message[:50]}...)"


def is_git_repository(project_root: str) -> bool:
    """
    Gitリポジトリかどうかを判定

    Args:
        project_root: プロジェクトルートディレクトリ

    Returns:
        Gitリポジトリの場合True
    """
    git_dir = os.path.join(project_root, ".git")
    return os.path.exists(git_dir) and os.path.isdir(git_dir)


def get_git_commits(project_root: str, max_commits: int = 100) -> list[CommitInfo]:
    """
    Gitコミット履歴を取得

    Args:
        project_root: プロジェクトルートディレクトリ
        max_commits: 取得する最大コミット数

    Returns:
        コミット情報のリスト（時系列順、新しい順）

    Raises:
        GitHistoryError: Gitコマンドの実行に失敗した場合
    """
    if not is_git_repository(project_root):
        logger.warning(f"Gitリポジトリではありません: {project_root}")
        return []

    try:
        # git logコマンドを実行
        # フォーマット: hash|date|author|message|files
        cmd = [
            "git",
            "log",
            f"--max-count={max_commits}",
            "--pretty=format:%H|%ai|%an|%s|",
            "--name-only",
            "--date=iso",
        ]

        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        if result.returncode != 0:
            logger.error(f"Gitコマンドの実行に失敗しました: {result.stderr}")
            raise GitHistoryError(f"Gitコマンドの実行に失敗: {result.stderr}")

        # 出力をパース
        commits: list[CommitInfo] = []
        lines = result.stdout.strip().split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # コミット情報行をパース
            parts = line.split("|")
            if len(parts) < 4:
                i += 1
                continue

            commit_hash = parts[0]
            commit_date = parts[1]
            commit_author = parts[2]
            commit_message = "|".join(parts[3:])  # メッセージに|が含まれる可能性がある

            # 変更ファイルを取得
            files_changed: list[str] = []
            i += 1
            while i < len(lines):
                file_line = lines[i].strip()
                if not file_line:
                    break
                files_changed.append(file_line)
                i += 1

            commits.append(
                CommitInfo(
                    hash=commit_hash,
                    date=commit_date,
                    author=commit_author,
                    message=commit_message,
                    files_changed=files_changed,
                )
            )

            i += 1

        logger.info(f"Gitコミット履歴を取得しました: {len(commits)} 件")
        return commits

    except FileNotFoundError:
        logger.error(
            "Gitコマンドが見つかりません。Gitがインストールされているか確認してください。"
        )
        raise GitHistoryError("Gitコマンドが見つかりません") from None
    except Exception as e:
        logger.error(f"Git履歴の取得中にエラーが発生しました: {e}")
        raise GitHistoryError(f"Git履歴の取得エラー: {e}") from e


def get_latest_commit_date(project_root: str) -> str | None:
    """
    最新のコミット日を取得

    Args:
        project_root: プロジェクトルートディレクトリ

    Returns:
        最新のコミット日（YYYY-MM-DD形式）、取得できない場合はNone
    """
    commits = get_git_commits(project_root, max_commits=1)
    if not commits:
        return None

    # ISO形式の日付からYYYY-MM-DDを抽出
    date_str = commits[0].date
    try:
        # ISO形式: 2025-11-27 10:30:00 +0900
        date_part = date_str.split()[0]
        return date_part
    except (IndexError, AttributeError):
        return None


def format_date_for_portfolio(date_str: str) -> str:
    """
    日付をポートフォリオ用の形式に変換（YYYY年/MM月/DD日）

    Args:
        date_str: 日付文字列（YYYY-MM-DD形式）

    Returns:
        フォーマットされた日付文字列
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%Y年/%m月/%d日")
    except (ValueError, AttributeError):
        # パースに失敗した場合は元の文字列を返す
        return date_str


def group_commits_by_date(commits: list[CommitInfo]) -> dict[str, list[CommitInfo]]:
    """
    コミットを日付ごとにグループ化

    Args:
        commits: コミット情報のリスト

    Returns:
        日付（YYYY-MM-DD）をキー、コミットリストをバリューとする辞書
    """
    grouped: dict[str, list[CommitInfo]] = defaultdict(list)

    for commit in commits:
        try:
            date_part = commit.date.split()[0]  # YYYY-MM-DD部分を取得
            grouped[date_part].append(commit)
        except (IndexError, AttributeError):
            # 日付のパースに失敗した場合はスキップ
            continue

    return dict(grouped)


def categorize_files(files: list[str]) -> dict[str, list[str]]:
    """
    変更ファイルをカテゴリごとに分類

    Args:
        files: ファイルパスのリスト

    Returns:
        カテゴリをキー、ファイルリストをバリューとする辞書
    """
    categories: dict[str, list[str]] = defaultdict(list)

    for file_path in files:
        # ファイル拡張子やディレクトリで分類
        if any(file_path.endswith(ext) for ext in [".py", ".pyw"]):
            categories["Python"].append(file_path)
        elif any(file_path.endswith(ext) for ext in [".js", ".ts", ".jsx", ".tsx"]):
            categories["JavaScript/TypeScript"].append(file_path)
        elif file_path.endswith(".md"):
            categories["ドキュメント"].append(file_path)
        elif any(
            file_path.endswith(ext) for ext in [".json", ".yaml", ".yml", ".toml"]
        ):
            categories["設定ファイル"].append(file_path)
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            categories["Excel"].append(file_path)
        elif "test" in file_path.lower() or "spec" in file_path.lower():
            categories["テスト"].append(file_path)
        else:
            categories["その他"].append(file_path)

    return dict(categories)


def generate_development_history_markdown(
    project_root: str,
    max_commits: int = 50,
    include_file_details: bool = True,
) -> str:
    """
    開発履歴をマークダウン形式で生成

    Args:
        project_root: プロジェクトルートディレクトリ
        max_commits: 取得する最大コミット数
        include_file_details: 変更ファイルの詳細を含めるかどうか

    Returns:
        マークダウン形式の開発履歴
    """
    if not is_git_repository(project_root):
        return "## Git履歴\n\nこのプロジェクトはGitリポジトリではありません。\n"

    try:
        commits = get_git_commits(project_root, max_commits=max_commits)
        if not commits:
            return "## Git履歴\n\nコミット履歴が見つかりませんでした。\n"

        # 日付ごとにグループ化
        grouped_commits = group_commits_by_date(commits)

        # マークダウンを生成
        md_lines: list[str] = []
        md_lines.append("# 開発履歴\n")
        md_lines.append(
            f"最終更新: {commits[0].date.split()[0] if commits else '不明'}\n"
        )
        md_lines.append(f"総コミット数: {len(commits)}\n")

        md_lines.append("\n## 時系列での開発の様子\n")

        # 日付順にソート（新しい順）
        sorted_dates = sorted(grouped_commits.keys(), reverse=True)

        for date in sorted_dates:
            date_commits = grouped_commits[date]
            md_lines.append(f"\n### {date}\n")

            for commit in date_commits:
                md_lines.append(f"#### {commit.message}\n")
                md_lines.append(f"- **コミット**: `{commit.hash[:7]}`")
                md_lines.append(f"- **作成者**: {commit.author}")
                md_lines.append(f"- **時刻**: {commit.date}")

                if include_file_details and commit.files_changed:
                    md_lines.append(
                        f"- **変更ファイル数**: {len(commit.files_changed)}"
                    )

                    # ファイルをカテゴリごとに分類
                    file_categories = categorize_files(commit.files_changed)
                    if file_categories:
                        md_lines.append("\n**変更内容**:")
                        for category, files in file_categories.items():
                            md_lines.append(f"  - {category}: {len(files)}ファイル")
                            # 主要なファイルのみ表示（各カテゴリ最大3ファイル）
                            important_files = files[:3]
                            for file_path in important_files:
                                md_lines.append(f"    - `{file_path}`")
                            if len(files) > 3:
                                md_lines.append(f"    - ... 他{len(files) - 3}ファイル")

                md_lines.append("")

            md_lines.append("---\n")

        # 統計情報を追加
        md_lines.append("\n## 開発統計\n\n")

        total_files_changed = sum(len(c.files_changed) for c in commits)
        unique_authors = set(c.author for c in commits)

        md_lines.append(f"- **総コミット数**: {len(commits)}")
        md_lines.append(f"- **総変更ファイル数**: {total_files_changed}")
        md_lines.append(f"- **開発者数**: {len(unique_authors)}")

        if unique_authors:
            md_lines.append(f"- **開発者**: {', '.join(sorted(unique_authors))}")

        # 開発期間
        if len(commits) > 1:
            first_date = commits[-1].date.split()[0]
            last_date = commits[0].date.split()[0]
            md_lines.append(f"- **開発期間**: {first_date} ～ {last_date}")

        md_lines.append("")

        return "\n".join(md_lines)

    except GitHistoryError as e:
        logger.error(f"Git履歴の取得に失敗しました: {e}")
        return f"## Git履歴\n\nエラー: Git履歴の取得に失敗しました。\n```\n{e}\n```\n"
    except Exception as e:
        logger.error(f"開発履歴の生成中にエラーが発生しました: {e}")
        return f"## Git履歴\n\nエラー: 開発履歴の生成中にエラーが発生しました。\n```\n{e}\n```\n"


def get_git_info_summary(project_root: str) -> dict[str, Any]:
    """
    Git情報のサマリーを取得

    Args:
        project_root: プロジェクトルートディレクトリ

    Returns:
        Git情報のサマリー辞書
    """
    if not is_git_repository(project_root):
        return {
            "is_git_repo": False,
            "latest_commit_date": None,
            "total_commits": 0,
        }

    try:
        commits = get_git_commits(project_root, max_commits=10)
        latest_date = get_latest_commit_date(project_root)

        return {
            "is_git_repo": True,
            "latest_commit_date": latest_date,
            "formatted_date": (
                format_date_for_portfolio(latest_date) if latest_date else None
            ),
            "total_commits": len(commits),
            "latest_commit": (
                {
                    "hash": commits[0].hash[:7] if commits else None,
                    "message": commits[0].message if commits else None,
                    "author": commits[0].author if commits else None,
                }
                if commits
                else None
            ),
        }
    except Exception as e:
        logger.error(f"Git情報の取得に失敗しました: {e}")
        return {
            "is_git_repo": True,
            "error": str(e),
            "latest_commit_date": None,
            "total_commits": 0,
        }












