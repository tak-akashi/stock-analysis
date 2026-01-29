# ドキュメントレビューレポート

> 生成日時: 2026-01-29
> 対象: 全ファイル（docs/core/）

## サマリー

| 観点 | 評価 | 問題数 |
|------|------|--------|
| 完全性 | **B** | 2件 |
| 最新性 | **B** | 1件 |
| 正確性 | **C** | 5件 |
| 分かりやすさ | **A** | 0件 |
| 一貫性 | **B** | 2件 |
| **総合評価** | **C** | **10件** |

---

## 1. 完全性

### 未記載モジュール

| モジュール | 推奨対応 |
|------------|----------|
| `core/master/master_db.py` (`StockMasterDB`クラス) | api-reference.mdに追加 |

### 欠落ドキュメント

| ドキュメント | 推奨対応 |
|------------|----------|
| `glossary.md` | 用語集が未作成（推奨：`docs/core/glossary.md`を作成） |

---

## 2. 最新性

### 更新が必要なドキュメント

| ドキュメント | 問題 |
|--------------|----------|
| `CHANGELOG.md` | コミット `19ef3b3`（fix: bugfixes）が反映されていない |

---

## 3. 正確性

### コードとの乖離（重大）

| 項目 | ドキュメント記載 | 実際のコード | ファイル |
|------|--------------|------|----------|
| クラス名 | `HighLowRatioAnalyzer` | **クラスなし**（関数ベース） | api-reference.md:335-354 |
| クラス名 | `RelativeStrengthAnalyzer` | **クラスなし**（関数ベース） | api-reference.md:357-377 |

**詳細**: `api-reference.md`には`HighLowRatioAnalyzer`クラスと`RelativeStrengthAnalyzer`クラスが記載されていますが、実際の`core/analysis/high_low_ratio.py`と`core/analysis/relative_strength.py`にはこれらのクラスは存在しません。これらのモジュールは関数ベースで実装されています。

### その他の乖離

| 項目 | ドキュメント記載 | 実際 | ファイル |
|------|--------------|------|----------|
| ChartClassifierコンストラクタ | `mode: str = "full-optimized"` | modeパラメータなし（OptimizedChartClassifierを継承） | api-reference.md:393-398 |
| テストファイル | `tests/test_relative_strength.py` | 実際に存在 | repo-structure.md（OK） |
| テストファイル | `test_chart_classification.py` | 存在確認済み | repo-structure.md（OK） |

### README.mdとの整合性

| 項目 | 問題 |
|------|------|
| `core/analysis/integrated_analysis2.py`の実行コマンド | README.mdに記載のコマンドは正しい |

---

## 4. 分かりやすさ

### 評価結果

| 項目 | 評価 |
|------|------|
| 概要説明 | ✅ 各セクション冒頭に目的・概要あり |
| コード例 | ✅ 主要APIに使用例あり |
| パラメータ説明 | ✅ 全引数に説明あり |
| 戻り値説明 | ✅ 関数の戻り値に説明あり |

---

## 5. 一貫性

### 命名の統一

| 項目 | 出現パターン | 推奨 |
|------|--------------|------|
| ディレクトリ名 | `core/`, `backend/` | CHANGELOGに「backendをcoreにリネーム」と記載あり。ドキュメント全体で`core/`に統一済み（OK） |
| ドキュメントファイル名 | `dev-guidelines.md`と`development-guidelines.md` | 実際のファイル名は`dev-guidelines.md`。スキルのガイドでは`development-guidelines.md`を参照する可能性あり |
| ドキュメントファイル名 | `repo-structure.md`と`repository-structure.md` | 実際のファイル名は`repo-structure.md` |

### フォーマットの統一

| 問題 | 場所 | 推奨対応 |
|------|------|----------|
| テーブル形式 | 全ファイル | ✅ 統一済み |
| コードブロック | 全ファイル | ✅ 言語指定あり |

---

## 6. 改善提案

### 優先度: 高
- [ ] **api-reference.md**: `HighLowRatioAnalyzer`と`RelativeStrengthAnalyzer`クラスの記述を削除または修正（これらは関数ベースで実装されている）
- [ ] **api-reference.md**: 実際の関数インターフェース（`calculate_hl_ratio_for_stocks()`, `calculate_rsp_rsi_for_stocks()`等）を記載

### 優先度: 中
- [ ] **api-reference.md**: `ChartClassifier`のコンストラクタ記述を修正（modeパラメータの確認）
- [ ] **api-reference.md**: `StockMasterDB`クラスの追加
- [ ] **glossary.md**: 用語集を作成（RSP, RSI, HL比率, Minervini等の定義）

### 優先度: 低
- [ ] **CHANGELOG.md**: 最新コミットの反映
- [ ] **ファイル命名**: スキルガイドとの整合性を確認（dev-guidelines vs development-guidelines）

---

## 7. 次のアクション

1. **最優先**: `/update-docs`を実行して、api-reference.mdの誤ったクラス記述を修正
2. `HighLowRatioAnalyzer`と`RelativeStrengthAnalyzer`の記述を、実際の関数ベースのAPIに置き換え
3. 必要に応じて`glossary.md`を作成

---

## 補足: 確認された正確な実装

### high_low_ratio.py の主要関数
- `init_hl_ratio_db(db_path)` - DBテーブル初期化
- `calculate_hl_ratio_for_stocks(stock_codes, target_date, db_path)` - HL比率計算
- クラスベースのAnalyzerは存在しない

### relative_strength.py の主要関数
- `relative_strength_percentage_vectorized(df, period)` - RSP計算
- `calculate_rsp_rsi_for_stocks(stock_codes, target_date)` - RSP/RSI計算
- クラスベースのAnalyzerは存在しない

### minervini.py
- `MinerviniAnalyzer`クラス - ✅ドキュメント通り存在

---

## レビュー実施情報

| 項目 | 内容 |
|------|------|
| レビュー日 | 2026-01-29 |
| レビュー対象 | docs/core/*.md, README.md, CLAUDE.md |
| 確認したコード | core/**/*.py |
