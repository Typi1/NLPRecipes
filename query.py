from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# FOR REQUIREMENT 7
# returns list of substitutes
def get_substitute(query:str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    url = "http://www.google.com/search?q=" + query + "&start=" + str((0))
    driver.get(url)
    query_html = BeautifulSoup(driver.page_source, 'html.parser')
    results = query_html.find('div', id="search")
    results = results.find('div', class_="v7W49e")
    results = results.find('div', class_="MjjYud")
    first_attempt = results.find_all('li', class_="TrT0Xe")
    substitutes = []
    if not first_attempt:
        second_attempt = results.find('span', class_="ILfuVd")
        if not second_attempt:
            third_attempt = results.find_all('span', {"class": None, "id": None, "data-ved": None})
            substitutes.append(third_attempt[-1].text)
            return substitutes
        substitutes.append(second_attempt.text)
        return substitutes
    for result in first_attempt:
        result = result.text.split('.')[0]
        substitutes.append(result)
    return substitutes

# FOR REQUIREMENTS 4 AND 5
# returns string
def get_url(query:str):
    return "https://www.google.com/search?q=" + query.replace(" ","+")



# UNCOMMENT TO TEST
# print(get_substitute("what can i use instead of eggs"))