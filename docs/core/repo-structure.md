# リポジトリ構造

## ディレクトリツリー

```
Stock-Analysis/
├── core/                          # コアロジックとデータ処理
│   ├── __init__.py
│   ├── analysis/                     # 分析アルゴリズム
│   │   ├── __init__.py
│   │   ├── minervini.py              # ミネルヴィニトレンドスクリーニング
│   │   ├── high_low_ratio.py         # 52週高値・安値比率
│   │   ├── relative_strength.py      # RSP/RSI計算
│   │   ├── chart_classification.py   # MLベースチャートパターン分類
│   │   ├── integrated_analysis.py    # 複数指標統合クエリ
│   │   ├── integrated_analysis2.py   # Excel出力生成
│   │   ├── demo_integrated_analysis.py
│   │   └── _old/                     # 旧バージョン（参照用）
│   │       ├── minervini.py
│   │       ├── high_low_ratio.py
│   │       └── relative_strength.py
│   │
│   ├── config/                       # 設定管理
│   │   ├── __init__.py               # get_settings()エクスポート
│   │   └── settings.py               # Pydantic Settings定義
│   │
│   ├── jquants/                      # J-Quants API連携
│   │   ├── __init__.py
│   │   ├── data_processor.py         # 日次株価データ取得（非同期）
│   │   ├── statements_processor.py   # 財務諸表API
│   │   ├── fundamentals_calculator.py # PER/PBR/ROE等計算
│   │   └── _old/
│   │       └── data_processor.py
│   │
│   ├── master/                       # マスターデータ処理
│   │   └── master_db.py
│   │
│   ├── utils/                        # ユーティリティ
│   │   ├── __init__.py
│   │   ├── parallel_processor.py     # 並列処理フレームワーク
│   │   └── cache_manager.py          # キャッシュ管理
│   │
│   └── yfinance/                     # yfinance連携（レガシー、移行中）
│       └── data_processor.py
│
├── stock_reader/                     # pandas_datareader風データアクセスAPI
│   ├── __init__.py                   # パッケージエクスポート
│   ├── reader.py                     # DataReaderクラス実装
│   ├── utils.py                      # ユーティリティ関数
│   └── exceptions.py                 # カスタム例外クラス
│
├── scripts/                          # 実行スクリプト（cron用）
│   ├── run_daily_jquants.py          # 日次株価取得（平日22:00）
│   ├── run_daily_analysis.py         # 日次分析（平日23:00）
│   ├── run_weekly_tasks.py           # 週次タスク（日曜20:00）
│   ├── run_monthly_master.py         # 月次マスター更新（1日18:00）
│   ├── run_adhoc_integrated_analysis.py # アドホック統合分析
│   ├── create_database_indexes.py    # DBインデックス作成
│   └── _old/
│       ├── run_daily_jquants.py
│       └── run_daily_analysis.py
│
├── tests/                            # テストコード
│   ├── conftest.py                   # 共有フィクスチャ
│   ├── test_minervini.py
│   ├── test_high_low_ratio.py
│   ├── test_relative_strength.py
│   ├── test_chart_classification.py
│   ├── test_integrated_analysis.py
│   ├── test_integrated_analysis_optimization.py
│   ├── test_jquants_data_processor.py
│   ├── test_jquants_performance.py
│   ├── test_statements_processor.py
│   ├── test_fundamentals_calculator.py
│   ├── test_data_processor.py        # yfinance（レガシー）
│   ├── test_analysis_integration.py
│   ├── test_type8_optimization.py
│   ├── test_rsi_optimization.py
│   ├── test_optimizations.py
│   ├── test_functions.py
│   ├── test_fixes.py
│   └── simple_test.py
│
├── data/                             # SQLiteデータベース
│   ├── jquants.db                    # 日次株価（820MB）
│   ├── statements.db                 # 財務諸表（30MB）
│   ├── analysis_results.db           # 分析結果（1.7GB）
│   ├── master.db                     # 銘柄マスター（964KB）
│   └── yfinance.db                   # レガシー（1.4MB）
│
├── output/                           # 出力ファイル
│   ├── analysis_YYYY-MM-DD.xlsx      # 日次分析レポート
│   └── errors/                       # エラーログ
│
├── logs/                             # 実行ログ
│   └── *.log
│
├── docs/                             # ドキュメント
│   ├── core/                         # コアドキュメント
│   │   ├── architecture.md
│   │   ├── api-reference.md
│   │   ├── diagrams.md
│   │   ├── CHANGELOG.md
│   │   ├── dev-guidelines.md
│   │   └── repo-structure.md
│   ├── refs/                         # 参照用ドキュメント
│   │   ├── technical_design.md
│   │   ├── OPTIMIZATION_TECHNIQUES_GUIDE.md
│   │   ├── JQUANTS_OPTIMIZATION_README.md
│   │   └── ANALYSIS_OPTIMIZATION_README.md
│   └── ideas/                        # アイデア・検討用ドキュメント
│
├── notebooks/                        # Jupyter Notebook（分析・可視化用）
│   └── *.ipynb
│
├── sandbox/                          # 実験用コード
│
├── .env                              # 環境変数（gitignore）
├── .env.example                      # 環境変数テンプレート
├── .gitignore
├── CLAUDE.md                         # Claude Code用ガイド
├── README.md
├── pyproject.toml                    # プロジェクト設定
└── uv.lock                           # 依存関係ロック
```

## 主要ファイル説明

### 設定ファイル

| ファイル | 説明 |
|---------|------|
| `pyproject.toml` | プロジェクト設定、依存関係、ツール設定 |
| `.env` | 環境変数（API認証情報等） |
| `.env.example` | 環境変数テンプレート |
| `CLAUDE.md` | Claude Code用のプロジェクトガイド |

### バックエンドモジュール

| パス | 説明 |
|-----|------|
| `core/config/settings.py` | Pydantic Settings による設定管理 |
| `core/jquants/data_processor.py` | 非同期株価データ取得（~500行） |
| `core/jquants/statements_processor.py` | 財務諸表取得（~400行） |
| `core/jquants/fundamentals_calculator.py` | 財務指標計算（~300行） |
| `core/analysis/minervini.py` | ミネルヴィニ分析 |
| `core/analysis/high_low_ratio.py` | HL比率計算 |
| `core/analysis/relative_strength.py` | RSP/RSI計算 |
| `core/analysis/chart_classification.py` | チャートパターン分類 |
| `core/analysis/integrated_analysis2.py` | Excel出力 |
| `core/utils/parallel_processor.py` | 並列処理ラッパー |
| `core/utils/cache_manager.py` | キャッシュ管理 |
| `stock_reader/reader.py` | DataReaderクラス（pandas_datareader風API） |
| `stock_reader/exceptions.py` | カスタム例外クラス |

### スクリプト

| パス | 実行タイミング | 説明 |
|-----|--------------|------|
| `scripts/run_daily_jquants.py` | 平日22:00 | J-Quants APIから株価取得 |
| `scripts/run_daily_analysis.py` | 平日23:00 | 日次分析実行 |
| `scripts/run_weekly_tasks.py` | 日曜20:00 | 財務諸表取得 + 統合分析 |
| `scripts/run_monthly_master.py` | 毎月1日18:00 | マスターデータ更新 |
| `scripts/run_adhoc_integrated_analysis.py` | 手動 | アドホック統合分析実行 |
| `scripts/create_database_indexes.py` | 初回のみ | DBインデックス作成 |

### データベース

| ファイル | サイズ | 主要テーブル |
|---------|-------|-------------|
| `data/jquants.db` | 820MB | daily_quotes |
| `data/statements.db` | 30MB | financial_statements, calculated_fundamentals |
| `data/analysis_results.db` | 1.7GB | hl_ratio, minervini, relative_strength, classification_results |
| `data/master.db` | 964KB | stocks_master |

### テストファイル

| ファイル | テスト対象 |
|---------|----------|
| `tests/conftest.py` | 共有フィクスチャ |
| `tests/test_minervini.py` | ミネルヴィニ分析 |
| `tests/test_high_low_ratio.py` | HL比率 |
| `tests/test_relative_strength.py` | RSP/RSI |
| `tests/test_chart_classification.py` | チャートパターン分類 |
| `tests/test_statements_processor.py` | 財務諸表処理 |
| `tests/test_fundamentals_calculator.py` | 財務指標計算 |
| `tests/test_jquants_data_processor.py` | J-Quants API |
| `tests/test_jquants_performance.py` | パフォーマンステスト |
| `tests/test_stock_reader.py` | stock_readerパッケージ |

## ディレクトリ命名規則

- **`_old/`**: 旧バージョンのファイル（参照用に保持）
- **`core/`**: コアドキュメント

## ファイル命名規則

- **Pythonモジュール**: `snake_case.py`
- **テストファイル**: `test_<module_name>.py`
- **設定ファイル**: `lowercase.toml`, `.env`
- **ドキュメント**: `kebab-case.md` または `UPPERCASE.md`
