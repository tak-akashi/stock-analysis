#!/usr/bin/env python3
"""
月次マスターデータ更新スクリプト
cronから実行される月次タスク
"""

import sys
from datetime import datetime

from market_pipeline.master.master_db import StockMasterDB
from market_pipeline.utils.slack_notifier import JobContext


def main():
    """月次マスターデータ更新処理"""
    print(f"=== マスターデータ月次更新開始 {datetime.now()} ===")

    try:
        with JobContext("月次マスターデータ更新") as job:
            # マスターDBの初期化と更新
            master_db = StockMasterDB()
            success = master_db.update_master_data()

            if success:
                # 統計情報の出力
                stats = master_db.get_statistics()
                job.add_metric("総銘柄数", str(stats["total_stocks"]))
                job.add_metric("アクティブ銘柄数", str(stats["active_stocks"]))
                print(
                    f"更新完了 - 総銘柄数: {stats['total_stocks']}, アクティブ: {stats['active_stocks']}"
                )
            else:
                raise RuntimeError("マスターデータの更新に失敗しました")

        print(f"=== マスターデータ月次更新完了 {datetime.now()} ===")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
