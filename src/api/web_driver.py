import os

from selenium import webdriver
import atexit
import signal
import sys

HEADLESS = False
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
    if fire_cache_driver:
        return fire_cache_driver

    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
    import os

    user_data_dir = os.path.abspath("output/firefoxData")
    os.makedirs(user_data_dir, exist_ok=True)

    profile = FirefoxProfile(user_data_dir)
    profile.set_preference("dom.webnotifications.enabled", False)
    profile.set_preference("dom.webdriver.enabled", False)
    profile.set_preference("layers.acceleration.force-enabled", True)
    profile.set_preference("gfx.webrender.all", True)
    profile.set_preference("gfx.webrender.enabled", True)
    profile.set_preference("intl.accept_languages", "en-US,en")
    profile.set_preference("dom.max_script_run_time", 0)
    profile.set_preference("dom.max_chrome_script_run_time", 0)

    opts = Options()
    opts.profile = profile

    if HEADLESS:
        opts.add_argument("--headless=new")

    driver = webdriver.Firefox(options=opts)
    driver.set_window_size(1920, 1080)

    driver.execute_script("""
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    """)

    fire_cache_driver = driver
    return driver



atexit.register(cleanup_drivers)  # normal exit
signal.signal(signal.SIGINT, handle_exit)  # Ctrl+C
signal.signal(signal.SIGTERM, handle_exit)  # Kill
