import os
import csv
from typing import List, Dict


class CSVHelper:
    """
    CSV 儲存管理：
    - load(): 讀取 CSV → List[Dict]
    - save(): 覆寫 CSV（初始化）
    - append(): 增量寫入 CSV
    """

    def __init__(self, path: str, fieldnames: List[str]):
        self.path = path
        self.fieldnames = fieldnames

    def load(self) -> List[Dict]:
        """讀取現有 CSV（若不存在則回傳空 list）"""
        if not os.path.exists(self.path):
            return []

        rows: List[Dict] = []
        # 用 utf-8-sig 方便之後用 Excel 開啟
        with open(self.path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        return rows

    def save(self, rows: List[Dict]) -> None:
        """覆寫 CSV（初始化使用）"""
        if not rows:
            return

        with open(self.path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    def append(self, rows: List[Dict]) -> None:
        """增量寫入 CSV，不 overwrite 原資料"""
        if not rows:
            return

        file_exists = os.path.exists(self.path)

        with open(
            self.path, "a" if file_exists else "w", encoding="utf-8-sig", newline=""
        ) as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)

            # 如果檔案不存在，要先寫 header
            if not file_exists:
                writer.writeheader()

            for r in rows:
                writer.writerow(r)
