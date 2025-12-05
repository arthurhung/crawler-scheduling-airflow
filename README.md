🧩 系統整體架構圖（試題一 + 試題二）
【外部資料源】
衛福部國民健康署 HPA 保健闢謠文章網站
        │
        ▼
【試題一：資料收集層 (question_1)】
- crawler.py         → 抓取文章列表 + 內文
- csv_helper.py      → 初始化/增量寫入 CSV
- logger_setup.py    → 日誌紀錄
        │
        ▼
輸出：hpa_health_myths.csv
儲存位置：question_1/hpa_health_myths.csv
        │
        ▼
【試題二：服務化 & 排程層 (question_2)】
Dockerfile → 建立 Airflow 容器 (Python 3.12)
docker-compose → 啟動 Postgres + Airflow

Airflow DAG (hpa_crawler_dag.py)
- 每日 03:00 自動執行爬蟲
- 呼叫 HealthMythCrawler.run()
        │
        ▼
【Airflow 運作流程】
Scheduler → 觸發 PythonOperator
Webserver → 監控執行狀況 (http://localhost:8080)
Metadata → 儲存在 Postgres
Logs → question_2/logs
        │
        ▼
【最終結果】
CSV 會自動產生與增量更新：
question_2/data/hpa_health_myths.csv
