# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを`[x]`にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 「実装が複雑すぎるため後回し」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

### 実装可能なタスクのみを計画
- 計画段階で「実装可能なタスク」のみをリストアップ
- 「将来やるかもしれないタスク」は含めない
- 「検討中のタスク」は含めない

### タスクスキップが許可される唯一のケース
以下の技術的理由に該当する場合のみスキップ可能:
- 実装方針の変更により、機能自体が不要になった
- アーキテクチャ変更により、別の実装方法に置き換わった
- 依存関係の変更により、タスクが実行不可能になった

スキップ時は必ず理由を明記:
```markdown
- [x] ~~タスク名~~（実装方針変更により不要: 具体的な技術的理由）
```

### タスクが大きすぎる場合
- タスクを小さなサブタスクに分割
- 分割したサブタスクをこのファイルに追加
- サブタスクを1つずつ完了させる

---

## フェーズ0: backend → core リネーム

- [x] backend/ を core/ にリネーム
  - [x] `mv backend core` でディレクトリ名変更
  - [x] 全ての `from backend.` → `from core.` に置換（約51箇所）
  - [x] `CLAUDE.md` の参照を更新
  - [x] `docs/core/` 内のドキュメントを更新
  - [x] テスト実行で動作確認（`uv run pytest`）
  - [x] リント確認（`uv run ruff check .`）

## フェーズ1: パッケージ基盤構築

- [x] stock_reader/ディレクトリを作成
  - [x] `stock_reader/__init__.py` を作成（DataReader, 例外クラスをエクスポート）
  - [x] `stock_reader/exceptions.py` を作成
    - [x] `StockReaderError` 基底例外クラス
    - [x] `StockNotFoundError` 銘柄未発見例外
    - [x] `DatabaseConnectionError` DB接続エラー例外
    - [x] `InvalidDateRangeError` 日付範囲エラー例外

- [x] stock_reader/utils.py を作成
  - [x] `normalize_code(code: str) -> str` 関数（5桁→4桁変換）
  - [x] `validate_date(date_str: str | None) -> datetime | None` 関数
  - [x] `get_default_end_date(conn) -> datetime` 関数（DB最新日付取得）
  - [x] `get_default_start_date(end_date) -> datetime` 関数（5年前計算）

## フェーズ2: DataReaderクラス実装

- [x] stock_reader/reader.py を作成
  - [x] `SIMPLE_COLUMNS` 定数定義
  - [x] `FULL_COLUMNS` 定数定義
  - [x] `__init__(self, db_path, strict)` メソッド
    - [x] db_path=Noneの場合はcore/configから取得
    - [x] strictモードフラグの保持
  - [x] `_get_connection(self)` メソッド（コンテキストマネージャー）
    - [x] PRAGMA設定適用
  - [x] `_build_query(self, codes, start, end, columns)` メソッド
    - [x] 単一銘柄/複数銘柄の条件分岐
    - [x] カラム選択処理（simple/full/list）
    - [x] パラメータバインディング用のプレースホルダ生成
  - [x] `get_prices(self, code, start, end, columns)` メソッド
    - [x] 銘柄コード正規化
    - [x] 日付バリデーションとデフォルト値設定
    - [x] クエリ実行とDataFrame変換
    - [x] 単一銘柄: Dateインデックス
    - [x] 複数銘柄: MultiIndex(Date, Code)
    - [x] strictモードによるエラーハンドリング分岐

## フェーズ3: テスト実装

- [x] tests/test_stock_reader.py を作成
  - [x] `mock_database` フィクスチャ（一時DBにテストデータ挿入）
  - [x] `test_normalize_code_4digit` - 4桁コードがそのまま返る
  - [x] `test_normalize_code_5digit` - 5桁コードが4桁に変換される
  - [x] `test_validate_date_valid` - 正常な日付文字列がdatetimeに変換される
  - [x] `test_validate_date_invalid` - 不正な日付でValueError
  - [x] `test_get_prices_single_code` - 単一銘柄取得
  - [x] `test_get_prices_multiple_codes` - 複数銘柄取得（MultiIndex確認）
  - [x] `test_get_prices_columns_simple` - simpleカラム取得
  - [x] `test_get_prices_columns_full` - fullカラム取得
  - [x] `test_get_prices_columns_list` - リストでカラム指定
  - [x] `test_get_prices_default_dates` - 日付省略時のデフォルト
  - [x] `test_strict_mode_stock_not_found` - strict=TrueでStockNotFoundError発生
  - [x] `test_non_strict_mode_stock_not_found` - strict=Falseで空DataFrame+UserWarning
  - [x] `test_invalid_date_range` - 開始日>終了日でInvalidDateRangeError発生
  - [x] `test_database_connection_error` - 不正なDBパスでDatabaseConnectionError発生

## フェーズ4: パッケージ登録

- [x] pyproject.toml に stock_reader パッケージを登録
  - [x] `[project.scripts]` または `[tool.setuptools.packages]` に追加
  - [x] editable install が可能であることを確認

## フェーズ5: デモNotebook作成

- [x] notebooks/stock_reader_demo.ipynb を作成
  - [x] セル1: パッケージのインポートと初期化
  - [x] セル2: 単一銘柄データ取得の例
  - [x] セル3: 複数銘柄データ取得の例（MultiIndex操作）
  - [x] セル4: カラム選択の例（simple/full/list）
  - [x] セル5: 期間指定の例
  - [x] セル6: エラーハンドリングの例（strict=True/False）

## フェーズ6: 品質チェックと修正

- [x] すべてのテストが通ることを確認
  - [x] `uv run pytest tests/test_stock_reader.py -v`
- [x] リントエラーがないことを確認
  - [x] `uv run ruff check stock_reader/`
- [x] 型エラーがないことを確認
  - [x] `uv run mypy stock_reader/`
- [x] editable installが成功することを確認
  - [x] `uv pip install -e .`
  - [x] Pythonから`from stock_reader import DataReader`が成功

## フェーズ7: ドキュメント更新

- [x] CLAUDE.md を更新
  - [x] stock_readerパッケージの説明を追加
  - [x] 使用例を追加
- [x] README.md を更新（必要に応じて）
  - [x] ~~stock_readerの概要を追加~~ (README.mdは既存構造を維持、CLAUDE.mdに追加で十分)
- [x] 実装後の振り返り（このファイルの下部に記録）

---

## 実装後の振り返り

### 実装完了日
2026-01-29

### 計画と実績の差分

**計画と異なった点**:
- `to_5digit_code()` ヘルパー関数を追加（設計書にはなかったが、DB側が5桁コードを使用しているため必要になった）
- カラム名のホワイトリスト検証を追加（品質検証サブエージェントからの指摘で追加）
- mypyの型エラー対応として、validate_dateの返り値チェックを強化

**新たに必要になったタスク**:
- テストファイルの未使用インポート削除（ruff指摘）
- 無効カラム名テスト、空DBテストの追加（品質検証で推奨された追加テスト）

**技術的理由でスキップしたタスク**:
- なし（全タスク完了）

### 学んだこと

**技術的な学び**:
- `dateutil.relativedelta`を使用することで、1年前の日付計算が簡潔に書ける
- SQLiteのPRAGMA設定でリード性能を最適化できる（WALモード、cache_size等）
- mypyの型推論ではUnion型の分岐後も型が絞られない場合があり、明示的な型宣言が必要
- パラメータバインディング（`?`プレースホルダー）でSQLインジェクションを防止

**プロセス上の改善点**:
- tasklist.mdを細かいサブタスクに分割したことで進捗が把握しやすかった
- 品質検証サブエージェントの活用により、未使用インポートやセキュリティ強化ポイントを発見できた
- フェーズ0でのbackend→coreリネームを先に行ったことで、後続の実装がスムーズに進んだ

### 次回への改善提案
- テストファイル作成時に未使用インポートを残さないよう注意
- カラム名等のユーザー入力はホワイトリスト検証を最初から組み込む
- mypy対応は実装と並行して行い、最後にまとめて修正しないようにする
- design.mdにDB側のコード形式（5桁）も明記しておくと実装時の混乱を防げる
