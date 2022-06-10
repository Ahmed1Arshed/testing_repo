import requests
from bs4 import BeautifulSoup
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

def get_url():
    url = 'https://www.southlandelectrical.com/sitemap.xml'
    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
    user_agent = user_agent_rotator.get_random_user_agent()
    headers =  {
        'Accept': '*/*',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'User-Agent': user_agent,
        'X-Requested-With': 'XMLHttpRequest'
    }
    page = requests.get(url,headers=headers)
    sitemap_index = BeautifulSoup(page.content, 'html.parser')
    sitemap_url = [element.text for element in sitemap_index.findAll('loc')]
    return sitemap_url

print(get_url())