# 設計書

## アーキテクチャ概要

stock_readerは既存のstock-analysisシステムとは独立した読み取り専用のデータアクセスレイヤーとして設計する。
既存の`core/config/`設定システムを再利用し、データベースへの依存を最小限に抑える。

**注**: 実装に先立ち、`backend/` → `core/` へのリネームを行う。

```
┌─────────────────────────────────────────────────────────────────┐
│                    Jupyter Notebook / Python Script             │
│                                                                 │
│  from stock_reader import DataReader                            │
│  reader = DataReader()                                          │
│  df = reader.get_prices("7203", "2024-01-01", "2024-12-31")     │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                        stock_reader Package                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ DataReader (reader.py)                                       │ │
│  │  - __init__(db_path, strict)                                 │ │
│  │  - get_prices(code, start, end, columns)                     │ │
│  │  - _normalize_code(code)                                     │ │
│  │  - _get_connection()                                         │ │
│  │  - _build_query()                                            │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│                             │                                     │
│  ┌──────────────────────────▼──────────────────────────────────┐ │
│  │ utils.py                                                     │ │
│  │  - normalize_code(code: str) -> str                          │ │
│  │  - validate_date(date: str) -> datetime                      │ │
│  │  - get_default_dates() -> tuple[datetime, datetime]          │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬───────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                     core/config (既存)                         │
│  get_settings() → settings.paths.jquants_db                       │
└───────────────────────────────┬───────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                     data/jquants.db                               │
│  daily_quotes テーブル                                            │
│  - Date, Code, Open, High, Low, Close, Volume, AdjustmentClose... │
└───────────────────────────────────────────────────────────────────┘
```

## コンポーネント設計

### 1. DataReader クラス (stock_reader/reader.py)

**責務**:
- データベース接続の管理
- 株価データの取得とDataFrame変換
- 銘柄コード・期間のバリデーション
- カラム選択の処理

**実装の要点**:
- コンテキストマネージャーによるDB接続管理（`with get_connection() as conn`）
- PRAGMA設定を適用してクエリパフォーマンスを最適化
- pd.read_sql_queryでDataFrame直接取得

**クラス設計**:
```python
class DataReader:
    """株価データ取得のためのメインインターフェース"""

    # カラムマッピング定義
    SIMPLE_COLUMNS = ["Open", "High", "Low", "Close", "Volume", "AdjustmentClose"]
    FULL_COLUMNS = [
        "Date", "Code", "Open", "High", "Low", "Close",
        "UpperLimit", "LowerLimit", "Volume", "TurnoverValue",
        "AdjustmentFactor", "AdjustmentOpen", "AdjustmentHigh",
        "AdjustmentLow", "AdjustmentClose", "AdjustmentVolume"
    ]

    def __init__(
        self,
        db_path: str | Path | None = None,
        strict: bool = False
    ) -> None:
        """
        Args:
            db_path: jquants.dbへのパス。Noneの場合はcore/configの設定を使用
            strict: True=エラー時に例外、False=警告+空DataFrame
        """

    def get_prices(
        self,
        code: str | list[str],
        start: str | None = None,
        end: str | None = None,
        columns: str | list[str] = "simple"
    ) -> pd.DataFrame:
        """株価データを取得"""
```

### 2. ユーティリティモジュール (stock_reader/utils.py)

**責務**:
- 銘柄コードの正規化（5桁→4桁変換）
- 日付文字列のバリデーションと変換
- デフォルト期間の計算

**実装の要点**:
- 純粋関数として実装（副作用なし）
- 型ヒントによる明確なインターフェース

**関数設計**:
```python
def normalize_code(code: str) -> str:
    """銘柄コードを4桁形式に正規化

    Args:
        code: 4桁または5桁の銘柄コード
    Returns:
        4桁の銘柄コード
    Examples:
        >>> normalize_code("7203")
        '7203'
        >>> normalize_code("72030")
        '7203'
    """

def validate_date(date_str: str | None) -> datetime | None:
    """日付文字列をdatetimeに変換・バリデーション

    Args:
        date_str: 'YYYY-MM-DD'形式の日付文字列、またはNone
    Returns:
        datetimeオブジェクト、またはNone
    Raises:
        ValueError: 不正な日付形式の場合
    """

def get_default_end_date(conn: sqlite3.Connection) -> datetime:
    """DBから最新日付を取得"""

def get_default_start_date(end_date: datetime) -> datetime:
    """end_dateの5年前を返却"""
```

## データフロー

### 単一銘柄のデータ取得

```
1. reader.get_prices("7203", "2024-01-01", "2024-12-31")
2. normalize_code("7203") → "7203"
3. validate_date("2024-01-01") → datetime(2024, 1, 1)
4. validate_date("2024-12-31") → datetime(2024, 12, 31)
5. _build_query(code, start, end, columns)
   → SELECT Date, Open, High, Low, Close, Volume, AdjustmentClose
     FROM daily_quotes
     WHERE Code = '72030' AND Date BETWEEN '2024-01-01' AND '2024-12-31'
     ORDER BY Date
6. pd.read_sql_query(query, conn, parse_dates=["Date"], index_col="Date")
7. DataFrame返却
```

### 複数銘柄のデータ取得

```
1. reader.get_prices(["7203", "9984"], "2024-01-01", "2024-12-31")
2. [normalize_code(c) for c in ["7203", "9984"]] → ["7203", "9984"]
3. _build_query(codes, start, end, columns)
   → SELECT Date, Code, Open, ...
     FROM daily_quotes
     WHERE Code IN ('72030', '99840') AND Date BETWEEN ...
     ORDER BY Date, Code
4. pd.read_sql_query(query, conn, parse_dates=["Date"])
5. df.set_index(["Date", "Code"]) → MultiIndex DataFrame
6. Code列を4桁に正規化
7. DataFrame返却
```

## エラーハンドリング戦略

### カスタムエラークラス

```python
class StockReaderError(Exception):
    """stock_readerの基底例外クラス"""

class StockNotFoundError(StockReaderError):
    """指定された銘柄コードが見つからない場合"""
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Stock code not found: {code}")

class DatabaseConnectionError(StockReaderError):
    """データベース接続に失敗した場合"""

class InvalidDateRangeError(StockReaderError):
    """無効な日付範囲が指定された場合"""
```

### エラーハンドリングパターン

**strict=True（デフォルト: False）の場合**:
```python
# 銘柄が見つからない
raise StockNotFoundError(code)

# 日付が不正
raise InvalidDateRangeError(f"Start date {start} is after end date {end}")
```

**strict=False（デフォルト）の場合**:
```python
import warnings

# 銘柄が見つからない
warnings.warn(f"No data found for stock code: {code}", UserWarning)
return pd.DataFrame()  # 空のDataFrame

# 一部銘柄のみデータなし
warnings.warn(f"No data found for: {missing_codes}", UserWarning)
# 取得できた銘柄のみ返却
```

## テスト戦略

### ユニットテスト

**test_stock_reader.py**:
- `test_normalize_code`: 4桁/5桁コードの正規化
- `test_validate_date`: 日付バリデーション（正常系・異常系）
- `test_get_prices_single`: 単一銘柄取得
- `test_get_prices_multiple`: 複数銘柄取得（MultiIndex）
- `test_get_prices_columns`: カラム選択（simple/full/list）
- `test_get_prices_default_dates`: 日付省略時のデフォルト値
- `test_strict_mode_not_found`: strict=Trueでのエラー発生
- `test_non_strict_mode_not_found`: strict=Falseでの警告と空DataFrame

### テストフィクスチャ

```python
@pytest.fixture
def mock_database(tmp_path):
    """テスト用の一時的なSQLiteデータベースを作成"""
    db_path = tmp_path / "test_jquants.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE daily_quotes (
            Date TEXT, Code TEXT, Open REAL, High REAL,
            Low REAL, Close REAL, Volume REAL,
            AdjustmentClose REAL, ...
        )
    """)
    # テストデータ挿入
    conn.executemany(
        "INSERT INTO daily_quotes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("2024-01-01", "72030", 2500.0, 2550.0, 2480.0, 2520.0, 1000000.0, 2520.0),
            ("2024-01-02", "72030", 2520.0, 2600.0, 2510.0, 2580.0, 1200000.0, 2580.0),
            # ...
        ]
    )
    conn.commit()
    conn.close()
    return db_path
```

### 統合テスト

- 実際のjquants.dbを使用した動作確認（スキップ可能にマーク）
- Jupyter Notebookでのインタラクティブテスト

## 依存ライブラリ

既存の依存のみ使用（新規追加なし）:

```toml
# pyproject.toml（追記不要、既存依存を使用）
[project]
dependencies = [
    "pandas>=2.0.0",  # 既存
    "pydantic-settings>=2.0.0",  # 既存（core/configで使用）
]
```

## ディレクトリ構造

```
stock-analysis/
├── core/                            # 内部エンジン（旧backend）
│   ├── analysis/                    # 分析アルゴリズム
│   ├── config/                      # 設定管理
│   ├── jquants/                     # API連携
│   └── utils/                       # ユーティリティ
├── stock_reader/                    # 新規パッケージ（ユーザー向けAPI）
│   ├── __init__.py                  # DataReader, エラークラスをエクスポート
│   ├── reader.py                    # DataReaderクラス本体
│   ├── utils.py                     # ユーティリティ関数
│   └── exceptions.py                # カスタム例外クラス
├── scripts/                         # 実行スクリプト
├── tests/
│   └── test_stock_reader.py         # 新規テストファイル
├── notebooks/
│   └── stock_reader_demo.ipynb      # 新規デモNotebook
└── pyproject.toml                   # stock_readerパッケージ登録を追加
```

## 実装の順序

1. **基盤構築**: stock_reader/ディレクトリ作成、__init__.py
2. **例外クラス**: exceptions.py（StockReaderError, StockNotFoundError, etc.）
3. **ユーティリティ**: utils.py（normalize_code, validate_date）
4. **メインクラス**: reader.py（DataReader.__init__, get_prices）
5. **テスト**: test_stock_reader.py（ユニットテスト全量）
6. **パッケージ登録**: pyproject.tomlへの追記
7. **デモNotebook**: stock_reader_demo.ipynb
8. **品質チェック**: pytest, ruff, mypy

## セキュリティ考慮事項

- SQLインジェクション対策: パラメータバインディングを使用
  ```python
  # NG: f-string直接埋め込み
  query = f"SELECT * FROM daily_quotes WHERE Code = '{code}'"

  # OK: パラメータバインディング
  query = "SELECT * FROM daily_quotes WHERE Code = ?"
  pd.read_sql_query(query, conn, params=[code])
  ```
- ファイルパスの検証: db_pathが期待されるディレクトリ内にあることを確認

## パフォーマンス考慮事項

- データベースインデックス: `idx_daily_quotes_code`, `idx_daily_quotes_date`を活用
- PRAGMA設定: WALモード、適切なキャッシュサイズ
- 大量銘柄取得時: IN句の銘柄数上限は設けないが、1000件超の場合に警告表示を検討
- DataFrameへの直接読み込み: `pd.read_sql_query`でメモリ効率を確保

## 将来の拡張性

Phase 2以降に向けた設計考慮:

1. **データソース追加**: `DataReader`に`get_fundamentals()`, `get_analysis()`メソッドを追加可能
2. **キャッシュ機構**: `@lru_cache`または独自キャッシュレイヤーを追加可能
3. **非同期対応**: `get_prices_async()`メソッドを追加可能（aiohttpパターン流用）
4. **設定の拡張**: `core/config/settings.py`に`StockReaderSettings`を追加可能
