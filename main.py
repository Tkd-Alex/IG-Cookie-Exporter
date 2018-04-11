from configparser import SafeConfigParser
from bot import Bot

def init_bot():
    config = SafeConfigParser()
    config.read('config.ini')

    return Bot(
        nogui = False,
        headless_browser = False,
        page_delay = 10,
        scp_auto = True,
        scp_ip = config.get('scp', 'ip'),
        scp_user = config.get('scp', 'user'),
        scp_password = config.get('scp', 'password'),
        scp_path = "/home/viralprod/IG-Force-Login/cookies/"
    )

if __name__ == '__main__':
    bot = init_bot()

    # brute-force all country, the cookie will'be exported auto
    #bot.try_all_country(username="", password="")

    # manual testing
    username = input("[Browser]\tInsert username page\n")
    bot.export_cookie(username)

