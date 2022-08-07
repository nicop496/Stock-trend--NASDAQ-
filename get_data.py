import os, re
import pandas as pd

from numpy import object_
from time import sleep
from datetime import datetime as dt
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import element_to_be_clickable


DATA_PATH = Path('Downloaded data')


def _press_download_btn(url, btn_class_name, file_match_pattern, other_actions=lambda _: None):
    try:
        # Go to the web page
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('log-level=3')
        driver = webdriver.Chrome(service=Service('./chromedriver.exe'), options=chrome_options)
        print('Waiting until the page loads completely...')
        driver.get(url)

        # Do some other optional actions (like changing the time period)
        other_actions(driver)
        sleep(3)

        # Press the download button
        download_btn = driver.find_element(By.CLASS_NAME, btn_class_name)
        driver.execute_script("arguments[0].click();", download_btn)

    except:
        print('SELENIUM ERROR')
        driver.quit()
        raise

    else:
        # Get and return the file path
        filepath = lambda: sorted(Path(Path.home() / 'Downloads').iterdir(), key=os.path.getmtime)[-1]
        while not re.match(file_match_pattern, filepath().name):
            sleep(.5)
            print('Waiting for the download to finish...')
        driver.quit()
        return filepath()


def get_companies_list():
    filename = f'Companies list {dt.today().strftime("%m-%Y")}.csv'
    if not filename in os.listdir(DATA_PATH):
        filepath = _press_download_btn(
            'https://www.nasdaq.com/market-activity/stocks/screener/', 
            'ns-download-1', 
            r'(nasdaq_screener_)[0-9]+(\.csv)$')
        os.rename(filepath, DATA_PATH / filename)
    df = pd.read_csv(DATA_PATH / filename, encoding='latin1', on_bad_lines='skip', index_col=0)
    return df[['Name', 'Country', 'Sector', 'Market Cap']]


def get_company_data(symbol:str, time_period:str):
    '''
    Time period argument must be one of the following:
    - 'm1' (last month passed)
    - 'm6' (last six months)
    - 'ytd' (all this year till now)
    - 'y1' (last year)
    - 'y5' (last five years)
    - 'y10' (last ten years)
    '''
    def set_time_period(driver):
        time_period_btn = WebDriverWait(driver, 10).until(
            element_to_be_clickable((By.XPATH, f'//button[@data-value="{time_period}"]'))
        )
        driver.execute_script("arguments[0].click();", time_period_btn)

    filename = f'{symbol.upper()} {time_period.upper()} {dt.today().strftime("%d-%m-%y")}.csv'

    if not filename in os.listdir(DATA_PATH):
        filepath = _press_download_btn(
        f'https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/historical/', 
        'historical-download', 
        r'(HistoricalData_)[0-9]+(\.csv)$',
        other_actions=set_time_period
        )
        os.rename(filepath, DATA_PATH / filename)

    df = pd.read_csv(DATA_PATH / filename, index_col=0)
    df.index = pd.to_datetime(df.index, infer_datetime_format=True)
    for i in df:
        if df[i].dtype == object_:
            df[i] = pd.to_numeric(df[i].apply(lambda val: val[1:]))
    return df
