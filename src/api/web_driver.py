import os

from selenium import webdriver


def chrome_driver(headless=False):
    from selenium.webdriver.chrome.options import Options
    prefs = {"profile.default_content_setting_values.notifications": 2}
    opts = Options()
    opts.add_experimental_option("prefs", prefs)
    # opts.add_argument('--user-data-dir=C:\\Users\\Vetal\\AppData\\Local\\Google\\Chrome\\User Data')
    # opts.add_argument('--profile-directory=Default')

    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-extensions")  # disabling extensions
    opts.add_argument("--disable-gpu")  # applicable to windows os only
    opts.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems
    opts.add_argument("--no-sandbox")  # Bypass OS security model

    if headless:
        opts.add_argument('--start-minimized')
        opts.add_argument('--headless')
        opts.add_argument('--disable-gpu')
    return webdriver.Chrome(options=opts)


def uc_chrome_driver(headless=False):
    import undetected_chromedriver as uc
    from selenium.webdriver.chrome.options import Options
    user_data_dir = os.path.abspath("chromeData")

    opts = Options()
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-save-password-bubble")
    opts.add_argument(f"--user-data-dir={user_data_dir}")
    driver = uc.Chrome(options=opts, headless=headless, use_subprocess=False)
    return driver


def firefox_driver(headless=False):
    from selenium.webdriver.firefox.options import Options
    opts = Options()

    opts.add_argument("-profile")
    opts.add_argument(os.path.join('profiles/firefox', 'w64vj4qk.default-release'))

    if headless:
        opts.add_argument("--headless")

    return webdriver.Firefox(options=opts)
