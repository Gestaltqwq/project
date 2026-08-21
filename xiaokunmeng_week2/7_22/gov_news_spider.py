import time
import random
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, exc
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("sqlite:///gov_news.db", echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class GovNews(Base):
    """新闻数据表模型"""
    __tablename__ = "gov_news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)            # 新闻标题
    publish_time = Column(String(30), nullable=False)      # 发布时间
    link = Column(String(800), unique=True, nullable=False)  # 新闻链接（唯一）


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.gov.cn/",
    "Connection": "keep-alive",
}

TIMEOUT = 40
SLEEP_MIN = 2
SLEEP_MAX = 4
MAX_PAGES = 10

def build_url(page_num):
    if page_num == 1:
        return "https://www.gov.cn/toutiao/liebiao/"
    return f"https://www.gov.cn/toutiao/liebiao/home_{page_num - 1}.htm"

def crawl_page(page_num):
    url = build_url(page_num)
    print(f"\n{'='*50}")
    print(f"[*] 正在抓取第 {page_num} 页：{url}")
    print(f"{'='*50}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        print(f"[X] 第 {page_num} 页请求超时（>{TIMEOUT}s）")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[X] 第 {page_num} 页请求异常：{e}")
        return False

    if resp.status_code == 403:
        print(f"[X] 第 {page_num} 页访问受限（403），触发反爬机制，终止抓取")
        return False

    if resp.status_code != 200:
        print(f"[X] 第 {page_num} 页状态码异常：{resp.status_code}")
        return False

    raw_html = resp.content.decode("utf-8")

    # ---------- BeautifulSoup 解析（本次自学核心）----------    # 坑点：gov.cn 的公共头部内嵌了一段完整 HTML（含 </html>），
    # 导致 lxml 在第一个 </html> 处截断文档，后面的新闻内容全部丢失。
    # 解法：摘掉这个提前闭合的 </html>。
    if "<!--公共头结束-->" in raw_html:
        # 仅保留公共头结束之后的实际页面内容
        raw_html = raw_html.split("<!--公共头结束-->", 1)[1]

    soup = BeautifulSoup(raw_html, "lxml")

    news_items = soup.select(".news_box ul li")

    if not news_items:
        print(f"[!] 第 {page_num} 页未找到新闻条目")
        return False

    print(f"  本页共 {len(news_items)} 条新闻")

    db = SessionLocal()
    inserted = 0
    skipped = 0

    for idx, item in enumerate(news_items, start=1):
        try:
            # 标题 & 链接
            title_tag = item.select_one("h4 a")
            if title_tag is None:
                # 部分条目可能结构不同，跳过
                skipped += 1
                continue

            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")

            # 发布时间
            time_tag = item.select_one(".date")
            pub_time = time_tag.get_text(strip=True) if time_tag else ""

            if not title or not pub_time:
                print(f"  [!] 第 {idx} 条标题或时间为空")
                skipped += 1
                continue

            #写入数据库
            news_record = GovNews(
                title=title,
                publish_time=pub_time,
                link=link,
            )
            db.add(news_record)
            db.commit()
            inserted += 1

            # 打印简要日志
            print(f"  [+] #{inserted} [{pub_time}] {title[:45]}...")

        except exc.IntegrityError:
            db.rollback()
            print(f"  [-] 第 {idx} 条链接重复")
            skipped += 1

        except Exception as e:
            db.rollback()
            print(f"  [X] 第 {idx} 条入库异常：{e}")
            skipped += 1

    db.close()

    print(f"\n  第 {page_num} 页完成：插入 {inserted} 条，跳过 {skipped} 条")
    return True

def interactive_menu():
    """简易交互式菜单，支持单页抓取 / 批量抓取 / 导出 CSV。"""
    while True:
        print("\n" + "=" * 40)
        print("  中国政府网新闻爬虫 — 交互菜单")
        print("=" * 40)
        print("  1. 抓取指定单页")
        print("  2. 批量抓取 1~10 页")
        print("  3. 导出数据为 CSV")
        print("  4. 退出")
        print("=" * 40)
        choice = input("请输入选项（1-4）：").strip()

        if choice == "1":
            try:
                n = int(input("请输入页码（1-435）：").strip())
                if n < 1 or n > 435:
                    print("页码超出范围！")
                    continue
                crawl_page(n)
            except ValueError:
                print("输入无效，请输入数字。")

        elif choice == "2":
            for page in range(1, MAX_PAGES + 1):
                ok = crawl_page(page)
                if not ok:
                    print(f"第 {page} 页异常，批量抓取终止。")
                    break
                if page < MAX_PAGES:
                    sleep_time = random.uniform(SLEEP_MIN, SLEEP_MAX)
                    print(f"  休眠 {sleep_time:.1f} 秒...")
                    time.sleep(sleep_time)
            print("\n批量抓取全部完成！")

        elif choice == "3":
            export_to_csv()

        elif choice == "4":
            print("退出程序。")
            break

        else:
            print("无效选项，请重新输入。")

def export_to_csv():
    """将数据库中的数据导出为 CSV 文件。"""
    import csv
    from sqlalchemy import text

    output_file = "gov_news.csv"

    try:
        db = SessionLocal()
        # 使用原生 SQL 查询，避免加载大量 ORM 对象
        rows = db.execute(
            text("SELECT id, title, publish_time, link FROM gov_news ORDER BY id")
        ).fetchall()

        if not rows:
            print("数据库暂无数据，无法导出。")
            db.close()
            return

        with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["序号", "标题", "发布时间", "链接"])
            writer.writerows(rows)

        db.close()
        print(f"[+] 已导出 {len(rows)} 条数据到 {output_file}")

    except Exception as e:
        print(f"[X] 导出 CSV 异常：{e}")

if __name__ == "__main__":
        interactive_menu()