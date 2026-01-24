# API リファレンス

## 設定モジュール (`backend/config/`)

### get_settings()

設定インスタンスを取得します（シングルトン）。

```python
from backend.config import get_settings

settings = get_settings()
```

**戻り値**: `Settings` - 設定オブジェクト

### Settings クラス

#### settings.paths

| 属性 | 型 | 説明 |
|-----|-----|------|
| `base_dir` | `Path` | プロジェクトルートディレクトリ |
| `data_dir` | `Path` | データディレクトリ (`data/`) |
| `logs_dir` | `Path` | ログディレクトリ (`logs/`) |
| `output_dir` | `Path` | 出力ディレクトリ (`output/`) |
| `jquants_db` | `Path` | J-Quants株価DB (`data/jquants.db`) |
| `analysis_db` | `Path` | 分析結果DB (`data/analysis_results.db`) |
| `yfinance_db` | `Path` | yfinance DB (`data/yfinance.db`) - レガシー |
| `master_db` | `Path` | マスターDB (`data/master.db`) |
| `statements_db` | `Path` | 財務諸表DB (`data/statements.db`) |

#### settings.jquants

| 属性 | 型 | デフォルト | 説明 |
|-----|-----|---------|------|
| `max_concurrent_requests` | `int` | 3 | 同時リクエスト数上限 |
| `batch_size` | `int` | 100 | バッチサイズ |
| `request_delay` | `float` | 0.1 | リクエスト間隔（秒） |
| `timeout_seconds` | `int` | 30 | リクエストタイムアウト（秒） |
| `cache_ttl_hours` | `int` | 24 | キャッシュ有効期間（時間） |

#### settings.yfinance

| 属性 | 型 | デフォルト | 説明 |
|-----|-----|---------|------|
| `max_workers` | `int` | 1 | 最大ワーカー数（1 = シーケンシャル推奨） |
| `rate_limit_delay` | `float` | 2.0 | リクエスト間隔（秒） |

#### settings.analysis

| 属性 | 型 | デフォルト | 説明 |
|-----|-----|---------|------|
| `sma_short` | `int` | 50 | 短期移動平均期間 |
| `sma_medium` | `int` | 150 | 中期移動平均期間 |
| `sma_long` | `int` | 200 | 長期移動平均期間 |
| `hl_ratio_weeks` | `int` | 52 | HL比率計算期間（週） |
| `rsp_period_days` | `int` | 500 | RSP計算期間（日） |
| `update_window_days` | `int` | 5 | 更新ウィンドウ期間（日） |
| `trading_days_per_year` | `int` | 260 | 年間営業日数 |
| `type6_threshold` | `float` | 1.3 | Type6判定閾値（52週安値の130%以上） |
| `type7_threshold` | `float` | 0.75 | Type7判定閾値（52週高値の75%以上） |
| `type8_rsi_threshold` | `int` | 70 | Type8判定RSI閾値 |
| `rsp_weight_q1_q3` | `float` | 0.2 | RSP計算のQ1-Q3ウェイト |
| `rsp_weight_q4` | `float` | 0.4 | RSP計算のQ4ウェイト |
| `composite_weight_hl` | `float` | 0.4 | 複合スコアのHL比率ウェイト |
| `composite_weight_rsi` | `float` | 0.4 | 複合スコアのRSIウェイト |
| `composite_weight_minervini` | `float` | 0.2 | 複合スコアのMinerviniウェイト |
| `high_rsi_threshold` | `float` | 70.0 | 高RSI閾値 |
| `strong_composite_threshold` | `float` | 70.0 | 強い複合スコア閾値 |
| `chart_windows` | `list` | [20, 60, 120, 240] | 短期チャートウィンドウ |
| `chart_long_windows` | `list` | [960, 1200] | 長期チャートウィンドウ |

#### settings.database

| 属性 | 型 | デフォルト | 説明 |
|-----|-----|---------|------|
| `journal_mode` | `str` | "WAL" | SQLiteジャーナルモード |
| `synchronous` | `str` | "NORMAL" | 同期モード |
| `cache_size` | `int` | 10000 | キャッシュサイズ（ページ） |
| `mmap_size` | `int` | 268435456 | メモリマップサイズ（256MB） |

---

## J-Quants モジュール (`backend/jquants/`)

### JQuantsDataProcessor

日次株価データの取得と保存を担当。

```python
from backend.jquants.data_processor import JQuantsDataProcessor

processor = JQuantsDataProcessor()
await processor.fetch_and_store_daily_quotes(stock_codes, start_date, end_date)
```

#### メソッド

##### `async fetch_and_store_daily_quotes(stock_codes, start_date, end_date)`

複数銘柄の日次株価データを非同期で取得し、データベースに保存。

**パラメータ**:
- `stock_codes` (`list[str]`): 銘柄コードリスト
- `start_date` (`str`): 開始日 (YYYY-MM-DD)
- `end_date` (`str`): 終了日 (YYYY-MM-DD)

##### `get_refresh_token() -> str`

J-Quants APIのリフレッシュトークンを取得。

### JQuantsStatementsProcessor

財務諸表データの取得を担当。

```python
from backend.jquants.statements_processor import JQuantsStatementsProcessor

processor = JQuantsStatementsProcessor(
    max_concurrent_requests=3,
    batch_size=100,
    request_delay=0.1
)
processor.get_all_statements(db_path)
```

#### コンストラクタ

```python
JQuantsStatementsProcessor(
    max_concurrent_requests: int = 3,
    batch_size: int = 100,
    request_delay: float = 0.1
)
```

**パラメータ**:
- `max_concurrent_requests`: 同時リクエスト数上限
- `batch_size`: バッチサイズ
- `request_delay`: リクエスト間隔（秒）

#### メソッド

##### `get_all_statements(db_path: str)`

全上場銘柄の財務諸表データを取得しデータベースに保存。

**パラメータ**:
- `db_path` (`str`): statements.dbのパス

##### `async get_statements_async(session, code) -> Tuple[str, List[Dict]]`

単一銘柄の財務諸表を非同期で取得。

**パラメータ**:
- `session`: aiohttpセッション
- `code` (`str`): 銘柄コード（5桁）

**戻り値**: `Tuple[str, List[Dict]]` - (銘柄コード, 財務諸表リスト)

##### `get_database_stats(db_path: str) -> Dict[str, Any]`

データベース統計を取得。

**戻り値**: `Dict` - statement_record_count, statement_code_count, statement_date_range, fundamentals_count

### FundamentalsCalculator

財務指標の計算を担当。

```python
from backend.jquants.fundamentals_calculator import FundamentalsCalculator

calculator = FundamentalsCalculator(
    statements_db_path="data/statements.db",
    jquants_db_path="data/jquants.db"
)
processed = calculator.update_all_fundamentals(output_db_path)
```

#### コンストラクタ

```python
FundamentalsCalculator(
    statements_db_path: str,
    jquants_db_path: str,
    master_db_path: str = None
)
```

**パラメータ**:
- `statements_db_path`: statements.dbのパス（財務諸表テーブル）
- `jquants_db_path`: jquants.dbのパス（株価テーブル）
- `master_db_path`: master.dbのパス（省略時はjquants_db_pathから推測）

#### メソッド

##### `update_all_fundamentals(output_db_path: str) -> int`

全銘柄のファンダメンタルズを計算しデータベースに保存。

**パラメータ**:
- `output_db_path` (`str`): 出力データベースパス

**戻り値**: `int` - 処理した銘柄数

##### `calculate_per(price, eps) -> Optional[float]`

PER（株価収益率）を計算。

##### `calculate_pbr(price, bps) -> Optional[float]`

PBR（株価純資産倍率）を計算。

##### `calculate_roe(profit, equity) -> Optional[float]`

ROE（自己資本利益率）を計算。

##### `calculate_roa(profit, total_assets) -> Optional[float]`

ROA（総資産利益率）を計算。

##### `calculate_dividend_yield(dps, price) -> Optional[float]`

配当利回りを計算。

##### `calculate_market_cap(price, shares) -> Optional[float]`

時価総額を計算。

##### `calculate_operating_margin(operating_profit, net_sales) -> Optional[float]`

営業利益率を計算。

##### `calculate_profit_margin(profit, net_sales) -> Optional[float]`

純利益率を計算。

##### `calculate_free_cash_flow(cf_operating, cf_investing) -> Optional[float]`

フリーキャッシュフローを計算。

---

## 分析モジュール (`backend/analysis/`)

### MinerviniAnalyzer

マーク・ミネルヴィニのトレンドスクリーニング戦略。

```python
from backend.analysis.minervini import MinerviniAnalyzer

analyzer = MinerviniAnalyzer(db_path)
results = analyzer.analyze(stock_codes, date)
```

#### コンストラクタ

```python
MinerviniAnalyzer(db_path: str | Path)
```

**パラメータ**:
- `db_path`: jquants.dbのパス

#### メソッド

##### `analyze(stock_codes, date) -> pd.DataFrame`

指定日時点でのミネルヴィニ条件チェック。

**パラメータ**:
- `stock_codes` (`list[str]`): 銘柄コードリスト
- `date` (`str`): 分析日 (YYYY-MM-DD)

**戻り値**: `pd.DataFrame` - 各条件の合否とスコア

### HighLowRatioAnalyzer

52週高値・安値位置比率の計算。

```python
from backend.analysis.high_low_ratio import HighLowRatioAnalyzer

analyzer = HighLowRatioAnalyzer(db_path)
results = analyzer.calculate(stock_codes, date)
```

#### メソッド

##### `calculate(stock_codes, date) -> pd.DataFrame`

HL比率（0-100%）を計算。100%に近いほど52週高値に近い。

**パラメータ**:
- `stock_codes` (`list[str]`): 銘柄コードリスト
- `date` (`str`): 分析日 (YYYY-MM-DD)

**戻り値**: `pd.DataFrame` - Code, Date, hl_ratio

### RelativeStrengthAnalyzer

相対力指標（RSP/RSI）の計算。

```python
from backend.analysis.relative_strength import RelativeStrengthAnalyzer

analyzer = RelativeStrengthAnalyzer(db_path)
results = analyzer.calculate(stock_codes, date)
```

#### メソッド

##### `calculate(stock_codes, date) -> pd.DataFrame`

RSP（相対力パーセンテージ）とRSI（相対力指数）を計算。

**パラメータ**:
- `stock_codes` (`list[str]`): 銘柄コードリスト
- `date` (`str`): 分析日 (YYYY-MM-DD)

**戻り値**: `pd.DataFrame` - Code, Date, rsp, rsi

### ChartClassifier

MLベースのチャートパターン分類。

```python
from backend.analysis.chart_classification import ChartClassifier

classifier = ChartClassifier(db_path)
results = classifier.classify(stock_codes, windows=[20, 60, 120, 240])
```

#### コンストラクタ

```python
ChartClassifier(db_path: str | Path, mode: str = "full-optimized")
```

**パラメータ**:
- `db_path`: jquants.dbのパス
- `mode`: 実行モード ("sample-adaptive" | "full-optimized")

#### メソッド

##### `classify(stock_codes, windows) -> pd.DataFrame`

チャートパターンを分類。

**パラメータ**:
- `stock_codes` (`list[str]`): 銘柄コードリスト
- `windows` (`list[int]`): 分析ウィンドウサイズ

**戻り値**: `pd.DataFrame` - Code, Date, window, pattern_type, confidence

---

## ユーティリティ (`backend/utils/`)

### ParallelProcessor

並列処理のラッパークラス。

```python
from backend.utils.parallel_processor import ParallelProcessor

processor = ParallelProcessor(n_workers=8)
results = processor.process(items, process_func)
```

#### コンストラクタ

```python
ParallelProcessor(n_workers: int = None, use_threads: bool = False)
```

**パラメータ**:
- `n_workers`: ワーカー数（デフォルト: CPUコア数）
- `use_threads`: ThreadPoolExecutorを使用（デフォルト: ProcessPoolExecutor）

#### メソッド

##### `process(items, func, batch_size=100) -> list`

アイテムを並列処理。

**パラメータ**:
- `items` (`list`): 処理対象リスト
- `func` (`callable`): 処理関数
- `batch_size` (`int`): バッチサイズ

**戻り値**: `list` - 処理結果

### BatchDatabaseProcessor

効率的なバッチデータベース操作のユーティリティクラス。

```python
from backend.utils.parallel_processor import BatchDatabaseProcessor

processor = BatchDatabaseProcessor(db_path, batch_size=1000)

# バッチ挿入
inserted = processor.batch_insert('table_name', records, on_conflict='REPLACE')

# バッチ取得
df = processor.batch_fetch(query, params=[], as_dataframe=True)

# インデックス作成
processor.create_indexes([
    {'name': 'idx_name', 'table': 'table_name', 'columns': ['col1', 'col2'], 'unique': False}
])
```

#### コンストラクタ

```python
BatchDatabaseProcessor(db_path: str, batch_size: int = 1000)
```

**パラメータ**:
- `db_path`: SQLiteデータベースのパス
- `batch_size`: バッチサイズ

#### メソッド

##### `batch_insert(table_name, data, on_conflict='REPLACE') -> int`

バッチ挿入を実行。

**パラメータ**:
- `table_name` (`str`): テーブル名
- `data` (`List[Dict]`): 行データのリスト
- `on_conflict` (`str`): 競合時の処理（'REPLACE' | 'IGNORE' など）

**戻り値**: `int` - 挿入された行数

##### `batch_fetch(query, params=None, as_dataframe=True) -> Union[pd.DataFrame, List[Tuple]]`

効率的なデータ取得。

**パラメータ**:
- `query` (`str`): SQLクエリ
- `params` (`List[Any]`): クエリパラメータ
- `as_dataframe` (`bool`): DataFrameで返すか

**戻り値**: `pd.DataFrame` または `List[Tuple]`

##### `create_indexes(index_definitions: List[Dict]) -> None`

データベースインデックスを作成。

### measure_performance

関数の実行時間を計測するデコレータ。

```python
from backend.utils.parallel_processor import measure_performance

@measure_performance
def my_function():
    # 処理
    pass
```

### CacheManager

メモリ・ディスクベースのキャッシュ管理クラス。

```python
from backend.utils.cache_manager import CacheManager, get_cache

# グローバルキャッシュインスタンスを取得（推奨）
cache = get_cache()

# または直接初期化
cache = CacheManager(
    cache_dir="/path/to/cache",
    max_memory_items=100,
    default_ttl_hours=24
)

# キャッシュに保存
cache.put("key", data, ttl_hours=24, use_disk=True)

# キャッシュから取得
data = cache.get("key", use_disk=True)

# 関数デコレータとして使用
@cache.cached_function(ttl_hours=6, use_disk=True)
def expensive_calculation(param):
    return result
```

#### コンストラクタ

```python
CacheManager(
    cache_dir: Optional[str] = None,
    max_memory_items: int = 100,
    default_ttl_hours: int = 24
)
```

**パラメータ**:
- `cache_dir`: ディスクキャッシュディレクトリ（省略時はシステムtempを使用）
- `max_memory_items`: メモリキャッシュの最大アイテム数
- `default_ttl_hours`: デフォルトの有効期限（時間）

#### メソッド

##### `put(key, data, ttl_hours=None, use_disk=True)`

データをキャッシュに保存。

##### `get(key, use_disk=True) -> Any | None`

キャッシュからデータを取得。期限切れの場合はNone。

##### `clear_memory()`

メモリキャッシュをクリア。

##### `clear_disk()`

ディスクキャッシュをクリア。

##### `clear_all()`

全キャッシュをクリア。

##### `get_stats() -> Dict`

キャッシュ統計を取得（memory_items, disk_items, disk_size_mb, cache_dir）。

##### `cleanup_expired()`

期限切れのキャッシュエントリを削除。

#### ヘルパー関数

##### `get_cache() -> CacheManager`

グローバルキャッシュインスタンスを取得。

##### `cache_dataframe(key, df, ttl_hours=24)`

pandas DataFrameをキャッシュに保存。

##### `get_cached_dataframe(key) -> Optional[pd.DataFrame]`

キャッシュからDataFrameを取得。

---

## スクリプト (`scripts/`)

### run_daily_jquants.py

```bash
python scripts/run_daily_jquants.py
```

J-Quants APIから日次株価データを取得し、`data/jquants.db`に保存。

### run_daily_analysis.py

```bash
python scripts/run_daily_analysis.py
python scripts/run_daily_analysis.py --modules hl_ratio rsp minervini
```

**オプション**:
- `--modules`: 実行する分析モジュールを指定

### run_weekly_tasks.py

```bash
python scripts/run_weekly_tasks.py
python scripts/run_weekly_tasks.py --statements-only
python scripts/run_weekly_tasks.py --analysis-only
```

**オプション**:
- `--statements-only`: 財務諸表取得のみ
- `--analysis-only`: 統合分析のみ

### run_monthly_master.py

```bash
python scripts/run_monthly_master.py
```

銘柄マスターデータを更新。

### run_adhoc_integrated_analysis.py

```bash
python scripts/run_adhoc_integrated_analysis.py
```

アドホック統合分析を実行。スケジュール外で手動実行する場合に使用。

### create_database_indexes.py

```bash
python scripts/create_database_indexes.py
```

SQLiteデータベースにインデックスを作成（初回セットアップ時）。
