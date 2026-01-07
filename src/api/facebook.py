import logging
import os
import random
import time
import uuid
import bs4

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from src import io
from src.api.web_driver import chrome_driver, firefox_driver

selector_post_start = "div.xi81zsa"
xpath_post_body = "//div[@aria-placeholder='Что у вас нового?']"
xpath_comment_body = "//div[@aria-label='Комментировать как Sweety Life']"

intention = [
    "Продолжение чуть ниже в первом комментарии!",
    "Читайте больше в комментарии под этим постом!",
    "Полный текст в комментарии!",
    "Продолжение ждёт вас в комментариях!",
    "Не пропустите продолжение — в первом комментарии!",
    "Больше информации в комментариях!",
    "Подробности можно найти в комментарии!",
    "Хотите больше? Читайте в первом комментарии!",
    "Полная версия ниже в комментарии!",
    "Ответы и продолжение истории — в комментарии!"
]

intention_emoji = [
    "Больше в первом комментарии 👇👇",
    "Больше в комментарии 👇👇",
    "Больше в комментариях 👇👇",
    "Подробнее в первом комментарии 👇👇",
    "Подробнее в комментарии 👇👇",
    "Подробнее в комментариях 👇👇",
    "Читайте в первом комментарии 👇👇",
    "Читайте в комментарии 👇👇",
    "Читайте в комментариях 👇👇",
    "Больше в первом комментарии 👇",
    "Больше в комментарии 👇",
    "Больше в комментариях 👇",
    "Подробнее в первом комментарии 👇",
    "Подробнее в комментарии 👇",
    "Подробнее в комментариях 👇",
    "Читайте в первом комментарии 👇",
    "Читайте в комментарии 👇",
    "Читайте в комментариях 👇",
]

logger = logging.getLogger(__name__)


class FaceBookApi:
    def __init__(self, database, wd, config):
        self.config = config
        self.database = database
        self.wd = wd
        self.driver = firefox_driver()

    def publish(self):
        logger.info("Facebook Publish start")
        # TODO repeat process with loop of entities?

        to_publish_posts = self.database.find_by_fb_status(False, True)

        if not to_publish_posts:
            logger.info("Facebook everything is up to date")
            return None

        to_publish_posts = to_publish_posts[:3]
        to_publish = random.choice(to_publish_posts)

        try:
            soup = bs4.BeautifulSoup(to_publish.orig_content, 'html.parser')
            text = soup.get_text(separator='\n')
            preview_text = self._prepare_preview_text(text)

            post_text = "%s... %s" % (preview_text, random.choice(intention))
            post_image = to_publish.image
            post_comment = "%s %s" % ("Полная статья по ссылке:", to_publish.own_url)

            self._login()
            self._post_message(post_text, post_image)
            self._post_comment(post_comment)
            self.database.update_fb_status(to_publish.local_id, True)
            self.database.save_last_fb_publish_date()
            logger.info("Facebook published post '%s'", to_publish.title)
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
        self.driver.maximize_window()
        self.driver.get(self.config["fb_page"])
        time.sleep(2)

        accept_cookie = self.driver.find_elements(By.XPATH,
                                                  "//div[@aria-label='Разрешить все cookie']") or self.driver.find_elements(
            By.XPATH, "//div[@aria-label='Allow all cookies']")
        if accept_cookie:
            logger.debug("FB: Found cookie. Accept it")
            self.driver.save_screenshot(os.path.join(self.wd, "AcceptCookie.png"))
            accept_cookie[1].click()
        time.sleep(2)

        not_authed = self.driver.find_elements(By.XPATH,
                                               "//div[@aria-label='Создать новый аккаунт']") or self.driver.find_elements(
            By.XPATH, "//div[@aria-label='Create new account']")

        if not_authed:
            logger.debug("FB: Not authed. Login...")

            username = self.driver.find_element(By.XPATH, '//input[@type="text" and @name="email"]')
            if username:
                username.click()
                time.sleep(1)
                username.send_keys(self.config["fb_user"])

            time.sleep(2)
            password = self.driver.find_elements(By.XPATH, '//input[@type="password" and @name="pass"]')
            if password:
                password[1].click()
                time.sleep(1)
                password[1].send_keys(self.config["fb_password"])

            self.driver.save_screenshot(os.path.join(self.wd, "Login.png"))

            time.sleep(1)
            enter = self.driver.find_elements(By.XPATH,
                                              "//div[@aria-label='Войти на Facebook']") or self.driver.find_elements(
                By.XPATH, "//div[@aria-label='Log in to Facebook']")
            if enter:
                enter[0].click()

            time.sleep(15)
            logger.debug("FB: Log in Finish")
        else:
            logger.debug("FB: Already logged in")

        switch = self.driver.find_elements(By.XPATH, "//span[.='Переключиться']")
        if switch:
            logger.debug("FB: Switch to page")
            switch[3].click()
            time.sleep(5)


    def _post_message(self, msg, image_url):
        image_file = os.path.abspath(os.path.join(self.wd, "%s.jpg" % uuid.uuid4()))
        logger.debug("FB: post message. Temp image -> %s", image_file)
        try:
            io.download_file(image_url, image_file)
            self._start_post(image_file)
            self._make_post_body(msg)
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
            self.driver.find_elements(By.XPATH, "//span[.='Комментировать']")[0].click()
            time.sleep(5)

            comment_area = self.driver.find_element(By.XPATH, xpath_comment_body)
            # comment_area.click()
            time.sleep(2)
            self.driver.save_screenshot(os.path.join(self.wd, "CommentStart.png"))
            for t in text:
                comment_area.send_keys(t)
            time.sleep(2)
            self.driver.save_screenshot(os.path.join(self.wd, "CommentFull.png"))
            comment_area.send_keys(Keys.ENTER)
            logger.debug("FB: post comment success")
            time.sleep(10)
        except BaseException as e:
            logger.exception("FB: Post comment Failed!!", e)
            raise e

    def _start_post(self, image):
        self.driver.find_elements(By.XPATH, "//span[.='Фото/видео']")[0].click()
        time.sleep(1)
        input = self.driver.find_element(By.CSS_SELECTOR,
                                         "input[accept='image/*,image/heif,image/heic,video/*,video/mp4,video/x-m4v,video/x-matroska,.mkv']")
        input.send_keys(image)
        time.sleep(10)
        self.driver.save_screenshot(os.path.join(self.wd, "PostStart.png"))

    def _make_post_body(self, msg):
        text_area = self.driver.find_element(By.XPATH, xpath_post_body)
        text_area.click()
        time.sleep(5)
        for m in msg:
            text_area.send_keys(m)
            time.sleep(0.05)
        time.sleep(5)
        self.driver.save_screenshot(os.path.join(self.wd, "PostFull.png"))

    def _finish_post(self):
        next_btn = self.driver.find_element(By.XPATH, "//div[@aria-label='Далее']")
        next_btn.click()
        time.sleep(15)

        post_btn = self.driver.find_element(By.XPATH, "//div[@aria-label='Опубликовать']")
        post_btn.click()
        time.sleep(15)

        dont_now = self.driver.find_elements(By.XPATH, "//div[@aria-label='Не сейчас']")
        if dont_now:
            self.driver.save_screenshot(os.path.join(self.wd, "DontNow.png"))
            dont_now[0].click()
            self.driver.save_screenshot(os.path.join(self.wd, "DontNowClick.png"))
            time.sleep(15)

    @staticmethod
    def _prepare_preview_text(text):
        text_lines = text.split('\n')
        total_lines = len(text_lines)

        # Decide percentage dynamically
        if total_lines > 100:  # big text
            percent = 0.05
        elif total_lines > 30:  # medium text
            percent = 0.25
        else:  # very small text — show all
            percent = 0.80

        num_lines_to_keep = max(1, int(total_lines * percent))
        lines_to_keep = text_lines[:num_lines_to_keep]

        # Add ellipsis if text was trimmed
        if num_lines_to_keep < total_lines:
            lines_to_keep.append("…")

        return '\n'.join(lines_to_keep)
