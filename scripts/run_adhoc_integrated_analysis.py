from market_pipeline.analysis.integrated_analysis2 import main
from market_pipeline.utils.slack_notifier import JobContext


if __name__ == "__main__":
    with JobContext("統合分析") as job:
        main()
