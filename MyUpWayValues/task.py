"""Template robot with Python."""
from RPA.Robocloud.Secrets import Secrets
from RPA.Browser.Playwright import Playwright as Browser

secret = Secrets()

browser = Browser()
url = "https://myupway.com/LogIn?ReturnUrl=%2fSystem%2f{}%2fStatus%2fServiceInfo".format(secret.get_secret("myupway")["system"])
term = "python"

def login_myupway():
    browser.open_browser(url)
    browser.type_text("#Email", secret.get_secret("myupway")["username"])
    browser.type_text("#Password", secret.get_secret("myupway")["password"])
    browser.click(".LoginButton")

def read_data():
    handle_data_elements(browser.get_elements("xpath=/html/body/div[2]/div[2]/div[1]/div[2]/table[1]/tbody/tr/td[2]/span"))
    browser.take_screenshot(fullPage=True)

def handle_data_elements(elements):
    for x in elements:
        print(x)

def minimal_task():
    print("Done.")
    print(f"Secrets: {secret.get_secret('myupway')}")


if __name__ == "__main__":
    minimal_task()
    login_myupway()
    read_data()