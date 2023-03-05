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
    results = query_html.find_all('li', class_="TrT0Xe")
    substitutes = []
    if not results:
        results = query_html.find('div', class_="MjjYud")
        if not results:
            return substitutes
        results = results.find_all('span')
        for result in results:
            if "." in result.text:
                substitutes.append(result.text)
        return substitutes
    for result in results:
        result = result.text.split('.')[0]
        substitutes.append(result)
    return substitutes

# FOR REQUIREMENTS 4 AND 5
# returns string
def get_url(query:str):
    return "https://www.google.com/search?q=" + query.replace(" ","+")



# UNCOMMENT TO TEST
# print(get_substitute("what can i substitute for flour"))