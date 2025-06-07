import os

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from app_config import crawl_config, account_config
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from db import DB
import time


class Crawl_Pipeline:
    def __init__(self):
        self.crawl_config = crawl_config
        self.account_config = account_config
        self.db = DB()

    def get_driver(self, options):
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def process_crawl_profile(self):
        count = 1
        for account in self.account_config:
            print(f"START ACCOUNT {count}")
            for category in self.crawl_config["category"]:
                print(f"CRAWL {category.upper()}")
                self.crawl_profile(category, account["token"])
            count += 1

    def process_crawl_pdf(self):
        count = 1
        for account in self.account_config:
            print(f"START ACCOUNT {count}")
            self.crawl_pdf(self.crawl_config["crawl_num"], account["token"])
            count += 1

    def crawl_profile(self, category, token):
        try:
            # config
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument(
                "User-Agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")
            driver = self.get_driver(options)

            # go to LinkedIn
            driver.get("https://www.linkedin.com/")
            time.sleep(1)

            driver.add_cookie({
                "name": "li_at",
                "value": token,
                "domain": ".www.linkedin.com",
                "path": "/",
                "secure": True,
                "httpOnly": True
            })
            search_name = self.crawl_config["search_name"]
            driver.get(f"https://www.linkedin.com/search/results/people/?keywords={search_name}&origin=FACETED_SEARCH&sid=_j.&titleFreeText={category}")

            # Bắt đầu crawl
            base_url = driver.current_url
            print("(2)Start crawl")
            count = 0
            for i in range(self.db.get_crawl_page(self.db.get_category(category), self.crawl_config["search_name"]) + 1,
                           self.db.get_crawl_page(self.db.get_category(category), self.crawl_config["search_name"]) + 100):
                page_url = base_url + f"&page={i}"
                print(f"(3)Crawl {page_url}")
                driver.get(page_url)

                # Chờ các liên kết xuất hiện và lấy chúng
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "ul a[href^='https://www.linkedin.com/in/']:not(.scale-down)"))
                )
                links = driver.find_elements(By.CSS_SELECTOR,
                                             "ul a[href^='https://www.linkedin.com/in/']:not(.scale-down)")
                print(f"Found {len(links)} links")

                for link in links:
                    href = link.get_attribute("href").split('?')[0]
                    if href:
                        result = self.db.add_profile(href, self.db.get_category(category))
                        if result:
                            print(f"ADDED PROFILE {href}:{self.db.get_category(category)}")
                            count += 1
                            if count == self.crawl_config["crawl_num"]:
                                self.db.update_crawl_page(self.db.get_category(category), self.crawl_config["search_name"], i)
                                return

                self.db.update_crawl_page(self.db.get_category(category), self.crawl_config["search_name"], i)

        except Exception as e:
            print(f"Đã xảy ra lỗi: {e}")
        finally:
            print("(4)Close crawl")
            driver.quit()

    def crawl_pdf(self, crawl_num, token):
        try:
            data = self.db.get_needed_profiles(crawl_num)
            print('(1)Start crawl')

            for profile in data:
                category = profile['Category']
                category_dir = self.db.get_dataset_path(category)
                options = webdriver.ChromeOptions()
                options.add_argument("--headless")
                options.add_argument(
                    "User-Agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")
                options.add_experimental_option("prefs", {
                    "download.default_directory": os.path.abspath(category_dir),
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "plugins.always_open_pdf_externally": True
                })

                driver = self.get_driver(options)
                wait = WebDriverWait(driver, 15)

                try:
                    # Đăng nhập LinkedIn
                    driver.get("https://www.linkedin.com/")
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

                    driver.add_cookie({
                        "name": "li_at",
                        "value": token,
                        "domain": ".www.linkedin.com",
                        "path": "/",
                        "secure": True,
                        "httpOnly": True
                    })

                    # Truy cập trang profile
                    driver.get(profile['Link'])
                    time.sleep(1)

                    # Chờ phần tử dropdown xuất hiện
                    wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "artdeco-dropdown__trigger")))
                    more_buttons = driver.find_elements(By.CLASS_NAME, "artdeco-dropdown__trigger")

                    more_button = more_buttons[3]
                    ActionChains(driver).move_to_element(more_button).click().perform()
                    time.sleep(1)

                    # Chờ các lựa chọn xuất hiện trong dropdown
                    wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "artdeco-dropdown__item")))
                    selections = driver.find_elements(By.CLASS_NAME, "artdeco-dropdown__item")

                    save_button = selections[6]
                    ActionChains(driver).move_to_element(save_button).click().perform()
                    time.sleep(5)

                    print(f"✅ Đã lưu PDF từ {profile['Link']} vào thư mục {category}")
                    self.db.update_crawl_num()
                except Exception as e:
                    print(f"❌ Lỗi khi xử lý {profile['Link']}: {e}")
                finally:
                    driver.quit()

        except Exception as e:
            print(f"Đã xảy ra lỗi toàn cục: {e}")


main = Crawl_Pipeline()
main.process_crawl_pdf()