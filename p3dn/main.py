# p3dn crawler
from operator import index
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import time
from requests import Session
import pandas as pd

# Global variables
users = pd.read_csv('data.csv', sep=';')
# remove space from nip_penandatangan
users['nip_penandatangan'] = users['nip_penandatangan']
# remove space from nip_penandatangan
users['nip_penandatangan'] = users['nip_penandatangan'].apply(lambda x: str(x).replace(' ', ''))
# Edge driver
driver = webdriver.Edge(executable_path="./msedgedriver.exe")
driver.maximize_window()

for user in users['nip_penandatangan'].tolist():
    # login
    driver.get("https://p3dn.sipd.kemendagri.go.id/")
    # wait for page to load
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/form/div[1]/div[1]/label')))
    element.click()
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div/div[2]/form/div[2]/div/div/div[2]/div')))
    element.click()
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="react-select-2-input"]')))
    element.send_keys("Provinsi Lampung")
    element.send_keys(Keys.RETURN)
    # input username
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//input[@name="username"]')))
    element.send_keys(user)
    # input password
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//input[@name="password"]')))
    element.send_keys('lampungprov')
    # click login
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//button[@type="submit"]')))
    element.click()
    try:
        # wait for page to load navbar
        element = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, '//div[@class="sub-header-container"]')))
        pass
    except TimeoutException:
        print('Login gagal')
        users.loc[users['nip_penandatangan'] == user, 'status_login'] = 'gagal'
        continue
    try:
        # wait for page to load
        element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/div[1]/div[4]/div[1]/div/div/div[1]/div')))
        # get token from local storage
        token = driver.execute_script("return window.localStorage.getItem('token');")
        
        # driver header for request
        if token:
            headers = {
            'authority': 'p3dn.sipd.kemendagri.go.id',
            'accept': 'application/json, text/plain, */*',
            'authorization': 'Bearer ' + token,
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            'content-type': 'application/json;charset=UTF-8',
            'origin': 'https://p3dn.sipd.kemendagri.go.id',
            'sec-fetch-site': 'same-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://p3dn.sipd.kemendagri.go.id/',
            'sec-ch-ua-platform': 'Windows'
            }
            bulans = ['januari', 'februari', 'maret', 'april', 'mei', 'juni', 'juli', 'agustus', 'september', 'oktober', 'november', 'desember']
            if 'status_login' not in users.columns:
                users['status_login'] = 'gagal'
            # if bulan not in users header add bulan
            for bulan in bulans:
                if bulan not in users.columns:
                    users[bulan] = "no data"
            bulan = 1
            while bulan <= 12:
                # get data from api
                req = Session()
                # add certificate to req
                req.verify = False
                # req.cert = 'cert.pem'

                url = 'https://apip3dn.sipd.kemendagri.go.id/auth/pppdn/index?tahun=2022&bulan=%s'%bulan
                users.loc[users['nip_penandatangan'] == user, 'status_login'] = 'BERHASIL'
                response = req.get(url, headers=headers)
                if response != 'null':
                    data = response.json()
                    # covert data list to dataframe
                    df = pd.DataFrame(data)
                    # if df header realisasi_belanja exists
                    if 'realisasi_belanja' in df.columns:
                        if df['realisasi_belanja'].sum() > 0:
                            users.loc[users['nip_penandatangan'] == user, bulans[bulan-1]] = f'SUDAH' if df['realisasi_belanja'].sum() > 0 else 'BELUM-SUM-R-0'
                        else:
                            users.loc[users['nip_penandatangan'] == user, bulans[bulan-1]] = 'BELUM R-0'
                        # save to csv
                        df.to_csv(f'data/{user}-{bulan}.csv', index=False, sep=';', header=True)
                    else:
                        print(f'{user} {bulan} tidak ada realisasi belanja')
                        # df.to_csv(f'data/{user}-{bulan}-tanparealisasi.csv', index=False, sep=';', header=True)
                        users.loc[users['nip_penandatangan'] == user, bulans[bulan-1]] = 'BELUM-KOLOM-REALISASI-NOT-FOUND'
                else:
                    users.loc[users['nip_penandatangan'] == user, bulans[bulan-1]] = 'BELUM-DATA-NULL'
                bulan += 1
        else:
            print('token not found')
            users.loc[users['nip_penandatangan'] == user, 'status_login'] = 'GAGAL'

    except:
        users.loc[users['nip_penandatangan'] == user, 'status_login'] = 'GAGAL'
        pass
# close driver
driver.close()
# generate timestamp
timestamp = time.strftime("%Y%m%d-%H%M%S")
# add ' on first nip_penandatangan value
users['nip_penandatangan'] = "'" + users['nip_penandatangan']
# save to csv only if status_login is berhasil
users.to_csv(f'result-data-{timestamp}.csv', index=False, sep=';', header=True)