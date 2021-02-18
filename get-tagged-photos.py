import logging
import random
import time

import click
import selenium.webdriver as webdriver
import selenium.webdriver.chrome.options as chrome_options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.touch_actions import TouchActions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as Wait

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# WebDriverWait timeout in seconds.
WAIT_TIMEOUT = 10


@click.command()
@click.argument("username")
@click.argument("password", envvar="FB_PASSWORD")
@click.option(
    "--wait",
    default=True,
    type=bool,
    help="Wait a random amount of time between requests",
)
def photos_of_me(username, password, wait):
    """Gets "photos of me" from Facebook.

    Authenticates with USERNAME and PASSWORD.
    """
    driver = chrome_driver()
    sign_in_to_facebook(driver, username, password)
    go_to_first_photo(driver)

    count = 5
    for photo in photos(driver, wait):
        if count < 0:
            break
        else:
            count -= 1
        print(photo)


def chrome_driver():
    """Returns instance of Chrome webdriver."""
    options = chrome_options.Options()
    options.add_experimental_option("w3c", False)
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--mute-audio")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)


def sign_in_to_facebook(driver, username, password):
    """Signs in to Facebook with `username` and `password`."""
    logger.info("Signing in to Bookface")
    driver.get("https://m.facebook.com/")
    driver.find_element_by_css_selector("input[name='email']").send_keys(username)
    driver.find_element_by_css_selector("input[name='pass']").send_keys(password)
    driver.find_element_by_css_selector("button[name='login']").click()
    # Wait until title changes.
    title = driver.title
    Wait(driver, timeout=WAIT_TIMEOUT).until_not(EC.title_is(title))
    # Then just go here again to skip that "one tap" bullshit.
    driver.get("https://m.facebook.com/")


def go_to_first_photo(driver):
    """Navigates to first photo of you."""
    logger.info("Clicking through to first photo in 'photos of you'")
    wait = Wait(driver, timeout=WAIT_TIMEOUT)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "i.profpic"))).click()
    wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.scrollAreaBody > a"))
    ).click()
    wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.timeline.photos > span > a"))
    ).click()


def get_photo(driver):
    """Scrapes photo details from page."""
    return {
        "actor": driver.find_element_by_css_selector("strong.actor").text,
        "url": driver.find_element_by_link_text("View full size").get_attribute("href"),
        "caption": driver.find_element_by_xpath(
            "//div[@id='voice_replace_id']/.."
        ).text,
        "date": driver.find_element_by_css_selector("abbr").text,
    }


def tap_next_photo(driver):
    """Taps next photo button."""
    TouchActions(driver).tap(
        driver.find_element_by_xpath(
            "//a[@data-sigil='touchable']/span[text()='Next']/.."
        )
    ).perform()


def photos(driver, wait):
    """Generates photo details.

    Wait a random amount of time between requests if `wait` is True.
    """
    # Loop until there is no "Next" button to click --  I assume this would
    # mean the end of photos.
    while True:
        if wait:
            time.sleep(random.random() + 0.3)
        try:
            # Wait for "View full size" link.
            Wait(driver, timeout=WAIT_TIMEOUT).until(
                EC.element_to_be_clickable(
                    (
                        By.LINK_TEXT,
                        "View full size",
                    )
                )
            )
            photo = get_photo(driver)
            logging.debug(photo)
            yield photo
        except TimeoutException:
            logging.warning('"View full size" link did not appear')
        try:
            logging.info("Going to next photo")
            tap_next_photo(driver)
        except NoSuchElementException:
            logging.info("Can't find a Next to click")
            break
    raise Exception()


if __name__ == "__main__":
    photos_of_me()
