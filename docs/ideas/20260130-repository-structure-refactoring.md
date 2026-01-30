# リポジトリ構造リファクタリング計画

## 目的
ルート直下の `core/` と `stock_reader/` を `backend/` 配下に移動し、将来のモジュール追加（為替・金利等）やフロントエンド統合（Next.js等）に備えた構造に再編成する。

## 変更後の構造

```
/stock-analysis/
├── backend/
│   ├── market_pipeline/         # 旧 core/ → リネーム
│   │   ├── __init__.py          # 新規作成
│   │   ├── analysis/
│   │   ├── config/
│   │   ├── jquants/
│   │   ├── utils/
│   │   ├── master/
│   │   └── yfinance/
│   └── market_reader/           # 旧 stock_reader/ → リネーム
│       ├── __init__.py
│       ├── reader.py
│       ├── exceptions.py
│       └── utils.py
├── scripts/                     # 位置維持
├── tests/                       # 位置維持
├── frontend/                    # 将来用（今回は作成しない）
├── data/                        # 位置維持
├── output/                      # 位置維持
├── logs/                        # 位置維持
├── notebooks/                   # 位置維持
├── pyproject.toml
├── CLAUDE.md
└── README.md
```

## 実装手順

### Step 1: ディレクトリ構造の変更
```bash
mkdir -p backend/market_pipeline
mv core/* backend/market_pipeline/
touch backend/market_pipeline/__init__.py
mv stock_reader backend/market_reader
rmdir core
```

### Step 2: pyproject.toml の更新
```toml
[tool.setuptools.packages.find]
where = ["backend"]

[tool.pytest.ini_options]
pythonpath = ["backend"]
```

### Step 3: インポートパスの一括置換
対象ファイル:
- `backend/market_pipeline/**/*.py` - 内部インポート
- `backend/market_reader/reader.py` - core への依存
- `scripts/*.py` - 全スクリプト
- `tests/*.py` - 全テスト
- `notebooks/*.ipynb` - 全ノートブック

変換パターン:
- `from core.` → `from market_pipeline.`
- `import core.` → `import market_pipeline.`
- `from stock_reader` → `from market_reader`
- `import stock_reader` → `import market_reader`

### Step 4: settings.py の base_dir 修正
`backend/market_pipeline/config/settings.py`:
```python
# 階層が1つ深くなるため調整
base_dir: Path = Path(__file__).parent.parent.parent.parent
# backend/market_pipeline/config/settings.py → project root
```

### Step 5: scripts/ の sys.path.insert 削除
editable install により不要になるため、以下を削除:
```python
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

### Step 6: 検証
```bash
pip install -e .
pytest
python scripts/run_daily_analysis.py --help
```

### Step 7: ドキュメント更新
- CLAUDE.md: パス・インポート例の更新
- README.md: 構造・使用例の更新

## 変更対象ファイル一覧

### 設定ファイル
- `pyproject.toml`

### Python コード（インポート置換）
- `backend/market_pipeline/config/settings.py` - base_dir 修正
- `backend/market_pipeline/**/*.py` - 内部インポート置換
- `backend/market_reader/reader.py` - core → market_pipeline
- `scripts/run_daily_jquants.py`
- `scripts/run_daily_analysis.py`
- `scripts/run_weekly_tasks.py`
- `scripts/run_monthly_master.py`
- `scripts/run_adhoc_integrated_analysis.py`
- `scripts/create_database_indexes.py`
- `tests/conftest.py`
- `tests/test_*.py` (全テストファイル)

### ドキュメント
- `CLAUDE.md`
- `README.md`

## 検証方法

1. **単体テスト実行**
   ```bash
   pytest -v
   ```

2. **スクリプト動作確認**
   ```bash
   python scripts/run_daily_analysis.py --help
   python scripts/run_daily_jquants.py --help
   ```

3. **パッケージインポート確認**
   ```python
   from market_reader import DataReader
   from market_pipeline.config import get_settings
   ```

4. **notebooks 動作確認** (手動)

## 注意事項

- `.venv/` 配下は変更しない
- data/, output/, logs/ のデータファイルは影響なし
- git履歴を保持するため `git mv` を使用推奨

## 将来の拡張例

為替・金利データを追加する場合：
```
backend/
├── market_pipeline/
│   ├── jquants/        # 既存: 日本株
│   ├── forex/          # 新規: 為替
│   └── rates/          # 新規: 金利
└── market_reader/
    └── reader.py       # asset_type パラメータ追加など
```
