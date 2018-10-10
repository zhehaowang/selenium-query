#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

import time
import urllib.request

class Query():
    url = 'https://ceac.state.gov/CEACStatTracker/Status.aspx'
    visa_type_elem_name = 'ctl00$ContentPlaceHolder1$Visa_Application_Type'
    location_select_elem_name = 'ctl00$ContentPlaceHolder1$Location_Dropdown'
    ds160_textbox_elem_name = 'ctl00$ContentPlaceHolder1$Visa_Case_Number'
    submit_elem_id = 'ctl00_ContentPlaceHolder1_btnSubmit'
    captcha_elem_id = 'c_status_ctl00_contentplaceholder1_defaultcaptcha_CaptchaImage'
    refresh_captcha_id = 'c_status_ctl00_contentplaceholder1_defaultcaptcha_ReloadIcon'
    sound_captcha_id = 'c_status_ctl00_contentplaceholder1_defaultcaptcha_SoundIcon'
    audio_element_id = 'LBD_CaptchaSoundAudio_c_status_ctl00_contentplaceholder1_defaultcaptcha'

    def __init__(self):
        return

    def send_query(self, visa_type, visa_location, ds160_number):
        driver = webdriver.Chrome()
        driver.get(Query.url)
        
        type_select = Select(driver.find_element_by_name(Query.visa_type_elem_name))
        type_select.select_by_visible_text(visa_type)
        if __debug__:
            time.sleep(1)

        location_select = Select(driver.find_element_by_name(Query.location_select_elem_name))
        location_select.select_by_visible_text(visa_location)
        if __debug__:
            time.sleep(1)

        ds160_textbox = driver.find_element_by_name(Query.ds160_textbox_elem_name)
        ds160_textbox.clear()
        ds160_textbox.send_keys(ds160_number)
        if __debug__:
            time.sleep(1)

        submit = driver.find_element_by_id(Query.submit_elem_id)
        # submit.click()

    def download_captcha_imgs(self, num):
        driver = webdriver.Chrome()
        driver.get(Query.url)

        file_prefix = str(int(time.time()))

        for cnt in range(num):
            captcha_img = driver.find_element_by_id(Query.captcha_elem_id)
            refresh_captcha_btn = driver.find_element_by_id(Query.refresh_captcha_id)
            captcha_src = captcha_img.get_attribute('src')
            urllib.request.urlretrieve(captcha_src, '../imgs/' + file_prefix + '_' + str(cnt))
            refresh_captcha_btn.click()
            time.sleep(1)
        return

    def download_captcha_audios(self, num):
        driver = webdriver.Chrome()
        driver.get(Query.url)

        file_prefix = str(int(time.time()))

        for cnt in range(num):
            play_captcha_btn = driver.find_element_by_id(Query.sound_captcha_id)
            play_captcha_btn.click()
            time.sleep(1)

            audio_element = driver.find_element_by_id(Query.audio_element_id)
            audio_url = audio_element.get_attribute('src')
            urllib.request.urlretrieve(audio_url, '../audios/' + file_prefix + '_' + str(cnt) + '.wav')

            time.sleep(5)
            refresh_captcha_btn = driver.find_element_by_id(Query.refresh_captcha_id)
            refresh_captcha_btn.click()
            time.sleep(1)
        return

if __name__ == "__main__":
    visa_location = 'CHINA, BEIJING'
    ds160_number = 'AA0086FOO8'
    visa_type = 'NONIMMIGRANT VISA (NIV)'

    q = Query()
    # q.send_query(visa_type, visa_location, ds160_number)
    # q.download_captcha_audios(10)
    # q.audio_recognition('chunk4.wav')