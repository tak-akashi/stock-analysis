# テスト失敗・エラー修正計画

## 概要

validation-reportとacceptance-test-reportで指摘された23件のテスト失敗と29件のエラーを修正します。

## 問題と修正方針

### 1. tests/test_functions.py - 削除

**問題**: 存在しない関数`update_type8_db_by_date`のインポート（9行目）

**分析**:
- ハードコードされた絶対パス使用（本番DB直接アクセス）
- pytestテストではなく手動実行スクリプト
- 同等機能は`test_minervini.py`でカバー済み

**修正**: ファイルを削除

---

### 2. tests/test_integrated_analysis.py - カラム名統一（16件失敗）

**問題**: テストと実装でカラム名が不一致
- 実装側: `HlRatio` (大文字) - high_low_ratio.py:53, integrated_analysis.py:60
- テスト側: `hl_ratio` (小文字) - test_integrated_analysis.py:35, 78, 144, 159等

**修正箇所**:
1. CREATE TABLE文のカラム名を大文字に変更（32-68行）
2. INSERT文のカラム名を大文字に変更（78, 92-95, 111-114, 117-121行）
3. アサーションのカラム名を大文字に変更（144, 150, 159, 197, 198, 208, 209, 220行等）

---

### 3. tests/test_chart_classification.py - @patchパス修正（4件失敗）

**問題**: @patchデコレータのパスが間違っている
- 現在: `@patch('chart_classification.XXX')`
- 正しいパス: `@patch('market_pipeline.analysis.chart_classification.XXX')`

**修正箇所**:
- 135行: `@patch('chart_classification.ChartClassifier')` → `@patch('market_pipeline.analysis.chart_classification.ChartClassifier')`
- 153行: `@patch('chart_classification.get_all_tickers', ...)` → `@patch('market_pipeline.analysis.chart_classification.get_all_tickers', ...)`
- 154行: `@patch('chart_classification.save_result_to_db')` → `@patch('market_pipeline.analysis.chart_classification.save_result_to_db')`
- 155行: `@patch('chart_classification.ChartClassifier')` → `@patch('market_pipeline.analysis.chart_classification.ChartClassifier')`
- 179行: `mocker.patch('chart_classification.main_sample')` → `mocker.patch('market_pipeline.analysis.chart_classification.main_sample')`
- 180行: `mocker.patch('chart_classification.main_full_run')` → `mocker.patch('market_pipeline.analysis.chart_classification.main_full_run')`

---

## 修正対象ファイル

| ファイル | 操作 |
|----------|------|
| `tests/test_functions.py` | 削除 |
| `tests/test_integrated_analysis.py` | 編集 |
| `tests/test_chart_classification.py` | 編集 |

---

## 実装ステップ

1. `tests/test_functions.py` を削除
2. `tests/test_integrated_analysis.py` のカラム名を修正
   - CREATE TABLE: date→Date, code→Code, hl_ratio→HlRatio, weeks→Weeks
   - INSERT: 同様にカラム名変更
   - アサーション: 'hl_ratio' → 'HlRatio' 等
3. `tests/test_chart_classification.py` の@patchパスを修正

---

## 検証方法

```bash
# 全テスト実行
uv run pytest

# 個別テスト実行
uv run pytest tests/test_integrated_analysis.py -v
uv run pytest tests/test_chart_classification.py -v

# test_functions.pyが削除されたことを確認
ls tests/test_functions.py  # ファイルが存在しないことを確認
```

**期待結果**:
- test_functions.pyのインポートエラー解消（29件のエラーの一部）
- test_integrated_analysis.pyの16件の失敗が解消
- test_chart_classification.pyの4件の失敗が解消
