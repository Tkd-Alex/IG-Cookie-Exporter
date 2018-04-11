import json, requests, pickle, subprocess, os, time, paramiko
from datetime import datetime
from pprint import pprint
from time import sleep
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from scp import SCPClient


class Bot:
    def __init__(self,
                 nogui=False,
                 selenium_local_session=True,
                 use_firefox=False,
                 page_delay=25,
                 headless_browser=False,
                 proxy_address=None,
                 proxy_port=0,
                 scp_auto=False,
                 scp_ip=None,
                 scp_user=None,
                 scp_password=None,
                 scp_path=None):

        if nogui:
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()

        self.browser = None
        self.headless_browser = headless_browser
        self.proxy_address = proxy_address
        self.proxy_port = proxy_port

        self.nogui = nogui

        self.page_delay = page_delay
        self.switch_language = True
        self.use_firefox = use_firefox
        self.firefox_profile_path = None

        self.aborting = False

        self.scp_auto = scp_auto
        self.scp_ip = scp_ip
        self.scp_user = scp_user
        self.scp_password = scp_password
        self.scp_path = scp_path

        if not os.path.exists("cookies"):
            os.makedirs("cookies")

        if selenium_local_session:
            self.set_selenium_local_session()


    def set_selenium_local_session(self):
        if self.aborting:
            return self

        if self.use_firefox:
            if self.firefox_profile_path is not None:
                firefox_profile = webdriver.FirefoxProfile(self.firefox_profile_path)
            else:
                firefox_profile = webdriver.FirefoxProfile()

            firefox_profile.set_preference('permissions.default.image', 2)

            if self.proxy_address and self.proxy_port > 0:
                firefox_profile.set_preference('network.proxy.type', 1)
                firefox_profile.set_preference('network.proxy.http', self.proxy_address)
                firefox_profile.set_preference('network.proxy.http_port', self.proxy_port)
                firefox_profile.set_preference('network.proxy.ssl', self.proxy_address)
                firefox_profile.set_preference('network.proxy.ssl_port', self.proxy_port)

            self.browser = webdriver.Firefox(firefox_profile=firefox_profile)

        else:
            chromedriver_location = './chromedriver'
            chrome_options = Options()
            chrome_options.add_argument('--dns-prefetch-disable')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--lang=en-US')
            chrome_options.add_argument('--disable-setuid-sandbox')

            chrome_options.add_argument('--disable-gpu')

            chrome_options.add_extension('./editthiscookie.crx')
            chrome_options.add_extension('./holavpn.crx')

            if self.proxy_address and self.proxy_port > 0:
                chrome_options.add_argument('--proxy-server={}:{}'.format(self.proxy_address, self.proxy_port))

            if self.headless_browser:
                chrome_options.add_argument('--headless')
        
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
            chrome_options.add_argument('user-agent={user_agent}'.format(user_agent=user_agent))
            
            chrome_prefs = {
                'intl.accept_languages': 'en-US',
                'profile.managed_default_content_settings.images': 2
            }
            chrome_options.add_experimental_option('prefs', chrome_prefs)
            
            self.browser = webdriver.Chrome(chromedriver_location, chrome_options=chrome_options)

        self.browser.implicitly_wait(self.page_delay)
        self.browser.set_page_load_timeout(self.page_delay)
        
        return self

    def export_cookie(self, username=""):
        try:
            pickle.dump(self.browser.get_cookies(), open('cookies/{}_cookie.pkl'.format(username), 'wb'))
            print('[Browser]\tcookies/{}_cookie.pkl exported!'.format(username))
            
            if self.scp_auto == True and self.scp_user != None and self.scp_password != None and self.scp_ip != None and self.scp_path != None:
                try:
                    ssh = paramiko.SSHClient()
                    ssh.load_system_host_keys()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(self.scp_ip, username=self.scp_user, password=self.scp_password)
                    print("[SSH]\tConnected!")
                    scp = SCPClient(ssh.get_transport())
                    scp.put("cookies/{}_cookie.pkl".format(username), remote_path=self.scp_path)
                    print("[SCP]\tFile copied!")
                    scp.close()
                except Exception as e:
                    print("[Error]\t{}".format(e))
            
            self.browser.delete_all_cookies()
            self.browser.quit()

            if self.nogui:
                self.display.stop()
        except Exception as e:
            print("[Error]\t{}".format(e))

    def try_all_country(self, username, password):
        countrylist = [
            'AF','AL','DZ','AX','AS','AD','AO','AP','AI','AQ','AG','AR','AM','AW','AU','AT','AZ','BS','BH','JE','BD','BB','BY','BE','BZ','BJ','BM','BT','BO','BQ','BA','WF',
            'BW','BV','BR','IO','BN','BG','BF','BI','KH','CM','CA','CV','KY','CF','TD','CL','CN','CX','CC','CO','KM','CG','CK','CR','HR','CU','CW','CY','CZ','CD','DK','EH',
            'DJ','DM','DO','TP','EC','EG','SV','GQ','ER','EU','EE','ET','FK','FO','FJ','FI','FR','FX','GF','PF','TF','GA','GM','GE','DE','GH','GI','GB','GR','GL','GD','WS',
            'GP','GU','GT','GG','GN','GW','GY','HT','HM','HN','HK','HU','IS','IN','ID','IR','IQ','IE','IM','IL','IT','JM','JP','JO','KZ','KE','KI','KW','KG','LA','LV','YE',
            'LB','LS','LR','LY','LI','LT','LU','MO','MK','MG','MW','MY','MV','ML','MT','MH','MQ','MR','MU','YT','MX','FM','MD','MC','MN','ME','MS','MA','MZ','MM','NA','YU',
            'NR','NP','NL','AN','NC','NZ','NI','NE','NG','NU','NF','KP','MP','NO','OM','PK','PW','PS','PA','PG','PY','PE','PH','PN','PL','PT','PR','QA','RE','RO','RU','ZM',
            'RW','BL','SH','KN','LC','MF','PM','VC','SM','SX','ST','SA','SN','RS','SC','SL','SG','SK','SI','SB','SO','ZA','GS','KR','SS','ES','LK','SD','SR','SJ','SZ','ZW',
            'SE','CH','SY','TW','TJ','TZ','TH','TL','TG','TK','TO','TT','TN','TR','TM','TC','TV','UG','UA','AE','UK','US','UM','UY','UZ','VU','VA','VE','VN','VG','VI'
        ]
        i = 0
        while True:
            self.poweron_hola(countrylist[i])
            i += 1
            if self.login_user(username, password) is True:
                print("[{}]\nLogged with country: {}".format(username, countrylist[i]))
                break
        self.export_cookie(username)


    def poweron_hola(self, country):
        try:
            print("[VPN]\tGoing to instagram.com")
            print("[VPN]\tTry with country: {}".format(country))
            self.browser.get("http://hola.org/access/instagram.com/using/vpn-{}?go=2".format(country.lower()))
            sleep(6)
        except Exception as e:
            print("[Error]\t{}".format(e))
        
    def login_user(self, username, password, switch_language=True):

        self.browser.get('https://www.instagram.com')
        login_elem = self.browser.find_elements_by_xpath("//*[contains(text(), 'Log in')]")

        if switch_language:
            try:
                self.browser.find_element_by_xpath("//select[@class='_fsoey']/option[text()='English']").click()
            except Exception as e:
                pass

        login_elem = self.browser.find_element_by_xpath("//article/div/div/p/a[text()='Log in']")
        if login_elem is not None:
            ActionChains(self.browser).move_to_element(login_elem).click().perform()
            print("[{}]\tClick 'Log in' button".format(username))

        # Populate username and password
        input_username = self.browser.find_elements_by_xpath("//input[@name='username']")
        ActionChains(self.browser).move_to_element(input_username[0]).click().send_keys(username).perform()
        print("[{}]\tWrite username".format(username))
        sleep(1)

        input_password = self.browser.find_elements_by_xpath("//input[@name='password']")
        ActionChains(self.browser).move_to_element(input_password[0]).click().send_keys(password).perform()
        print("[{}]\tWrite password".format(username))

        login_button = self.browser.find_element_by_xpath("//form/span/button[text()='Log in']")
        ActionChains(self.browser).move_to_element(login_button).click().perform()
        print("[{}]\tClick 'Log in' button".format(username))
        sleep(5)

        return self.check_login(username)

    def check_login(self, username):
        print("[{}]\tCheck login...".format(username))
        nav = self.browser.find_elements_by_xpath('//nav')
        if len(nav) == 2:
            print("[{}]\tLogin success!".format(username))
            return True
        else:
            print("[{}]\tLogin fail!".format(username))
            return False