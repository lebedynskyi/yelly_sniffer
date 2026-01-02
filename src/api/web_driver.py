import os

from selenium import webdriver
import atexit
import signal
import sys

from selenium.webdriver import FirefoxProfile

HEADLESS = True
cache_driver = None
uc_cache_driver = None
fire_cache_driver = None


def cleanup_drivers():
    print("Cleaning up cached drivers...")
    global cache_driver
    global uc_cache_driver
    global fire_cache_driver

    try:
        if cache_driver and hasattr(cache_driver, "quit"):
            cache_driver.quit()
    except:
        pass

    try:
        if uc_cache_driver and hasattr(uc_cache_driver, "quit"):
            uc_cache_driver.quit()
    except:
        pass

    try:
        if fire_cache_driver and hasattr(fire_cache_driver, "quit"):
            fire_cache_driver.quit()
    except:
        pass


def handle_exit(signum, frame):
    cleanup_drivers()
    sys.exit(0)


def chrome_driver():
    from selenium.webdriver.chrome.options import Options

    global cache_driver
    if not cache_driver:
        user_data_dir = os.path.abspath("output/chromeData")
        opts = Options()

        opts.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})

        opts.add_argument("--ignore-certificate-errors")
        opts.add_argument("--disable-save-password-bubble")
        opts.add_argument("--disable-extensions")  # disabling extensions
        opts.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems
        opts.add_argument("--no-sandbox")  # Bypass OS security model
        if HEADLESS:
            opts.add_argument('--start-minimized')
            opts.add_argument("--headless=new")
            opts.add_argument('--disable-gpu')
        cache_driver = webdriver.Chrome(options=opts)

    return cache_driver


def uc_chrome_driver():
    import undetected_chromedriver as uc
    from selenium.webdriver.chrome.options import Options

    global uc_cache_driver
    if not uc_cache_driver:
        user_data_dir = os.path.abspath("output/chromeData")

        opts = Options()
        opts.add_argument("--ignore-certificate-errors")
        opts.add_argument("--disable-save-password-bubble")
        opts.add_argument("--disable-extensions")  # disabling extensions
        opts.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems
        opts.add_argument("--no-sandbox")  # Bypass OS security model
        opts.add_argument(f"--user-data-dir={user_data_dir}")
        uc_cache_driver = uc.Chrome(options=opts, headless=HEADLESS, use_subprocess=False)

    return uc_cache_driver


def firefox_driver():
    global fire_cache_driver
    if not fire_cache_driver:
        from selenium.webdriver.firefox.options import Options

        user_data_dir = os.path.abspath("output/firefoxData")
        os.makedirs(user_data_dir, exist_ok=True)

        opts = Options()
        opts.set_preference("dom.webnotifications.enabled", False)
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument('-profile')
        opts.add_argument(user_data_dir)
        if HEADLESS:
            opts.add_argument("--headless")

        fire_cache_driver = webdriver.Firefox(options=opts)
    return fire_cache_driver


atexit.register(cleanup_drivers)  # normal exit
signal.signal(signal.SIGINT, handle_exit)  # Ctrl+C
signal.signal(signal.SIGTERM, handle_exit)  # Kill
