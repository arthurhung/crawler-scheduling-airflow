## 🧩 系統整體架構圖（試題一 + 試題二）

<pre class="overflow-visible!" data-start="3869" data-end="4561"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre!"><span><span>【外部資料源】
衛福部國民健康署 HPA 保健闢謠文章網站
        │
        ▼
【試題一：資料收集層 (question_1)】
</span><span>- crawler.py         → 抓取文章列表 + 內文</span><span>
</span><span>- csv_helper.py      → 初始化/增量寫入 CSV</span><span>
</span><span>- logger_setup.py    → 日誌紀錄</span><span>
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
</span><span>- 每日 03:00 自動執行爬蟲</span><span>
</span><span>- 呼叫 HealthMythCrawler.run()</span><span>
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
question_2/data/hpa_health_myths.csv</span></span></code></div></div></pre>
