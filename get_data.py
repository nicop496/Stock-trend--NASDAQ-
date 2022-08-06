import os, re
import pandas as pd
from time import sleep
from datetime import datetime as dt
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service


DATA_PATH = Path('Downloaded data')


def __press_download_btn(url, btn_class_name, file_match_pattern, other_actions=lambda _: None):
    try:
        # Go to the web page
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('log-level=3')
        driver = webdriver.Chrome(service=Service('./chromedriver.exe'), options=chrome_options)
        print('Waiting until the page loads completely...')
        driver.get(url)
        sleep(5)

        # Do some other optional actions (like changing the time period)
        other_actions(driver)
        sleep(5)

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
            sleep(1)
            print('Waiting for the download to finish...')
        driver.quit()
        return filepath()


def get_companies_list():
    filename = f'Companies list {dt.today().strftime("%m-%Y")}.csv'
    if not filename in os.listdir(DATA_PATH):
        filepath = __press_download_btn(
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
    def set_time_period(driver): # THIS IS NOT WORKING AS EXPECTED
                                 # (the button is not being pressed)
        actions = webdriver.ActionChains(driver, 5000)
        time_period_btn = driver.find_element(By.XPATH, f'//button[@data-value="{time_period}"]')
        actions.move_to_element(time_period_btn).click().perform()

    filename = f'{symbol.upper()} {time_period.upper()} {dt.today().strftime("%d-%m-%y")}.csv'

    if not filename in os.listdir(DATA_PATH):
        filepath = __press_download_btn(
        f'https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/historical/', 
        'historical-download', 
        r'(HistoricalData_)[0-9]+(\.csv)$',
        other_actions=set_time_period
        )
        os.rename(filepath, DATA_PATH / filename)
    df = pd.read_csv(DATA_PATH / filename, encoding='latin1', on_bad_lines='skip')
    df = df[['Date', 'Close/Last']]
    df['Date'] = pd.to_datetime(df['Date'], infer_datetime_format=True)
    df['Close/Last'] = pd.to_numeric(df['Close/Last'].apply(lambda val: val[1:]))
    return df    