import os, re
from time import sleep
from pandas import read_csv
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service


def __press_download_btn(url, btn_class_name, file_match_pattern, other_actions=lambda _: None):
    try:
        # Go to the web page
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('log-level=3')
        driver = webdriver.Chrome(service=Service('./chromedriver.exe'), options=chrome_options)
        driver.get(url)

        # Do some other optional actions (like changing the time period)
        other_actions(driver)
        sleep(5)

        # Press the download button
        download_btn = driver.find_element(By.CLASS_NAME, btn_class_name)
        driver.execute_script("arguments[0].click();", download_btn)

    except:
        print('SELENIUM ERROR')
        raise

    else:
        # Get and return the file
        file_path = lambda: sorted(Path(Path.home() / 'Downloads').iterdir(), key=os.path.getmtime)[-1]
        while not re.match(file_match_pattern, file_path().name):#file_path().endswith('.tmp') or not file_path().endswith('.csv') :
            sleep(1)
            print('Waiting download...')
        driver.quit()
        return str(file_path())


def get_companies_list():
    file_path = __press_download_btn(
        'https://www.nasdaq.com/market-activity/stocks/screener/', 
        'ns-download-1', 
        r'(nasdaq_screener_)[0-9]+(\.csv)$')
    df = read_csv(file_path, encoding='latin1', on_bad_lines='skip', index_col=0)
    return df[['Name', 'Country', 'Sector', 'Market Cap']]


def get_company_data(company_symbol:str, time_period:str):
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
        time_period_btn = driver.find_element(By.XPATH, f'//button[@data-value="{time_period}"]')
        actions = webdriver.ActionChains(driver)
        actions.move_to_element(time_period_btn).perform()
        actions.click().perform()
        
    file_path = __press_download_btn(
        f'https://www.nasdaq.com/market-activity/stocks/{company_symbol.lower()}/historical/', 
        'historical-download', 
        r'(HistoricalData_)[0-9]+(\.csv)$',
        other_actions=set_time_period)
    df = read_csv(file_path, encoding='latin1', on_bad_lines='skip', index=False)
    return df[['Date', 'Close/Last']]
 