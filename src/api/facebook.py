import datetime
import logging
import os
import random
import time

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from src import io

selector_post_start = "div.xi81zsa"
xpath_post_body = "//div[@aria-label='Что у вас нового?']"
xpath_comment_body = "//div[@aria-label='Напишите комментарий…']"

intention = [
    "Больше в первом комментарии.",
    "Больше в комментарии.",
    "Больше в комментариях.",
    "Подробнее в первом комментарии.",
    "Подробнее в комментарии.",
    "Подробнее в комментариях.",
    "Читайте в первом комментарии.",
    "Читайте в комментарии.",
    "Читайте в комментариях.",
]

logger = logging.getLogger(__name__)


class FaceBookApi:
    driver = None

    def __init__(self, driver, database, wd, config, headless=True):
        self.config = config
        self.database = database
        self.wd = wd
        self.headless = headless
        self.driver_name = driver

    def publish(self):
        last_date = self.database.get_last_fb_publish_date()
        now = datetime.datetime.now()
        diff = now - last_date
        if diff.total_seconds() < self.config["fb_publish_delay"]:
            logger.info("No time for update. Only %s time from last post", diff)
            return

        # TODO repeat process with loop of enteties?

        to_publish_posts = self.database.find_by_fb_status(False, True)
        if not to_publish_posts:
            logger.info("Facebook everything is up to date")
            return

        to_publish = to_publish_posts[0]
        try:
            if to_publish.title[-1].isalpha():
                post_title = "%s%s %s" % (to_publish.title, random.choice(["!", "."]), random.choice(intention))
            else:
                post_title = "%s %s" % (to_publish.title, random.choice(intention))

            post_image = to_publish.image
            post_comment = "%s %s" % (to_publish.title, to_publish.own_url)

            self._login()
            self._post_message(post_title, post_image)
            self._post_comment(post_comment)
            self.database.update_fb_status(to_publish.local_id, True)
            self.database.save_last_fb_publish_date()
            logger.info("Facebook published post '%s'", to_publish.title)
            self.database.update_fb_status(to_publish.local_id, True)
            self.quit()
            return to_publish
        except BaseException as e:
            logger.exception("Unable Publish via FaceBook", e)
            self.driver.save_screenshot(os.path.join(self.wd, "Error.png"))
            self.quit()
            raise e

    def quit(self):
        self.driver.quit()

    def _login(self):
        logger.debug("FB: log in. Driver %s", self.driver_name)
        if self.driver_name.lower() == "chrome":
            self.driver = self._chrome_driver()
        elif self.driver_name.lower() == "firefox":
            self.driver = self._firefox_driver()
        else:
            raise AttributeError("Unknown driver name '%s'" % self.driver_name)

        self.driver.maximize_window()
        self.driver.get("https://www.facebook.com/sweetylife.fun")
        time.sleep(5)
        self.driver.save_screenshot(os.path.join(self.wd, "Login.png"))
        logger.debug("FB: Log in Finish")

    def _post_message(self, msg, image_url):
        image_file = os.path.abspath(os.path.join(self.wd, "temp_image.jpg"))
        logger.debug("FB: post message. Temp image -> %s", image_file)
        try:
            io.download_file(image_url, image_file)
            self._start_post()
            self._make_post_body(msg, image_file)
            self._finish_post()
            os.remove(image_file)
            logger.debug("FB: post message success")
        except BaseException as e:
            os.remove(image_file)
            logger.exception("FB: Post message failed!!", e)
            raise e

    def _post_comment(self, text):
        try:
            logger.debug("FB: post comment")
            comment_area = self.driver.find_element(By.XPATH, xpath_comment_body)
            comment_area.click()
            time.sleep(2)
            self.driver.save_screenshot(os.path.join(self.wd, "CommentStart.png"))
            for t in text:
                comment_area.send_keys(t)
            time.sleep(2)
            self.driver.save_screenshot(os.path.join(self.wd, "CommentFull.png"))
            comment_area.send_keys(Keys.ENTER)
            logger.debug("FB: post comment success")
            time.sleep(5)
        except BaseException as e:
            logger.exception("FB: Post comment Failed!!", e)
            raise e

    def _start_post(self):
        self.driver.find_elements(By.XPATH, "//span[.='Фото/видео']")[0].click()
        time.sleep(5)
        self.driver.save_screenshot(os.path.join(self.wd, "PostStart.png"))

    def _make_post_body(self, msg, image):
        text_area = self.driver.find_element(By.XPATH, xpath_post_body)
        text_area.click()
        time.sleep(2)
        for m in msg:
            text_area.send_keys(m)
        time.sleep(2)

        input = self.driver.find_element(By.CSS_SELECTOR,
                                         "input[accept='image/*,image/heif,image/heic,video/*,video/mp4,video/x-m4v,video/x-matroska,.mkv']")
        input.send_keys(image)
        time.sleep(5)
        self.driver.save_screenshot(os.path.join(self.wd, "PostFull.png"))

    def _finish_post(self):
        post_btn = self.driver.find_element(By.XPATH, "//div[@aria-label='Опубликовать']")
        post_btn.click()
        time.sleep(15)

        dont_now = self.driver.find_elements(By.XPATH, "//div[@aria-label='Не сейчас']")
        if dont_now:
            self.driver.save_screenshot(os.path.join(self.wd, "DontNow.png"))
            dont_now[0].click()
            self.driver.save_screenshot(os.path.join(self.wd, "DontNowClick.png"))
            time.sleep(15)

    def _chrome_driver(self):
        from selenium.webdriver.chrome.options import Options
        prefs = {"profile.default_content_setting_values.notifications": 2}
        opts = Options()
        opts.add_experimental_option("prefs", prefs)
        opts.add_argument('--user-data-dir=posts/chrome')
        opts.add_argument('--profile-directory=Default')
        opts.add_argument('--start-minimized')
        opts.add_argument("--ignore-certificate-errors")
        if self.headless:
            opts.add_argument('--headless')
            opts.add_argument('--disable-gpu')
        return webdriver.Chrome(options=opts)

    def _firefox_driver(self):
        from selenium.webdriver.firefox.options import Options
        ffOptions = Options()
        if self.headless:
            ffOptions.add_argument("--headless")
        ffOptions.add_argument("-profile")
        ffOptions.add_argument(os.path.join(self.wd, 'firefox/w64vj4qk.default-release'))
        return webdriver.Firefox(options=ffOptions)
