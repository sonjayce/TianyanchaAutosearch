import os
import csv
import time
import random
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver import ActionChains


class TianyanchaAutoSearch:
    def __init__(self):
        self._init_webdriver()
        self.wait = WebDriverWait(self.driver, 20)
        self.results = []
        self.max_pages = 10  # 最大翻页数限制

    def _init_webdriver(self):
        """浏览器初始化配置"""
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # 随机用户代理
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        ]
        options.add_argument(f"user-agent={random.choice(user_agents)}")

        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    def _human_delay(self, element=None):
        """人性化延迟操作"""
        delay = random.uniform(0.5, 3)
        if element:
            actions = ActionChains(self.driver)
            actions.move_to_element(element).pause(delay / 2).perform()
        time.sleep(delay)

    def _human_type(self, element, text):
        """模拟人类输入"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))

    def _human_scroll(self, element=None):
        """智能滚动策略"""
        if element:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'center'});",
                element
            )
        else:
            scroll_distance = random.randint(300, 700)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
        self._human_delay()

    def check_captcha(self):
        """验证码检测处理"""
        try:
            captcha_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="geetest_btn_click"]'))
            )
            if captcha_element.is_displayed():
                print("\n⚠️ 检测到验证码，请手动处理！")
                input("✅ 处理完成后按回车继续...")
                if self.driver.find_elements(By.CSS_SELECTOR, 'div[class*="geetest_btn_click"]'):
                    raise TimeoutException("验证码仍未处理")
        except TimeoutException:
            pass

    def close_popups(self):
        """弹窗关闭处理"""
        popup_selectors = [
            "div.popup-close", "div.mask-layer",
            "i.icon-close", "div.modal-close",
            "button.btn-close"
        ]
        for selector in popup_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    self.driver.execute_script("arguments[0].click();", element)
                    time.sleep(1)
            except Exception:
                continue

    def login_intervention(self):
        """登录流程处理"""
        print("✅正在登陆流程")
        self.driver.get("https://beian.tianyancha.com/")
        self.driver.maximize_window()
        self.close_popups()

        try:
            if self.driver.find_elements(By.CSS_SELECTOR, "span.tyc-header-nav-login-btn"):
                login_btn = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "span.tyc-header-nav-login-btn"))
                )
                self._human_scroll(login_btn)
                login_btn.click()
                self.check_captcha()
        except TimeoutException:
            pass

    def construct_search_url(self, keyword, page=1):
        """构造分页URL"""
        encoded_keyword = quote(keyword)
        return f"https://beian.tianyancha.com/search/{encoded_keyword}/p{page}"

    def load_page(self, url):
        """加载指定页面"""
        try:
            self.driver.get(url)
            self.wait.until(
                lambda d: d.find_element(By.CSS_SELECTOR, "table.table.-ranking") or
                          d.find_element(By.CSS_SELECTOR, "div.no-data-container")
            )
            self.close_popups()
            self.check_captcha()
            return True
        except TimeoutException:
            print(f"❌ 页面加载超时: {url}")
            return False

    def extract_data(self):
        """数据提取"""
        for _ in range(3):  # 重试机制
            try:
                table = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table.table.-ranking"))
                )
                self._human_scroll(table)

                rows = WebDriverWait(table, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody tr:not(.no-data)"))
                )

                for row in rows:
                    try:
                        record = {
                            '备案号': row.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip(),
                            '主办单位': row.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text.strip(),
                            '网站名称': row.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.strip(),
                            '网站域名': row.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text.strip(),
                            '审核时间': row.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text.strip()
                        }
                        self.results.append(record)
                    except StaleElementReferenceException:
                        continue
                return True
            except Exception as e:
                print(f"⚠️ 数据提取异常: {str(e)}")
                time.sleep(2)
        return False

    def handle_pagination(self, keyword):
        """分页处理核心逻辑"""
        for page in range(1, self.max_pages + 1):
            print(f"\n📖 正在处理第 {page} 页")
            search_url = self.construct_search_url(keyword, page)

            if not self.load_page(search_url):
                break

            # 检查无数据情况
            if self.driver.find_elements(By.CSS_SELECTOR, "div.no-data-container"):
                print("✅ 已到达最后一页")
                break

            # 提取数据
            if not self.extract_data():
                print("❌ 数据提取失败，终止分页")
                break

            # 随机延迟防止请求过快
            time.sleep(random.uniform(1, 3))

    def save_results(self):
        """数据保存"""
        if not self.results:
            print("⚠️ 无有效数据可保存")
            return

        # 创建结果目录
        result_dir = os.path.join(os.path.dirname(__file__), 'result')
        os.makedirs(result_dir, exist_ok=True)
        
        file_path = os.path.join(result_dir, 'result.csv')
        
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
            writer.writeheader()
            writer.writerows(self.results)
        print(f"💾 成功保存 {len(self.results)} 条数据至：{os.path.abspath(file_path)}")

    def run(self):
        """主执行流程"""
        try:
            self.login_intervention()
            keyword = input("请输入查询关键词：")

            print("\n🔍 开始执行搜索...")
            self.handle_pagination(keyword)

            print("\n💾 正在保存数据...")
            self.save_results()

        except Exception as e:
            print(f"\n❗ 程序异常: {str(e)}")
            self.driver.save_screenshot('error.png')
        finally:
            self.driver.quit()
            print("\n🛑 浏览器已关闭")


if __name__ == "__main__":
    print("=== 天眼查备案信息自动查询程序 ===")
    print("⚠️ 请确保：")
    print("1. Chrome浏览器已安装")
    print("2. 网络连接正常")
    print("3. 准备好处理验证码\n")
    
    bot = TianyanchaAutoSearch()
    bot.run()