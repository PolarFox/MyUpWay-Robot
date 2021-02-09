"""Template robot with Python."""
from datetime import datetime
from RPA.Robocloud.Secrets import Secrets
from RPA.Browser.Playwright import Playwright as Browser
import os
import re
from pymongo import MongoClient
from urllib.parse import urlparse, urljoin


secret = Secrets()

MONGODB_CONNECTION_STRING = secret.get_secret("db")["connection_string"]
db = MongoClient(host=MONGODB_CONNECTION_STRING)["MyUpWayData"]

browser = Browser()
url = urlparse("https://myupway.com/LogIn?ReturnUrl=%2fSystem%2f{}%2fStatus%2fServiceInfo".format(secret.get_secret("myupway")["system"]))
term = "python"



def login_myupway():
    browser.new_page(url.geturl())
    browser.type_text("#Email", secret.get_secret("myupway")["username"])
    browser.type_text("#Password", secret.get_secret("myupway")["password"])
    browser.click(".LoginButton")

def read_heatpump_data():
    tracked_labels = ("avg. outdoor temp", "hot water charging", "outdoor temp.", "degree minutes", "hot water top", "flow", "heat medium flow", "external flow temp.", "calculated flow temp.", "external adjustment", "outdoor temp.", "return temp.", "room temperature", "addition temperature", "heating, compr. only.", "heating, int. add. incl.", "hotwater, compr. only.", "hw, incl. int. add", "country", "product", "version", "serial number","electrical addition power", "set max electrical add.", "time factor", "calculated flow temp.")
    heatpump_url = url.scheme+"://"+url.hostname+"/System/{}/Status/ServiceInfo".format(secret.get_secret("myupway")["system"])
    browser.go_to(heatpump_url)
    sensor_data = get_element_values(browser.get_elements("xpath=/html/body/div[2]/div[2]/div[1]/div[2]/table/tbody/tr"), tracked_labels)
    return sensor_data

def read_slave_data(slave_num: int=1):
    tracked_labels = ("defrosting EB101", "pump speed heating medium EB101","pump speed heating medium","compressor starts EB101", "cpr. protection mode EB101", "condenser out EB101", "evaporator EB101", "hot gas EB101", "liquid line EB101", "return temp. EB101", "suction gas EB101", "high pressure sensor EB101", "low pressure sensor EB101", "compressor operating time EB101", "compressor operating time hot water EB101", "current compr. frequency EB101", "requested compressor freq EB101", "product","version EB101", "outdoor temp. EB101")
    slave_url = "{}://{}/System/{}/Status/ServiceInfo/{}".format(url.scheme,url.hostname,secret.get_secret("myupway")["system"],slave_num)
    browser.go_to(slave_url)
    sensor_data = get_element_values(browser.get_elements("xpath=/html/body/div[2]/div[2]/div[1]/div[2]/table/tbody/tr"),tracked_labels)
    return sensor_data

def get_element_values(elements, tracked_labels: tuple):
    timestamp = datetime.utcnow()
    retval = [] # List of dicts
    for i, x in enumerate(elements):
        element_info = browser.get_text(elements[i]).split("\t")
        if not element_info[0].strip().startswith(tracked_labels):
            continue
        value_parts = parse_value(element_info[1])
        if value_parts:
            data_dict = {"value": float(value_parts[0]), "unit": value_parts[1]}
        else:
            data_dict = {"value": element_info[1]}
        if re.search(r"[A-Z]{1,3}[0-9]+$", element_info[0]):
            for label in tracked_labels:
                if element_info[0].startswith(label):
                    data_dict["label"] = label
                    data_dict["sensor"] = element_info[0].replace(label,"").strip("-").strip()
                    break
        else:
            data_dict["label"]=element_info[0].strip()
        if "label" in data_dict.keys():
            data_dict["timestamp"] = timestamp
            retval.append(data_dict)

    return retval
        
def parse_value(value: str) -> list:
    value_parts = None
    if "°" in value or "º" in value: # Temperature
        value_parts = value.replace("º","°").split("°")
        value_parts[1] = "°" + value_parts[1]
    elif value.endswith("kWh"):
        value_parts = [value.split("kWh")[0], "kWh"]
    elif value.endswith("kW"):
        value_parts = [value.split("kW")[0], "kW"]
    elif value.endswith("A"):
        value_parts = [value.split("A")[0], "A"]
    elif value.endswith("DM"):
        value_parts = [value.split("DM")[0], "DM"]
    elif value.endswith("l/m"):
        value_parts = [value.split("l/m")[0], "l/m"]
    elif value.endswith("bar"):
        value_parts = [value.split("bar")[0], "bar"]
    elif value.endswith("Hz"):
        value_parts = [value[:-2], "Hz"]
    elif value.endswith("h"):
        value_parts = [value[:-1], "h"]
    return value_parts

def minimal_task():
    print("Done.")
    print(f"Secrets: {secret.get_secret('myupway')}")


if __name__ == "__main__":
    minimal_task()
    login_myupway()
    heatpump_data = read_heatpump_data()
    heatpump_data = [{**x,**{"system": secret.get_secret("myupway")["system"]} } for x in heatpump_data]
    db["heatpump"].insert_many(heatpump_data)
    slave1_data = read_slave_data(1)
    slave1_data = [{**x,**{"system": secret.get_secret("myupway")["system"]} } for x in slave1_data]
    db["slave"].insert_many(slave1_data)
    browser.close_browser("ALL")
