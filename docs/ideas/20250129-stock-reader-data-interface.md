# Stock Reader - データ取得インターフェース

> 作成日: 2025-01-29
> ステータス: draft
> 優先度: P1

## 概要

蓄積した株価データをJupyter Notebook上で簡単に活用するための、pandas_datareaderライクなデータ取得インターフェースを構築する。

## 背景

### 現状の課題

- J-Quants APIから収集したデータがSQLiteに蓄積されているが、分析時に毎回SQLを書く必要がある
- Jupyter Notebookでの探索的データ分析やチャート描画が手軽にできない
- 財務データや分析結果など複数のデータソースへのアクセスが統一されていない

### 解決したいこと

- pandas_datareaderのような直感的なAPIで株価データを取得できるようにする
- Jupyter Notebook上でのインタラクティブな分析ワークフローを実現する
- 将来的にチャート描画、テクニカル分析、バックテストへと機能を拡張する基盤を作る

## 解決策

### アプローチ

クラスベースのAPI設計を採用し、`stock_reader`パッケージとして実装する。

```python
from stock_reader import DataReader

reader = DataReader()
df = reader.get_prices("7203", "2024-01-01", "2024-12-31")
```

### 設計方針

1. **クラスベースAPI**: 設定のカスタマイズと再利用が可能
2. **pandas_datareaderライクなインターフェース**: 学習コストを低減
3. **段階的な機能拡張**: Phase 1で価格データ、以降で財務・分析データへ拡張

### 代替案と比較

| 案 | メリット | デメリット | 採否 |
|----|---------|-----------|------|
| クラスベースAPI | 設定の再利用、拡張性が高い | 初期化が必要 | 採用 |
| 関数ベースAPI | シンプル、即座に使える | 設定の共有が困難 | 不採用 |
| ハイブリッド | 両方の利点 | 実装・保守コスト増 | 不採用 |

| 案 | メリット | デメリット | 採否 |
|----|---------|-----------|------|
| MultiIndex DataFrame | pandasの標準的な扱い、groupby等が使いやすい | 初見では扱いにくい | 採用 |
| 辞書形式 | 直感的、銘柄ごとの処理が容易 | 一括操作がしにくい | 不採用 |
| Panel形式（横持ち） | 銘柄間比較が容易 | 複数カラムの扱いが困難 | 不採用 |

## 実装する機能

### ロードマップ

| Phase | 機能 | 概要 |
|-------|------|------|
| 1 | データ取得インターフェース | 価格データ取得の基本機能（今回のスコープ） |
| 2 | データソース拡張 | 財務データ、分析結果の取得 |
| 3 | 可視化 | チャート描画ユーティリティ |
| 4 | テクニカル分析 | 移動平均、RSI、MACDなど |
| 5 | バックテスト | 売買シミュレーション |

### 機能1: DataReaderクラス

DB接続と設定を管理するメインクラス。

```python
from stock_reader import DataReader

# 基本利用
reader = DataReader()

# カスタム設定
reader = DataReader(
    db_path="custom/path/jquants.db",
    strict=True  # エラー時に例外を投げる（False: 空DataFrame + 警告）
)
```

**パラメータ:**
- `db_path`: データベースファイルのパス（省略時はデフォルト設定を使用）
- `strict`: エラー時の挙動（True: 例外、False: 警告+空DataFrame）

### 機能2: 価格データ取得 `get_prices()`

単一または複数銘柄の価格データをDataFrameで取得。

**単一銘柄:**
```python
df = reader.get_prices(
    code="7203",
    start="2024-01-01",
    end="2024-12-31",
    columns="simple"  # or "full" or ["Open", "High", "Low", "Close", "Volume"]
)
```

**複数銘柄（MultiIndex DataFrame）:**
```python
df = reader.get_prices(
    code=["7203", "9984"],
    start="2024-01-01",
    end="2024-12-31"
)

# 返却形式:
#                      Open    High    Low   Close   Volume
# Date       Code
# 2024-01-01 7203     2500    2550   2480    2520   1000000
#            9984    45000   45500  44800   45200    500000
```

**パラメータ:**
- `code`: 銘柄コード（文字列または文字列のリスト）
- `start`: 開始日（省略時: endの1年前）
- `end`: 終了日（省略時: 最新日付）
- `columns`: カラム選択（`"simple"` / `"full"` / リスト指定）

**カラムオプション:**

| オプション | 含まれるカラム |
|-----------|--------------|
| `"simple"` (デフォルト) | Open, High, Low, Close, Volume, AdjClose |
| `"full"` | 全カラム（売買代金、VWAP、前日比など） |
| リスト指定 | 任意のカラムを選択 |

### 機能3: 銘柄コード正規化

- 入力: 4桁（`"7203"`）でも5桁（`"72030"`）でも受け付け
- 出力: 4桁に統一

### 機能4: エラーハンドリング

strictモードで挙動を制御。

```python
# strictモード（デフォルト: False）
reader = DataReader(strict=True)   # 例外を投げる
reader = DataReader(strict=False)  # 空DataFrame + 警告
```

### Phase 2以降（将来）

#### 財務データ取得
```python
fundamentals = reader.get_fundamentals("7203")
```

#### 分析結果取得
```python
analysis = reader.get_analysis("7203", "minervini")
```

#### チャート描画
```python
from stock_reader import plot_chart
plot_chart(df)  # mplfinance統合
```

#### テクニカル分析
```python
df = reader.get_prices("7203")
df["SMA20"] = df["Close"].rolling(20).mean()
# または組み込みメソッド
df_with_indicators = reader.add_indicators(df, ["SMA20", "RSI14"])
```

#### バックテスト
```python
from stock_reader import Backtester
bt = Backtester(df)
result = bt.run(strategy)
```

## 受け入れ条件

### パッケージ構成
- [ ] `stock_reader`パッケージが`pip install -e .`でインストール可能
- [ ] `DataReader`クラスがインスタンス化できる

### データ取得
- [ ] `get_prices()`で単一銘柄の価格データがDataFrameで取得できる
- [ ] `get_prices()`で複数銘柄を指定するとMultiIndex DataFrameで取得できる
- [ ] `columns`パラメータでカラム選択ができる（simple/full/リスト）
- [ ] 期間を省略した場合、デフォルト値（end=最新、start=1年前）が適用される

### 銘柄コード処理
- [ ] 4桁/5桁の銘柄コードどちらでも受け付け、出力は4桁に統一される

### エラーハンドリング
- [ ] `strict=True`で存在しない銘柄を指定すると例外が発生する
- [ ] `strict=False`で存在しない銘柄を指定すると警告付きで空DataFrameが返る

### テスト・動作確認
- [ ] Jupyter Notebookでの動作確認ができる
- [ ] 単体テストが存在する

## スコープ外

### 今回対象外
- 財務データ（`statements.db`）の取得
- 分析結果（`analysis_results.db`）の取得
- チャート描画機能
- テクニカル指標計算
- バックテスト機能

### 将来対応予定
- Web API化
- キャッシュ機構
- チャンク読み込み（大量データ対応）

## 技術的考慮事項

### ディレクトリ構成

```
stock-analysis/
├── stock_reader/           # 新規パッケージ
│   ├── __init__.py
│   ├── reader.py           # DataReaderクラス
│   └── utils.py            # ユーティリティ関数
├── tests/
│   └── test_stock_reader.py
└── notebooks/
    └── stock_reader_demo.ipynb  # 使用例
```

### 既存コードとの関係

- `backend/config/`の設定システムを再利用（DBパス取得など）
- `data/jquants.db`の`daily_quotes`テーブルを参照
- 既存の分析モジュールとは独立（将来的に統合可能）

### 依存コンポーネント

| コンポーネント | 用途 |
|--------------|------|
| pandas | DataFrame操作 |
| sqlite3 | データベースアクセス（標準ライブラリ） |
| warnings | 警告出力（標準ライブラリ） |
| backend/config | 設定値の取得 |

### パフォーマンス考慮

- 大量データ取得時のメモリ使用量に注意
- 必要に応じてチャンク読み込みを検討（Phase 1ではスコープ外）

### リスクと対策

| リスク | 影響度 | 対策 |
|-------|--------|------|
| daily_quotesテーブルのスキーマ変更 | 高 | カラムマッピングを設定ファイル化 |
| 大量銘柄取得時のメモリ不足 | 中 | 警告表示 + 将来的にチャンク対応 |
| 銘柄コード形式の不整合 | 低 | 正規化処理で吸収 |

## 更新履歴

- 2025-01-29: 初版作成（ブレインストーミングセッション）
