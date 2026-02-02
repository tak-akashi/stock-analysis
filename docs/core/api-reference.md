# API リファレンス

## 設定モジュール (`backend/market_pipeline/config/`)

### get_settings()

設定インスタンスを取得します（シングルトン）。

```python
from market_pipeline.config import get_settings

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

## Market Reader パッケージ (`backend/market_reader/`)

pandas_datareader風のインターフェースでJ-Quantsの株価データにアクセスするパッケージ。

### DataReader

```python
from market_reader import DataReader

reader = DataReader()
df = reader.get_prices("7203", start="2024-01-01", end="2024-12-31")
```

#### コンストラクタ

```python
DataReader(db_path: str | Path | None = None, strict: bool = False)
```

**パラメータ**:
- `db_path`: jquants.dbのパス（省略時はsettings.paths.jquants_dbを使用）
- `strict`: エラー時の動作。True=例外発生、False（デフォルト）=空DataFrameと警告

**例外**:
- `DatabaseConnectionError`: データベースファイルが存在しない、またはアクセスできない場合

#### メソッド

##### `get_prices(code, start=None, end=None, columns="simple") -> pd.DataFrame`

株価データを取得。

**パラメータ**:
- `code` (`str | list[str]`): 銘柄コード（4桁または5桁、単一または複数）
- `start` (`str | None`): 開始日 (YYYY-MM-DD)。省略時はendの5年前
- `end` (`str | None`): 終了日 (YYYY-MM-DD)。省略時はDB内最新日
- `columns` (`str | list[str]`): 取得カラム。"simple"、"full"、またはカラム名リスト

**columnsオプション詳細**:

| オプション | 説明 |
|-----------|------|
| `"simple"` | デフォルト。基本的なOHLCVデータ |
| `"full"` | 全カラム（Date, Code以外） |
| `list[str]` | 任意のカラム名リスト |

**SIMPLE_COLUMNS** (6カラム):

| カラム名 | 説明 |
|---------|------|
| `Open` | 始値 |
| `High` | 高値 |
| `Low` | 安値 |
| `Close` | 終値 |
| `Volume` | 出来高 |
| `AdjustmentClose` | 調整後終値 |

**FULL_COLUMNS** (16カラム):

| カラム名 | 説明 |
|---------|------|
| `Date` | 日付（インデックスとして使用） |
| `Code` | 銘柄コード（インデックスとして使用） |
| `Open` | 始値 |
| `High` | 高値 |
| `Low` | 安値 |
| `Close` | 終値 |
| `UpperLimit` | ストップ高 |
| `LowerLimit` | ストップ安 |
| `Volume` | 出来高 |
| `TurnoverValue` | 売買代金 |
| `AdjustmentFactor` | 調整係数 |
| `AdjustmentOpen` | 調整後始値 |
| `AdjustmentHigh` | 調整後高値 |
| `AdjustmentLow` | 調整後安値 |
| `AdjustmentClose` | 調整後終値 |
| `AdjustmentVolume` | 調整後出来高 |

**戻り値**: `pd.DataFrame` - 日付インデックスの株価DataFrame。複数銘柄の場合はMultiIndex（Date, Code）

**例外**（strict=True時のみ）:
- `StockNotFoundError`: 銘柄が見つからない場合
- `InvalidDateRangeError`: start > end の場合

**例外**（常時）:
- `ValueError`: 無効なカラム名、無効な日付フォーマット

### 例外クラス

| クラス | 説明 |
|--------|------|
| `StockReaderError` | 基底例外クラス |
| `StockNotFoundError` | 銘柄が見つからない |
| `DatabaseConnectionError` | DB接続エラー |
| `InvalidDateRangeError` | 日付範囲エラー（start > end） |

### ユーティリティ関数 (`backend/market_reader/utils.py`)

##### `normalize_code(code: str) -> str`

銘柄コードを4桁形式に正規化。5桁コードで末尾が0の場合、4桁に変換。

```python
>>> normalize_code("72030")
'7203'
>>> normalize_code("7203")
'7203'
>>> normalize_code("72031")  # 末尾が0以外は変換しない
'72031'
```

##### `to_5digit_code(code: str) -> str`

4桁コードを5桁形式に変換（DBクエリ用）。

```python
>>> to_5digit_code("7203")
'72030'
```

##### `validate_date(date_str: str | None) -> datetime | None`

日付文字列をdatetimeに変換。形式はYYYY-MM-DD。

**例外**: `ValueError` - 無効な日付フォーマット

##### `get_default_end_date(conn: sqlite3.Connection) -> datetime`

データベース内の最新日付を取得。

##### `get_default_start_date(end_date: datetime) -> datetime`

デフォルト開始日（end_dateの5年前）を計算。

---

## Technical Tools パッケージ (`backend/technical_tools/`)

Jupyter Notebook用のテクニカル分析ツール。日本株(J-Quants)と米国株(yfinance)の統一インターフェースを提供。

### TechnicalAnalyzer

```python
from technical_tools import TechnicalAnalyzer

analyzer = TechnicalAnalyzer(source="jquants")
fig = analyzer.plot_chart("7203", show_sma=[25, 75], show_rsi=True)
fig.show()
```

#### コンストラクタ

```python
TechnicalAnalyzer(source: Literal["jquants", "yfinance"] = "jquants")
```

**パラメータ**:
- `source`: データソース（"jquants" または "yfinance"）

#### メソッド

##### `get_prices(ticker, start=None, end=None, **kwargs) -> pd.DataFrame`

株価データを取得（キャッシュ付き）。

**パラメータ**:
- `ticker` (`str`): 銘柄コード
- `start` (`str | None`): 開始日 (YYYY-MM-DD)
- `end` (`str | None`): 終了日 (YYYY-MM-DD)
- `**kwargs`: 追加引数（`period` など）

**戻り値**: `pd.DataFrame` - OHLCV列を持つDataFrame

##### `calculate_indicators(ticker, indicators, start=None, end=None, **kwargs) -> pd.DataFrame`

複数のテクニカル指標を計算。

**パラメータ**:
- `ticker` (`str`): 銘柄コード
- `indicators` (`list[str]`): 指標リスト（"sma", "ema", "rsi", "macd", "bb"）
- `start` (`str | None`): 開始日
- `end` (`str | None`): 終了日

**戻り値**: `pd.DataFrame` - 指標列が追加されたDataFrame

##### `add_sma(ticker, periods, start=None, end=None, **kwargs) -> pd.DataFrame`

単純移動平均を追加。

**パラメータ**:
- `ticker` (`str`): 銘柄コード
- `periods` (`list[int]`): SMA期間リスト

**戻り値**: `pd.DataFrame` - `SMA_N`列が追加されたDataFrame

##### `add_ema(ticker, periods, start=None, end=None, **kwargs) -> pd.DataFrame`

指数移動平均を追加。

**パラメータ**:
- `ticker` (`str`): 銘柄コード
- `periods` (`list[int]`): EMA期間リスト

**戻り値**: `pd.DataFrame` - `EMA_N`列が追加されたDataFrame

##### `add_rsi(ticker, period=14, start=None, end=None, **kwargs) -> pd.DataFrame`

RSIを追加。

**パラメータ**:
- `ticker` (`str`): 銘柄コード
- `period` (`int`): RSI期間（デフォルト: 14）

**戻り値**: `pd.DataFrame` - `RSI_N`列が追加されたDataFrame

##### `add_macd(ticker, fast=12, slow=26, signal=9, start=None, end=None, **kwargs) -> pd.DataFrame`

MACDを追加。

**パラメータ**:
- `ticker` (`str`): 銘柄コード
- `fast` (`int`): 短期EMA期間（デフォルト: 12）
- `slow` (`int`): 長期EMA期間（デフォルト: 26）
- `signal` (`int`): シグナル線期間（デフォルト: 9）

**戻り値**: `pd.DataFrame` - `MACD`, `MACD_Signal`, `MACD_Hist`列が追加されたDataFrame

##### `add_bollinger_bands(ticker, period=20, std=2.0, start=None, end=None, **kwargs) -> pd.DataFrame`

ボリンジャーバンドを追加。

**パラメータ**:
- `ticker` (`str`): 銘柄コード
- `period` (`int`): 移動平均期間（デフォルト: 20）
- `std` (`float`): 標準偏差倍率（デフォルト: 2.0）

**戻り値**: `pd.DataFrame` - `BB_Upper`, `BB_Middle`, `BB_Lower`列が追加されたDataFrame

##### `detect_crosses(ticker, short=5, long=25, patterns=None, start=None, end=None, **kwargs) -> list[Signal]`

ゴールデンクロス・デッドクロスを検出。

**パラメータ**:
- `ticker` (`str`): 銘柄コード
- `short` (`int`): 短期MA期間（patternsがNoneの場合使用）
- `long` (`int`): 長期MA期間（patternsがNoneの場合使用）
- `patterns` (`list[tuple[int, int]] | None`): 検出パターンリスト

**戻り値**: `list[Signal]` - 日付順にソートされたSignalオブジェクトのリスト

##### `plot_chart(ticker, show_sma=None, show_bb=False, show_rsi=False, show_macd=False, show_signals=False, signal_patterns=None, start=None, end=None, **kwargs) -> go.Figure`

インタラクティブチャートを生成。

**パラメータ**:
- `ticker` (`str`): 銘柄コード
- `show_sma` (`list[int] | None`): 表示するSMA期間リスト
- `show_bb` (`bool`): ボリンジャーバンドを表示
- `show_rsi` (`bool`): RSIサブプロットを表示
- `show_macd` (`bool`): MACDサブプロットを表示
- `show_signals` (`bool`): クロスシグナルを表示
- `signal_patterns` (`list[tuple[int, int]] | None`): シグナル検出パターン

**戻り値**: `go.Figure` - Plotly Figureオブジェクト

##### `load_existing_analysis(ticker, db_path=None) -> dict[str, Any]`

既存の分析結果をデータベースから読み込み。

**パラメータ**:
- `ticker` (`str`): 銘柄コード
- `db_path` (`Path | str | None`): analysis_results.dbのパス（省略時は設定から取得）

**戻り値**: `dict` - `minervini`と`relative_strength`キーを持つ辞書

### Signal

シグナルデータクラス。

```python
from technical_tools import Signal
```

**属性**:
- `date` (`datetime`): シグナル発生日
- `signal_type` (`Literal["golden_cross", "dead_cross"]`): シグナル種別
- `price` (`float`): シグナル発生時の終値
- `short_period` (`int`): 短期MA期間
- `long_period` (`int`): 長期MA期間

### 例外クラス

| クラス | 説明 |
|--------|------|
| `TechnicalToolsError` | 基底例外クラス |
| `DataSourceError` | データ取得エラー |
| `TickerNotFoundError` | 銘柄が見つからない |
| `InsufficientDataError` | データ不足 |

### 指標計算関数 (`backend/technical_tools/indicators.py`)

低レベル関数（DataFrame直接操作）:

##### `add_sma(df, periods) -> pd.DataFrame`

単純移動平均を追加。

##### `add_ema(df, periods) -> pd.DataFrame`

指数移動平均を追加。

##### `add_rsi(df, period=14) -> pd.DataFrame`

RSIを追加。

##### `add_macd(df, fast=12, slow=26, signal=9) -> pd.DataFrame`

MACDを追加。

##### `add_bollinger_bands(df, period=20, std=2.0) -> pd.DataFrame`

ボリンジャーバンドを追加。

##### `calculate_indicators(df, indicators, ...) -> pd.DataFrame`

複数指標を一括計算。

**パラメータ**:
- `df` (`pd.DataFrame`): 'Close'カラムを持つDataFrame
- `indicators` (`list[str]`): 計算する指標リスト（"sma", "ema", "rsi", "macd", "bb"）
- `sma_periods` (`list[int] | None`): SMA期間（デフォルト: [5, 25, 75]）
- `ema_periods` (`list[int] | None`): EMA期間（デフォルト: [12, 26]）
- `rsi_period` (`int`): RSI期間（デフォルト: 14）
- `macd_fast` (`int`): MACD短期EMA（デフォルト: 12）
- `macd_slow` (`int`): MACD長期EMA（デフォルト: 26）
- `macd_signal` (`int`): MACDシグナル線（デフォルト: 9）
- `bb_period` (`int`): ボリンジャーバンド期間（デフォルト: 20）
- `bb_std` (`float`): ボリンジャーバンド標準偏差倍率（デフォルト: 2.0）

**戻り値**: `pd.DataFrame` - 指定した指標カラムが追加されたDataFrame

### シグナル検出関数 (`backend/technical_tools/signals.py`)

##### `detect_crosses(df, short=5, long=25) -> list[Signal]`

単一パターンのクロス検出。

##### `detect_crosses_multiple(df, patterns=None) -> list[Signal]`

複数パターンのクロス検出。

### データソース (`backend/technical_tools/data_sources/`)

#### DataSource (抽象基底クラス)

```python
from technical_tools.data_sources.base import DataSource
```

すべてのデータソースが実装すべきインターフェース。

##### `get_prices(ticker, start=None, end=None, **kwargs) -> pd.DataFrame`

株価データを取得。戻り値はOpen, High, Low, Close, Volume列を持つDataFrame。

#### JQuantsSource

```python
from technical_tools.data_sources.jquants import JQuantsSource
```

market_readerパッケージ経由でJ-Quantsデータにアクセス。株式分割を考慮した調整後価格（AdjustmentOpen/High/Low/Close/Volume）を使用してOHLCVデータを返す。

**サポートするperiod値**: 1mo, 3mo, 6mo, 1y, 2y, 5y

#### YFinanceSource

```python
from technical_tools.data_sources.yfinance import YFinanceSource
```

yfinanceライブラリ経由で米国株・国際株にアクセス。

**サポートするティッカー形式**:
- 米国株: AAPL, MSFT等
- 日本株: 7203.T, 9984.T等

---

## J-Quants モジュール (`backend/market_pipeline/jquants/`)

### JQuantsDataProcessor

日次株価データの取得と保存を担当。

```python
from market_pipeline.jquants.data_processor import JQuantsDataProcessor

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
from market_pipeline.jquants.statements_processor import JQuantsStatementsProcessor

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
from market_pipeline.jquants.fundamentals_calculator import FundamentalsCalculator

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

## 分析モジュール (`backend/market_pipeline/analysis/`)

### MinerviniConfig

ミネルヴィニ分析の設定クラス。

```python
from market_pipeline.analysis.minervini import MinerviniConfig

config = MinerviniConfig(base_dir=Path("/path/to/project"))
```

#### コンストラクタ

```python
MinerviniConfig(base_dir: Optional[Path] = None)
```

**パラメータ**:
- `base_dir`: プロジェクトルートディレクトリ（省略時はデフォルトパス）

**属性**:
- `base_dir`: プロジェクトルートディレクトリ
- `data_dir`: データディレクトリ (`base_dir/data`)
- `logs_dir`: ログディレクトリ (`base_dir/logs`)
- `output_dir`: 出力ディレクトリ (`base_dir/output`)
- `jquants_db_path`: J-Quants DB パス
- `results_db_path`: 分析結果DB パス
- `error_output_dir`: エラー出力ディレクトリ

### MinerviniAnalyzer

マーク・ミネルヴィニのトレンドスクリーニング戦略。ベクトル化演算による最適化実装。

```python
from market_pipeline.analysis.minervini import MinerviniAnalyzer, MinerviniConfig

config = MinerviniConfig()
analyzer = MinerviniAnalyzer(config)
results = analyzer.calculate_strategy_vectorized(df)
```

#### コンストラクタ

```python
MinerviniAnalyzer(config: MinerviniConfig)
```

**パラメータ**:
- `config`: MinerviniConfigインスタンス

#### メソッド

##### `calculate_strategy_vectorized(df: pd.DataFrame) -> pd.DataFrame`

ベクトル化演算によるミネルヴィニ条件の計算。

**パラメータ**:
- `df` (`pd.DataFrame`): DateインデックスとAdjustmentCloseカラムを持つDataFrame

**戻り値**: `pd.DataFrame` - 以下のカラムを含むDataFrame

| カラム | 説明 |
|--------|------|
| `Close` | 終値 |
| `Sma50` | 50日移動平均 |
| `Sma150` | 150日移動平均 |
| `Sma200` | 200日移動平均 |
| `Type_1` | 株価が150日・200日MAより上（1.0/0.0） |
| `Type_2` | 150日MAが200日MAより上（1.0/0.0） |
| `Type_3` | 200日MAが1ヶ月間上昇トレンド（1.0/0.0） |
| `Type_4` | 50日MAが150日・200日MAより上（1.0/0.0） |
| `Type_5` | 株価が50日MAより上（1.0/0.0） |
| `Type_6` | 株価が52週安値の130%以上（1.0/0.0） |
| `Type_7` | 株価が52週高値の75%以上（1.0/0.0） |
| `Type_8` | RSI >= 70（別途計算、初期値NaN） |

### MinerviniDatabase

ミネルヴィニ分析のデータベース操作クラス。

```python
from market_pipeline.analysis.minervini import MinerviniDatabase, MinerviniConfig

config = MinerviniConfig()
database = MinerviniDatabase(config)
database.init_database(source_db_path, dest_db_path, code_list)
```

#### コンストラクタ

```python
MinerviniDatabase(config: MinerviniConfig)
```

**パラメータ**:
- `config`: MinerviniConfigインスタンス

#### メソッド

##### `init_minervini_table(dest_db_path: str)`

Minerviniテーブルとインデックスを初期化。

##### `init_database(source_db_path: str, dest_db_path: str, code_list: List[str], n_workers: Optional[int] = None)`

全銘柄のMinerviniデータベースを並列処理で初期化。

##### `update_database(source_db_path: str, dest_db_path: str, code_list: List[str], calc_start_date: str, calc_end_date: str, period: int = 5)`

Minerviniデータベースを更新。

##### `update_type8(dest_db_path: str, date_list: List[str], period: int = -5)`

Type 8（相対力指数）をバッチ操作で更新。

### 後方互換関数

```python
from market_pipeline.analysis.minervini import init_minervini_db, update_minervini_db, update_type8_db

# 初期化（SQLite接続オブジェクト使用）
init_minervini_db(source_conn, dest_conn, code_list, n_workers)

# 更新
update_minervini_db(source_conn, dest_conn, code_list, calc_start_date, calc_end_date, period)

# Type 8更新
update_type8_db(conn, date_list, period)
```

### High-Low Ratio 関数 (`backend/market_pipeline/analysis/high_low_ratio.py`)

52週高値・安値位置比率の計算。関数ベースで実装。

```python
from market_pipeline.analysis.high_low_ratio import calc_hl_ratio_for_all, calc_hl_ratio_by_code

# 全銘柄のHL比率を計算
ratio_df = calc_hl_ratio_for_all(db_path, end_date, weeks=52)

# 特定銘柄のHL比率を計算
ratios, price_df = calc_hl_ratio_by_code("7203", db_path, end_date, weeks=52)
```

#### 関数

##### `init_hl_ratio_db(db_path=RESULTS_DB_PATH)`

HL比率テーブルを初期化。

**パラメータ**:
- `db_path`: 結果データベースのパス

##### `calc_hl_ratio_for_all(db_path=JQUANTS_DB_PATH, end_date=None, weeks=52, n_workers=None) -> pd.DataFrame`

全銘柄のHL比率を並列処理で計算。

**パラメータ**:
- `db_path`: jquants.dbのパス
- `end_date`: 計算終了日（省略時は当日）
- `weeks`: 計算期間（週数、デフォルト52週）
- `n_workers`: 並列ワーカー数（省略時は自動）

**戻り値**: `pd.DataFrame` - Code, HlRatio, MedianRatio, Date, Weeks

##### `calc_hl_ratio_by_code(code, db_path=JQUANTS_DB_PATH, end_date=None, weeks=52, save_to_db=True) -> Tuple[Dict, pd.DataFrame]`

特定銘柄のHL比率を計算。

**パラメータ**:
- `code` (`str`): 銘柄コード
- `db_path`: jquants.dbのパス
- `end_date`: 計算終了日
- `weeks`: 計算期間（週数）
- `save_to_db`: データベースに保存するか

**戻り値**: `Tuple[Dict, pd.DataFrame]` - ({'HlRatio': float, 'MedianRatio': float}, 価格DataFrame)

##### `calc_ratios_vectorized(df, weeks=52) -> pd.DataFrame`

ベクトル化されたHL比率計算（内部関数）。

**パラメータ**:
- `df`: Date, Code, High, Low, AdjustmentCloseカラムを持つDataFrame
- `weeks`: 計算期間（週数）

**戻り値**: `pd.DataFrame` - Code, HlRatio, MedianRatio

### Relative Strength 関数 (`backend/market_pipeline/analysis/relative_strength.py`)

相対力指標（RSP/RSI）の計算。関数ベースで実装。

```python
from market_pipeline.analysis.relative_strength import (
    init_rsp_db, update_rsp_db, update_rsi_db,
    relative_strength_percentage_vectorized
)

# RSPデータベースを初期化（全履歴計算）
processed, errors = init_rsp_db(db_path, result_db_path)

# RSPを更新（直近のみ）
processed, errors = update_rsp_db(db_path, result_db_path, calc_end_date="2024-01-01")

# RSIを更新（RSPからランキング計算）
errors = update_rsi_db(result_db_path)
```

#### 関数

##### `init_results_db(db_path)`

相対力結果テーブルを初期化。

##### `init_rsp_db(db_path=JQUANTS_DB_PATH, result_db_path=RESULTS_DB_PATH, n_workers=None) -> Tuple[int, int]`

全銘柄のRSPを初期計算してデータベースに保存。

**パラメータ**:
- `db_path`: jquants.dbのパス
- `result_db_path`: 結果データベースのパス
- `n_workers`: 並列ワーカー数

**戻り値**: `Tuple[int, int]` - (処理成功数, エラー数)

##### `update_rsp_db(db_path=JQUANTS_DB_PATH, result_db_path=RESULTS_DB_PATH, calc_start_date=None, calc_end_date=None, period=-5, n_workers=None) -> Tuple[int, int]`

直近のRSPを更新。

**パラメータ**:
- `db_path`: jquants.dbのパス
- `result_db_path`: 結果データベースのパス
- `calc_start_date`: 計算開始日
- `calc_end_date`: 計算終了日
- `period`: 更新期間（負数で直近N日）
- `n_workers`: 並列ワーカー数

**戻り値**: `Tuple[int, int]` - (処理成功数, エラー数)

##### `update_rsi_db(result_db_path=RESULTS_DB_PATH, date_list=None, period=-5) -> int`

RSI（相対力指数）を計算して更新。RSPを基にランキングを計算。

**パラメータ**:
- `result_db_path`: 結果データベースのパス
- `date_list`: 処理対象日リスト（省略時は自動取得）
- `period`: 更新期間

**戻り値**: `int` - エラー数

##### `relative_strength_percentage_vectorized(df, period=200) -> pd.DataFrame`

RSP（相対力パーセンテージ）をベクトル化計算。

**パラメータ**:
- `df`: Date インデックスと AdjustmentClose カラムを持つDataFrame
- `period`: 計算期間（日数）

**戻り値**: `pd.DataFrame` - RelativeStrengthPercentage カラムを追加したDataFrame

### OptimizedChartClassifier / ChartClassifier

MLベースのチャートパターン分類。テンプレートマッチングによるパターン検出。

```python
from market_pipeline.analysis.chart_classification import OptimizedChartClassifier, ChartClassifier

# OptimizedChartClassifier（推奨）
classifier = OptimizedChartClassifier(
    ticker="7203",
    window=60,
    price_data=price_series,  # オプション: 事前ロード済みデータ
    logger=logger
)
label, score, data_date = classifier.classify_latest()

# ChartClassifier（後方互換性ラッパー）
classifier = ChartClassifier(ticker="7203", window=60, db_path=db_path)
```

#### OptimizedChartClassifier コンストラクタ

```python
OptimizedChartClassifier(
    ticker: str,
    window: int,
    price_data: Optional[pd.Series] = None,
    logger: Optional[logging.Logger] = None
)
```

**パラメータ**:
- `ticker`: 銘柄コード
- `window`: 分析ウィンドウサイズ（20, 60, 120, 240, 960, 1200）
- `price_data`: 事前ロード済みの価格データ（省略時はDBから取得）
- `logger`: ロガーインスタンス

#### ChartClassifier コンストラクタ（後方互換）

```python
ChartClassifier(ticker: str, window: int, db_path: str = JQUANTS_DB_PATH)
```

**パラメータ**:
- `ticker`: 銘柄コード
- `window`: 分析ウィンドウサイズ
- `db_path`: jquants.dbのパス

#### メソッド

##### `classify_latest() -> Tuple[str, float, str]`

最新の価格データでチャートパターンを分類。

**戻り値**: `Tuple[str, float, str]` - (パターンラベル, 相関スコア, データ日付)

**パターンラベル**:
- `uptrend`: 上昇トレンド
- `downtrend`: 下降トレンド
- `double_bottom`: ダブルボトム
- `head_and_shoulders`: ヘッドアンドショルダーズ
- `その他のパターン`

##### `save_classification_plot(label, score, output_dir)`

分類結果のプロットを保存。

**パラメータ**:
- `label`: パターンラベル
- `score`: 相関スコア
- `output_dir`: 出力ディレクトリ

#### ヘルパー関数

##### `get_adaptive_windows(data_length: int) -> List[int]`

データ長に応じた適切なウィンドウサイズリストを返す。

##### `main_full_run_optimized()`

全銘柄の分類を実行するメイン関数（スクリプトから呼び出し）。

---

## マスターモジュール (`backend/market_pipeline/master/`)

### StockMasterDB

東証上場銘柄のマスター情報を管理するクラス。各データソース間の共通参照テーブルを提供。

```python
from market_pipeline.master.master_db import StockMasterDB

master_db = StockMasterDB(db_path="data/master.db")

# マスターデータを最新の東証情報で更新
master_db.update_master_data()

# 全銘柄を取得
stocks_df = master_db.get_all_stocks(active_only=True)

# 銘柄コードで検索
stock_info = master_db.get_stock_by_code("7203")

# 業種で検索
sector_stocks = master_db.get_stocks_by_sector("輸送用機器")

# 市場で検索
prime_stocks = master_db.get_stocks_by_market("プライム")

# 統計情報を取得
stats = master_db.get_statistics()
```

#### コンストラクタ

```python
StockMasterDB(db_path: str = None)
```

**パラメータ**:
- `db_path`: データベースファイルのパス（省略時は `data/master.db`）

#### メソッド

##### `update_master_data() -> bool`

東証上場銘柄一覧をダウンロードしてマスターデータを更新。

**戻り値**: `bool` - 更新成功時 True

##### `get_all_stocks(active_only: bool = True) -> pd.DataFrame`

全銘柄情報を取得。

**パラメータ**:
- `active_only`: アクティブな銘柄のみ取得するか

**戻り値**: `pd.DataFrame` - 銘柄情報（code, name, sector, market, market_product_category, yfinance_symbol, jquants_code, is_active）

##### `get_stock_by_code(code: str) -> Optional[Dict[str, Any]]`

銘柄コードから銘柄情報を取得。

**パラメータ**:
- `code`: 銘柄コード（4桁）

**戻り値**: `Dict[str, Any]` または `None`

##### `get_stocks_by_sector(sector: str, active_only: bool = True) -> pd.DataFrame`

業種で銘柄を取得。

**パラメータ**:
- `sector`: 業種名（33業種区分）
- `active_only`: アクティブな銘柄のみ取得するか

**戻り値**: `pd.DataFrame` - 該当銘柄情報

##### `get_stocks_by_market(market: str, active_only: bool = True) -> pd.DataFrame`

市場で銘柄を取得。

**パラメータ**:
- `market`: 市場名（プライム、スタンダード、グロース）
- `active_only`: アクティブな銘柄のみ取得するか

**戻り値**: `pd.DataFrame` - 該当銘柄情報

##### `get_statistics() -> Dict[str, Any]`

マスターデータの統計情報を取得。

**戻り値**: `Dict` - total_stocks, active_stocks, inactive_stocks, sector_distribution, market_distribution, last_updated

##### `download_tse_listed_stocks() -> Optional[str]`

東証上場銘柄一覧のExcelファイルをダウンロード（内部使用）。

##### `load_tse_stocks_from_excel(file_path: str) -> pd.DataFrame`

ExcelファイルからTSE上場銘柄データを読み込み（内部使用）。

---

## ユーティリティ (`backend/market_pipeline/utils/`)

### ParallelProcessor

並列処理のラッパークラス。

```python
from market_pipeline.utils.parallel_processor import ParallelProcessor

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
from market_pipeline.utils.parallel_processor import BatchDatabaseProcessor

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
- `on_conflict` (`str`): 競合時の処理（'REPLACE' | 'IGNORE' | 'ABORT' | 'ROLLBACK' | 'FAIL'）

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
from market_pipeline.utils.parallel_processor import measure_performance

@measure_performance
def my_function():
    # 処理
    pass
```

### CacheManager

メモリ・ディスクベースのキャッシュ管理クラス。

```python
from market_pipeline.utils.cache_manager import CacheManager, get_cache

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
