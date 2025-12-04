from csv_helper import CSVHelper
from crawler import HealthMythCrawler


def main():
    fieldnames = [
        "pid",
        "title",
        "url",
        "publish_date",
        "update_date",
        "content",
    ]
    storage = CSVHelper(path="./hpa_health_myths.csv", fieldnames=fieldnames)
    crawler = HealthMythCrawler(storage=storage)

    crawler.run(initial_n=10, max_pages=5)


if __name__ == "__main__":
    main()
