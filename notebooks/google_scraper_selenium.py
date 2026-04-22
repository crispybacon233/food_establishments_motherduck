import marimo

__generated_with = "0.23.1"
app = marimo.App(width="columns")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    import time
    import json
    import re
    from urllib.parse import unquote

    import requests
    from bs4 import BeautifulSoup

    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options

    return (
        ActionChains,
        BeautifulSoup,
        By,
        DesiredCapabilities,
        Keys,
        Service,
        re,
        time,
        unquote,
        webdriver,
    )


@app.cell
def _(BeautifulSoup, By, re, unquote):
    def get_coordinates(driver):
        html = driver.page_source
        soup = BeautifulSoup(html, features="html.parser")

        a = soup.find("a", attrs={"aria-label": "Sign in"})
        if not a:
            return None, None

        href = a.get("href")
        if not href:
            return None, None

        decoded_href = unquote(href)

        match = re.search(r'@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', decoded_href)
        if not match:
            return None, None

        return float(match.group(1)), float(match.group(2))

    # get google's name for establishment
    def get_google_name(driver):
        try:
            google_name = driver.find_element(By.XPATH, '//h1[@class="DUwDvf lfPIob"]').text
            return google_name
        except:
            return None


    # get num of dollar signs, indicating price
    def get_price(driver):
        try:
            price = int(driver.find_element(By.CLASS_NAME, 'mgr77e').text)
            return price
        except:
            return None


    # get establishment category type
    def get_category(driver):
        try:
            category = driver.find_element(By.CLASS_NAME, 'DkEaL ').text
            return category
        except:
            return None



    return get_category, get_coordinates, get_google_name, get_price


@app.cell
def _(ActionChains, By, Keys, re, time):
    # get average stars and number of reviews
    def n_stars_reviews(driver):
        try:
            data = driver.find_element(By.CLASS_NAME, 'F7nice ').text.split('\n')
            stars, n_reviews = data
            stars = float(stars)
            n_reviews = int(re.sub('\(|\)|,', '', n_reviews))  # number of reviews is wrapped in parentheses
            return (stars, n_reviews)
        except:
            return (None, None)


    # click reviews tab
    def click_reviews_tab(driver):
        try:
            tabs = driver.find_elements(By.CLASS_NAME, 'hh2c6 ') # get all tabs
            overview_tab, reviews_tab, about_tab = tabs
            reviews_tab.click()
        except:
            pass


    # keep scrolling until enough reviews are loaded
    def load_all_reviews(driver, n_reviews, max_reviews, max_time):
        if n_reviews > 0:
            action = ActionChains(driver)

            # gets number of reviews loaded
            reviews = driver.find_elements(By.XPATH, "//div[@class='jftiEf fontBodyMedium ']")

            # gets empty space to click so it can page_down correctly
            empty = driver.find_element(By.XPATH, "//div[@class='cVwbnc IlRKB']")
            empty.click()

            # pages down while num of reviews loaded is less than total reviews
            start_time = time.time()
            while len(reviews) < max_reviews and len(reviews) < n_reviews:
                action.send_keys(Keys.PAGE_DOWN).perform()
                reviews = driver.find_elements(By.XPATH, "//div[@class='jftiEf fontBodyMedium ']")
                time.sleep(0.25)
                elapsed_time = time.time() - start_time # sometimes the reviews won't load despite the scrolling, so this breaks out of the loop if that is the case
                if elapsed_time > max_time: 
                    break
        else:
            pass

    return (n_stars_reviews,)


@app.cell
def _(DesiredCapabilities, webdriver):
    # set options
    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}
    options = webdriver.ChromeOptions()
    return caps, options


@app.cell
def _(Service, caps, options, webdriver):
    driver = webdriver.Chrome(service=Service(desired_capabilities=caps, options=options))
    return (driver,)


@app.cell
def _(driver):
    driver.get('https://www.google.com/maps/')
    return


@app.cell
def _(driver):
    driver.get(f'https://www.google.com/maps/search/Burger King 13450 N US 183 HWY Svrd SB Austin, TX')
    return


@app.cell
def _(
    driver,
    get_category,
    get_coordinates,
    get_google_name,
    get_price,
    n_stars_reviews,
):
    print(
        get_coordinates(driver), 
        '\n',
        get_google_name(driver),
        '\n',
        get_price(driver), 
        '\n',
        get_category(driver),
        '\n',
        n_stars_reviews(driver)
    )
    return


@app.cell
def _(driver):
    driver.quit()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
