# 要求内容

## 概要

pandas_datareaderライクなインターフェースを提供し、蓄積した株価データをJupyter Notebook上で簡単に活用できるようにする`stock_reader`パッケージを構築する。

## 背景

### 現状の課題

- J-Quants APIから収集したデータがSQLiteに蓄積されているが、分析時に毎回SQLを書く必要がある
- Jupyter Notebookでの探索的データ分析やチャート描画が手軽にできない
- 財務データや分析結果など複数のデータソースへのアクセスが統一されていない

### 解決したいこと

- pandas_datareaderのような直感的なAPIで株価データを取得できるようにする
- Jupyter Notebook上でのインタラクティブな分析ワークフローを実現する
- 将来的にチャート描画、テクニカル分析、バックテストへと機能を拡張する基盤を作る

## 実装対象の機能

### 1. DataReaderクラス

DB接続と設定を管理するメインクラス。

- `DataReader()`でデフォルト設定を使用したインスタンス生成
- `DataReader(db_path="custom/path.db")`でカスタムDBパスを指定可能
- `strict`パラメータでエラー時の挙動を制御（True: 例外、False: 警告+空DataFrame）

### 2. 価格データ取得 `get_prices()`

単一または複数銘柄の価格データをDataFrameで取得する。

- 単一銘柄指定: 通常のDataFrameを返却
- 複数銘柄指定: MultiIndex DataFrame（Date, Code）を返却
- `columns`パラメータでカラム選択（"simple" / "full" / リスト指定）
- 期間省略時はデフォルト値を適用（end=最新日付、start=5年前）

### 3. 銘柄コード正規化

- 4桁または5桁の銘柄コード入力を受け付け
- 出力は常に4桁に統一（末尾の"0"を除去）

### 4. エラーハンドリング

- `strict=True`: 存在しない銘柄や期間外データで例外を発生
- `strict=False`: 警告をログに出力し、空のDataFrameを返却

## 受け入れ条件

### パッケージ構成
- [x] `stock_reader`パッケージが`pip install -e .`でインストール可能
- [x] `DataReader`クラスがインスタンス化できる
- [x] `from stock_reader import DataReader`でインポートできる

### データ取得（単一銘柄）
- [x] `get_prices("7203")`で単一銘柄の価格データがDataFrameで取得できる
- [x] DataFrameのインデックスが`Date`（日付型）である
- [x] デフォルトカラム（simple）: Open, High, Low, Close, Volume, AdjustmentClose の6カラム

### データ取得（複数銘柄）
- [x] `get_prices(["7203", "9984"])`で複数銘柄がMultiIndex DataFrame（Date, Code）で取得できる
- [x] `df.loc["2024-01-01", "7203"]`形式でアクセスできる

### カラム選択
- [x] `columns="simple"`で6カラム（Open, High, Low, Close, Volume, AdjustmentClose）が取得できる
- [x] `columns="full"`で全カラムが取得できる（Date/Codeはインデックス）
- [x] `columns=["Open", "Close"]`でリスト指定ができる

### 期間指定
- [x] `start="2024-01-01", end="2024-12-31"`で期間指定ができる
- [x] `start`省略時は`end`の5年前が適用される
- [x] `end`省略時はDB内の最新日付が適用される

### 銘柄コード処理
- [x] 4桁コード（"7203"）が受け付けられる
- [x] 5桁コード（"72030"）が受け付けられ、内部で4桁に変換される
- [x] 出力DataFrameのCodeは4桁に統一される

### エラーハンドリング
- [x] `strict=True`で存在しない銘柄を指定すると`StockNotFoundError`が発生する
- [x] `strict=False`で存在しない銘柄を指定すると`UserWarning`付きで空DataFrameが返る
- [x] データベース接続エラー時に`DatabaseConnectionError`が発生する
- [x] 開始日が終了日より後の場合に`InvalidDateRangeError`が発生する

### テスト・動作確認
- [x] 単体テスト（tests/test_stock_reader.py）が存在し、全テストがパスする
- [x] Jupyter Notebookでのデモ（notebooks/stock_reader_demo.ipynb）が動作する

## 成功指標

- `get_prices()`呼び出しが1銘柄×1年分のデータ取得で500ms以内に完了する
- テストカバレッジ80%以上

## スコープ外

以下はこのフェーズでは実装しません:

- 財務データ（`statements.db`）の取得
- 分析結果（`analysis_results.db`）の取得
- チャート描画機能
- テクニカル指標計算
- バックテスト機能
- Web API化
- キャッシュ機構
- チャンク読み込み（大量データ対応）

## 参照ドキュメント

- `docs/ideas/20250129-stock-reader-data-interface.md` - 元アイデアファイル
- `docs/core/architecture.md` - アーキテクチャ設計書
- `docs/core/dev-guidelines.md` - 開発ガイドライン
- `docs/core/repo-structure.md` - リポジトリ構造
