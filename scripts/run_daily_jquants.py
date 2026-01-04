#!/usr/bin/env python3
"""
日次株価データ取得スクリプト（J-Quants API）
cronから実行される日次タスク
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.config import get_settings
from backend.jquants.data_processor import JQuantsDataProcessor


def setup_logging(settings):
    """ログ設定"""
    log_dir = settings.paths.logs_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"jquants_daily_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=getattr(logging, settings.logging.level),
        format=settings.logging.format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    return logging.getLogger(__name__)


def main():
    """日次株価データ取得処理"""
    settings = get_settings()
    logger = setup_logging(settings)

    logger.info("=== J-Quants日次データ取得開始 ===")

    try:
        # データディレクトリ作成
        settings.paths.data_dir.mkdir(parents=True, exist_ok=True)
        db_path = settings.paths.jquants_db

        logger.info(f"データベースパス: {db_path}")
        logger.info(
            f"設定: max_concurrent_requests={settings.jquants.max_concurrent_requests}, "
            f"batch_size={settings.jquants.batch_size}, "
            f"request_delay={settings.jquants.request_delay}s"
        )

        processor = JQuantsDataProcessor(
            max_concurrent_requests=settings.jquants.max_concurrent_requests,
            batch_size=settings.jquants.batch_size,
            request_delay=settings.jquants.request_delay,
        )

        # データベースの存在確認
        db_exists = db_path.exists()
        logger.info(f"データベース存在: {'はい' if db_exists else 'いいえ'}")

        if not db_exists:
            logger.info("初回実行: 過去5年分のデータを取得します")
            processor.get_all_prices_for_past_5_years_to_db_optimized(str(db_path))
        else:
            logger.info("差分更新を実行します")
            processor.update_prices_to_db_optimized(str(db_path))

        # 統計情報を表示
        stats = processor.get_database_stats(str(db_path))
        if stats:
            logger.info("データベース統計:")
            logger.info(f"  レコード数: {stats.get('record_count', 'N/A')}")
            logger.info(f"  銘柄数: {stats.get('code_count', 'N/A')}")
            logger.info(f"  データ期間: {stats.get('date_range', 'N/A')}")

        logger.info("=== J-Quants日次データ取得完了 ===")

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        logger.error("環境変数 EMAIL, PASSWORD が正しく設定されているか確認してください")
        sys.exit(1)


if __name__ == "__main__":
    main()
