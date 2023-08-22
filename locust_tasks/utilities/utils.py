import os
import csv
import re
import uuid
import logging
import requests
import subprocess

userid_list = None

def getPath(path):
    if os.path.exists(path):
        return path
    else:
        return os.path.join('/', path)

def init_userid_file(path):
    global userid_list
    userid_list = CSVReader(path)

def getCustomInputAsList(customInput):

    result_list = []
    try:
        # convert into dict if input has :
        if ":" in customInput and "{" in customInput and "}" in customInput:
            string = customInput.strip("{}")
            paris = string.split(",")
            dictonary = {}
            for pair in paris:
                key, value = pair.split(":")
                key = key.strip()
                value = int(value.strip())
                dictonary[key] = value
            keys = list(dictonary.keys())
            max_value = int(max(dictonary.values()))
            for i in range(max_value):
                for j in range(len(keys)):
                    key = keys[j]
                    value = dictonary[key]
                    if i < value:
                        result_list.append(key)
        elif "," in customInput:
            result_list = [s.strip() for s in customInput.split(",")]
        else:
            result_list.append(customInput)
        return result_list
    except Exception:
        print("Invalid custom Input format :" + str(customInput))

def getModuleNames(input):
    # eg:
    # moduleName.CLASSNAME
    # moduleName1.CLASSNAME1,moduleName2.CLASSNAME2
    # {moduleName1.CLASSNAME1:10,moduleName2.CLASSNAME2:12}
    result = re.sub(r"\.[A-Za-z0-9_-]+(?=:|,|}|$)", "", input)
    result = re.sub(r"\:[0-9]", "", result).strip("{}")
    return result

def getTestClasses(env):
    input_class = env.parsed_options.user_classes
    input_class1 = getCustomInputAsList(env.parsed_options.test_scenario)
    ip = input_class + input_class1
    if 'CUSTOM_CLASS' in ip:
        ip.remove('CUSTOM_CLASS')
    return ip

# alpha numeric
def getUniqueString():
    uniqueId = str(uuid.uuid4())
    if uniqueId[0].isdigit():
        uniqueId = chr(ord('A')+int(uniqueId[0])-1)+uniqueId[1:]
    uniqueId = uniqueId.replace("-", "").replace("_", "").lower()
    pattern = r'[^a-zA-Z0-9\s]' # matches any character that is non-alpha numeric
    uniqueId = re.sub(pattern, '', uniqueId)
    return uniqueId

def print_error_log(response):
    print("---- Request & Response print START ----")
    print("URL = " + str(response.request.method) +" "+ str(response.url))
    print("HEADERS = " + str(response.request.headers))
    print("REQUEST_BODY = " + str(response.request.body))
    print("RESPONSE_BODY = " + str(response.content))
    print("---- Request & Response print END ----")


def log_error_response(response):
    logging.error("---- Request & Response print START ----")
    logging.error("URL = " + str(response.request.method) + " " + str(response.url))
    logging.error("HEADERS = " + str(response.request.headers))
    logging.error("REQUEST_BODY = " + str(response.request.body))
    logging.error("RESPONSE_BODY = " + str(response.content))
    logging.error("---- Request & Response print END ----")

def getLocustMasterUrl():
    command = "grep -oE \"LOCUST_MASTER_IP='([^']+)'\" variables.sh | cut -d\"'\" -f2"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    ip = result.stdout.strip()

    try:
        if ip == '0.0.0.0' or ip == '<LOCUST_MASTER_IP>':
            locust_url = 'http://0.0.0.0:8089'
        else:
            locust_url = 'http://' + os.environ.get('LOCUST_MASTER_IP') + ':8089'
        headers = {'Connection': 'keep-alive'}
        requests.get(locust_url, headers=headers, timeout=1)
        return locust_url
    except Exception:
        return 'http://0.0.0.0:8089' # fallback to localhost

def stopLocustTests():
    headers = {'Connection': 'keep-alive'}
    stopResponse = requests.get(getLocustMasterUrl() + '/stop', headers=headers)
    return stopResponse

class CSVReader:

    def __init__(self, file, **kwargs):
        try:
            file = open(file)
        except TypeError:
            pass
        self.file = file
        self.reader = csv.reader(file, **kwargs)

    def __next__(self):
        try:
            return next(self.reader)
        except StopIteration:
            self.file.seek(0, 0)
            return next(self.reader)



