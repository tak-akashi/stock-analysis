# 変更履歴

このファイルはgitログから自動生成されました。

## [Unreleased]

### Fixed
- `backend/technical_tools/data_sources/jquants.py`: 株式分割を考慮した調整後価格（AdjustmentOpen/High/Low/Close/Volume）を使用するように修正
  - 以前は未調整価格（Open/High/Low/Close/Volume）を使用していたため、株式分割時にチャートにギャップが生じていた

### Added
- `backend/market_reader/` パッケージ: pandas_datareader風のデータアクセスAPI（旧 `stock_reader/`）
  - `DataReader`クラス: コンストラクタで `db_path` と `strict` パラメータをサポート
  - `get_prices()`: 単一/複数銘柄対応、日付自動デフォルト（end=DB最新日、start=5年前）
  - カラム選択: "simple"（OHLCV + AdjustmentClose）、"full"（全16カラム）、カスタムリスト
  - 4/5桁コード自動正規化（出力は常に4桁）
  - カスタム例外クラス: `StockReaderError`, `StockNotFoundError`, `DatabaseConnectionError`, `InvalidDateRangeError`
  - ユーティリティ関数: `normalize_code()`, `to_5digit_code()`, `validate_date()`
  - PRAGMA最適化（WALモード、キャッシュ設定）
- `notebooks/` ディレクトリ: 分析・可視化用Jupyterノートブック
- `py.typed` マーカーファイル: PEP 561準拠の型ヒントサポート
  - `backend/market_pipeline/py.typed`
  - `backend/market_reader/py.typed`
- パフォーマンスベンチマークファイル（テストから分離）:
  - `tests/benchmark_integrated_analysis_optimization.py`
  - `tests/benchmark_jquants_performance.py`
  - `tests/benchmark_optimizations.py`

### Changed
- yfinanceからJ-Quantsデータ計算への切り替え (`refactor/yfinance-to-jquants`ブランチ)
- FundamentalsCalculator: J-Quantsデータを使用した財務指標計算への移行
- ドキュメント構造の再編成（`docs/refs/`、`docs/core/`）
- リポジトリ構造のリファクタリング:
  - `core/` → `backend/market_pipeline/` へ移動
  - `stock_reader/` → `backend/market_reader/` へ移動
- `notebook/` を `notebooks/` にリネーム
- テストファイルの整理:
  - パフォーマンステストを `benchmark_*.py` に分離
  - `test_functions.py` を削除（機能を他のテストに統合）

### Removed
- `tests/test_functions.py` - 他のテストファイルに統合
- `tests/test_integrated_analysis_optimization.py` - ベンチマークに移行
- `tests/test_jquants_performance.py` - ベンチマークに移行
- `tests/test_optimizations.py` - ベンチマークに移行

---

## 最近のコミット履歴

### 19ef3b3 - バグ修正
- **タイプ**: fix
- **概要**: 各種バグの修正

### 6703a19 - yfinanceからjquantsデータ計算への切り替え
- **タイプ**: refactor
- **スコープ**: yfinance-to-jquants
- **概要**: yfinanceからJ-Quantsへのデータソース移行

### 86b372f - config設定の導入
- **概要**: Pydantic Settings ベースの設定システム導入
- 環境変数からの設定読み込み
- 型安全な設定アクセス

### a6c22b9 - ファイル名変更
- **概要**: `*_optimized.py` を `*.py` にリネーム
- 最適化版をメインバージョンとして採用

### 06b0118 - chart_classificationを週次から日次タスクへ移動
- **概要**: チャート分類処理の実行タイミング変更
- 週次実行から日次実行へ

### 70b589e - パフォーマンス問題の解決とその他更新
- **概要**: 処理時間の大幅短縮（5時間 → 15-20分）
- 並列処理の導入
- バッチ処理の最適化
- データベースインデックスの追加

### b2eb89f - get_refresh_token関数の追加
- **スコープ**: jquants/data_processing.py
- **概要**: J-Quants API認証のリフレッシュトークン取得機能

### 472fb3b - その他更新
- 軽微な修正とコード改善

### 5ef870e - その他更新
- 軽微な修正とコード改善

### cd230ae - その他更新
- 軽微な修正とコード改善

### 38a9118 - integrated_analysis2.pyの追加とREADME更新
- **概要**: Excel出力機能の追加
- READMEドキュメントの更新

### cf38fb6 - バグ修正とノートブック追加
- **概要**: 各種バグの修正
- Jupyterノートブックの追加

### 55ee88c - バグ修正とテストスクリプト更新
- **概要**: バグ修正
- テストスクリプトの改善

### 340763b - 分析機能とテスト機能の追加
- **概要**: 新しい分析アルゴリズムの実装
- テストカバレッジの拡充

### 7bd2483 - READMEの更新
- **タイプ**: Docs
- **概要**: 新しい分析機能と使用方法の説明を追加

### 07e1cb1 - バグ修正
- **概要**: 各種バグの修正

### f50576a - 初期コミット
- **概要**: プロジェクトの初期セットアップ

---

## 主要マイルストーン

### パフォーマンス最適化 (70b589e)
処理時間を5時間から15-20分に短縮（約15-20倍の高速化）

**採用した最適化技術:**
1. 並列処理 (ProcessPoolExecutor)
2. 非同期API呼び出し (aiohttp)
3. バッチデータベース操作
4. ベクトル化計算 (NumPy/Pandas)
5. テンプレートキャッシュ
6. データベースインデックス

### 設定システム導入 (86b372f)
Pydantic Settingsベースの型安全な設定管理システム導入

**機能:**
- 環境変数からの自動読み込み
- 階層的な設定構造
- シングルトンパターン

### yfinance → J-Quants移行 (6703a19)
データソースをyfinanceからJ-Quants APIに完全移行

**理由:**
- より信頼性の高いデータソース
- 財務諸表データの統合
- 日本株市場に特化

---

## バージョン命名規則

このプロジェクトは現在開発中であり、正式なバージョン番号は付与されていません。

将来的には[セマンティックバージョニング](https://semver.org/lang/ja/)を採用予定:
- MAJOR: 後方互換性のないAPI変更
- MINOR: 後方互換性のある機能追加
- PATCH: 後方互換性のあるバグ修正
