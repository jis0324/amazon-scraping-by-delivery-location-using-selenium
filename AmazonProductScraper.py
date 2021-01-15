# -*- coding: utf-8 -*-
import re
import os
import csv
import time
import json
import random
import logging
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
LOGGER.setLevel(logging.WARNING)

base_dir = os.path.dirname(os.path.abspath(__file__))

user_agent_list = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
]

class AmazonProductSpider():

    def __init__(self):
        self.country = None
        self.link = None
        self.page_count = None
        self.get_config()

        self.result_file = "{}/result_{}.csv".format(base_dir, self.country)
                
        if os.path.exists(self.result_file):
            os.remove(self.result_file)

    def get_config(self):
        with open(base_dir + "/config.json", "r") as config_f:
            config = json.load(config_f)
        
        self.country = config["Country"]
        self.link = config["Link"]
        self.page_count = config["PageCount"]

    def set_driver(self):
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Hide info bar
            chrome_options.add_experimental_option('useAutomationExtension', False)  # Disable dev mode
            chrome_options.add_argument('--headless')
            chrome_options.add_argument("test-type")
            chrome_options.add_argument("--temp-basedir")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument("--disable-blink-features")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument('user-agent={}'.format(random.choice(user_agent_list)))
            driver = webdriver.Chrome(ChromeDriverManager().install(), options = chrome_options)
            return driver

        except:
            print(traceback.print_exc())
            return None

    def parseProductURLs(self):
        try:
            productLinks = list()

            self.driver.get(self.link)

            locationSelector = WebDriverWait(self.driver, 30).until(lambda driver: driver.find_element_by_xpath("//a[@id='nav-global-location-popover-link']"))
            time.sleep(1)

            if self.country:
                print("Selecting Country...")
                locationSelector.click()
                time.sleep(3)

                self.driver.find_element_by_xpath("//select[@id='GLUXCountryList']/..").click()
                time.sleep(1)

                self.driver.find_element_by_xpath("//select[@id='GLUXCountryList']/optgroup/option[@value='{}']".format(self.country)).click()
                time.sleep(1)

                self.driver.find_element_by_xpath("//button[@name='glowDoneButton']").click()
                time.sleep(5)

                print("Selected Country:", self.country)
            
            page_index = 1
            while True:
                products = self.driver.find_elements_by_xpath('//span[@data-component-type="s-search-results"]//div[@data-asin]//h2/a[@href]')
                
                for product in products:
                    try:
                        productURL = product.get_attribute("href").split("//")[1].split("/")
                        productLink = "https://{}/{}/{}".format(productURL[0], productURL[2], productURL[3])
                        print(" --- Found Product :", productLink, "--- ")
                        if productLink not in productLinks:
                            productLinks.append(productLink)

                    except:
                        continue
                
                print("*** Total Found Products :", len(productLinks))

                if self.page_count and page_index >= self.page_count:
                    break

                nextBTN = self.driver.find_element_by_xpath("//ul[@class='a-pagination']/li[@class='a-last']/a")
                if nextBTN:
                    page_index += 1
                    nextBTN.click()
                    print("--- Movinging To {} Page... ---".format(page_index))
                    time.sleep(5)
                else:
                    break

            return productLinks

        except:
            print(traceback.print_exc())
       
    def parseProducts(self, productLinks):

        for index, productLink in enumerate(productLinks):
            try:
                item = {
                    "product_url": productLink,
                    "product_name": "",
                    "price": "",
                    "product_category": "",
                    "product_availability": "",
                    "product_brand": "",
                    "image_url": "",
                    "currency": "",
                    "shipping_cost": "",
                    "estimated_fee": "No Import Fee",
                    "ASIN": "",
                    "review": "",
                    "review_count": "",
                    "sales_rank": "",
                    "dimension": "",
                    "weight": "",
                    "ships_from": "",
                    "sold_by": "",
                    "seller": "",
                }

                self.driver.get(productLink)
                title = WebDriverWait(self.driver, 30).until(lambda driver: driver.find_element_by_xpath('//h1[@id="title"]'))
                time.sleep(1)

                try:
                    title = re.sub(r"\s+", " ", title.find_element_by_xpath('./span').text)
                    item['product_name'] = title.strip()
                except:
                    pass

                try:
                    item['price'] = self.driver.find_element_by_xpath('//span[contains(@id,"ourprice") or contains(@id,"saleprice")]').text.strip()
                except:
                    pass

                try:
                    item['product_category'] = ','.join(map(lambda x: x.text.strip(), self.driver.find_elements_by_xpath('//a[@class="a-link-normal a-color-tertiary"]'))).strip()
                except:
                    pass

                try:
                    item['product_availability'] = self.driver.find_element_by_xpath('//div[@id="availability"]').text.strip()
                except:
                    pass

                try:
                    item["product_brand"] = self.driver.find_element_by_xpath("//div[@data-brand]/@data-brand").text.strip()
                except:
                    pass

                try:
                    if not item["product_brand"]:
                        featureList = self.driver.find_elements_by_xpath("//div[@id='productOverview_feature_div']//table//tr")
                        for feature in featureList:
                            if "Brand" in feature.find_element_by_xpath("./td[1]").text:
                                item["product_brand"] = feature.find_element_by_xpath("./td[last()]").text.strip()
                                break
                except:
                    pass

                try:
                    if not item["product_brand"]:
                        item["product_brand"] = self.driver.find_element_by_xpath("//a[@id='bylineInfo']").text.split(":")[1].strip()
                except:
                    pass

                try:
                    if not item["product_brand"]:
                        item["product_brand"] = item["product_name"].split(" ")[0].strip()
                except:
                    pass

                try:
                    item["image_url"] = self.driver.find_element_by_xpath('//img[@id="landingImage"][@data-old-hires]').get_attribute("data-old-hires").strip()
                except:
                    pass
                
                try:
                    item["currency"] = re.sub(r"[\,\.\d]+", "", item["price"]).strip()
                except:
                    pass

                try:
                    priceDetails = self.driver.find_elements_by_xpath('//div[@id="a-popover-agShipMsgPopover"]/table//tr')
                    for detail in priceDetails:
                        try:
                            if "Shipping" in detail.find_element_by_xpath("./td[1]/span").get_attribute("textContent"):
                                item["shipping_cost"] = detail.find_element_by_xpath("./td[last()]/span").get_attribute("textContent").strip()

                            if "Estimated" in detail.find_element_by_xpath("./td[1]/span").get_attribute("textContent"):
                                item["estimated_fee"] = detail.find_element_by_xpath("./td[last()]/span").get_attribute("textContent").strip()
                        except:
                            continue
                except:
                    pass
                
                try:
                    item["ASIN"] = self.driver.find_element_by_xpath("//input[@id='all-offers-display-params'][@data-asin]").get_attribute("data-asin").strip()

                    if not item["ASIN"]:
                        item["ASIN"] = self.driver.find_element_by_xpath("//div[@id='averageCustomerReviews'][@data-asin]").get_attribute("data-asin").strip()
                except:
                    pass

                try:
                    item["review"] = self.driver.find_element_by_xpath('//table[@id="productDetails_detailBullets_sections1"]//div[@id="averageCustomerReviews"]/..').text.strip()
                except:
                    pass

                try:
                    item["review_count"] = self.driver.find_element_by_xpath('//table[@id="productDetails_detailBullets_sections1"]//div[@id="averageCustomerReviews"]/span[last()]').text.strip()
                except:
                    pass

                try:
                    productInfoList = self.driver.find_elements_by_xpath('//table[@id="productDetails_detailBullets_sections1"]//tr')
                    for tr in productInfoList:
                        try:
                            if "Best Sellers Rank" in tr.find_element_by_xpath("./th").text:
                                item["sales_rank"] = re.search(r"\#[\d,]+", tr.find_element_by_xpath("./td").text).group()

                            if "Dimension" in tr.find_element_by_xpath("./th").text:
                                item["dimension"] = tr.find_element_by_xpath("./td").text.strip()

                            if "Weight" in tr.find_element_by_xpath("./th").text:
                                item["weight"] = tr.find_element_by_xpath("./td").text.strip()

                        except:
                            continue
                except:
                    pass

                try:
                    buyboxList = self.driver.find_elements_by_xpath("//div[@id='tabular-buybox']/table//tr")
                    for tr in buyboxList:
                        try:
                            if "Ships from" in tr.find_element_by_xpath("./td[1]/span").text:
                                item["ships_from"] = tr.find_element_by_xpath("./td[last()]/span").text.strip()

                            if "Sold by" in tr.find_element_by_xpath("./td[1]/span").text:
                                item["sold_by"] = tr.find_element_by_xpath("./td[last()]/span").text.strip()
                        except:
                            continue
                except:
                    pass

                try:
                    item["seller"] = tr.find_element_by_xpath("//a[@id='sellerProfileTriggerId'][@href]").get_attribute("href").split("seller=")[1].split("&")[0].strip()
                except:
                    pass


                print("-------------------{} / {} ----------------------".format(index, len(productLinks)))
                print(json.dumps(item, indent=2))

                file_exist = os.path.exists(self.result_file)

                with open(self.result_file, "a", encoding="utf-8", errors="ignore", newline="") as f:
                    fieldnames = ["product_url", "product_name", "price", "product_category", "product_availability", "product_brand", "image_url", "currency", "shipping_cost", "estimated_fee", "ASIN", "review", "review_count", "sales_rank", "dimension", "weight", "ships_from", "sold_by", "seller"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    if not file_exist:
                        writer.writeheader()

                    writer.writerow(item)
            except:
                traceback.print_exc()
                continue

    def start(self):
        try:
            # create webdriver
            self.driver = self.set_driver()
            productLinks = self.parseProductURLs()

            self.parseProducts(productLinks)
        except:
            traceback.print_exc()
        finally:
            if self.driver is not None:
                self.driver.quit()
                self.driver = None

if __name__ == "__main__":
    
    spider = AmazonProductSpider()
    spider.start()