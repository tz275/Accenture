from selenium import webdriver
import time
from selenium.webdriver.common.by import By
import re
import random
import json
from selenium.webdriver.chrome.service import Service
from datetime import date, timedelta
import requests
from bs4 import BeautifulSoup


# init beautiful soup
session = requests.Session()
headers = {
        'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:46.0) Gecko/20100101 Firefox/46.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection' : 'Keep-Alive',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

def getAllPostedAndJobUrl(wd):
    ret = []
    today = date.today()
    for i in wd.find_elements(By.CSS_SELECTOR, ".cmp-teaser__title-link"):
        if i.get_attribute("data-href"):
            posted = i.find_element(By.CSS_SELECTOR, ".cmp-teaser__job-listing.cmp-teaser__job-listing-posted-date").text
            job_url = i.get_attribute("data-href")
            passed_number = re.search(r'\d+', posted)
            if passed_number:
                posted_number = int(passed_number.group())
            else:
                continue
            is_day = re.search(r'day', posted)
            if is_day:
                posted = today - timedelta(days = posted_number)
                posted = posted.strftime("%Y-%m-%d")
                ret.append([posted, job_url])
                continue
            is_month = re.search(r'monthy', posted)
            if is_month:
                posted = today - timedelta(days = posted_number * 30)
                posted = posted.strftime("%Y-%m-%d")
                ret.append([posted, job_url])
    return ret

def nextPage(page_index):
    return f"https://www.accenture.com/us-en/careers/jobsearch?jk=&sb=1&vw=0&is_rj=0&pg={page_index}"

def saveFile(file, index):
    with open(f"accenture{index}.json", 'w') as f:
        json.dump(file, f)



file_count = 1
to_save = []
page_index = 1
while True:
    # start selenium
    wd = webdriver.Chrome(r'/Users/tingkangzhao/SeleniumDriver/chromedriver')
    wd.implicitly_wait(10)
    url = nextPage(page_index)
    wd.get(url)

    posted_and_job_urls = getAllPostedAndJobUrl(wd)
    this_job = {}
    for job in posted_and_job_urls:
        try:
            # init for each job
            url_obj = session.get(job[1])
            bs = BeautifulSoup(url_obj.text, "html.parser")

            # Searching jobs go here
            ## Job Location
            if len([i for i in bs.find('div', {"class": "cmp-job-listing-hero__labels-container"}).text.split('\n') if i]) <= 2: # single location
                jobLocation = [i for i in bs.find('div', {"class": "cmp-job-listing-hero__labels-container"}).text.split('\n') if i][0]
                location = jobLocation.split('-')
                state = location[0].strip()
                city = location[1].strip()
            else: # multiple locations
                jobLocation = bs.find_all('div', {'class': 'description-content'})[-1].text.lstrip()
                state, city = '', ''
                for location in jobLocation.split(','):
                    location = location.split('-')
                    state += location[0].strip()
                    city += location[1].strip()
            ## Job Description
            jobDescription = bs.find('div', {'class': "cmp-job-listing-details__desc-block"})
            remote = False
            for i in jobDescription.text.split(' '):
                if re.search(r'remote', i, re.IGNORECASE):
                    remote = True
            if remote is True:
                remote = "remote"
            else:
                remote = "in-person"
            ## Education Requirement
            if re.search(r"bachelor", bs.find_all('div', {'class': "description-content"})[1].text.lstrip(), re.IGNORECASE):
                banchelors = 'banchelors'
            else:
                banchelors = None
            if re.search(r"master", bs.find_all('div', {'class': "description-content"})[1].text.lstrip(), re.IGNORECASE):
                masters = "masters"
            else:
                masters = None
            if re.search(r"phd", bs.find_all('div', {'class': "description-content"})[1].text.lstrip(), re.IGNORECASE):
                phd = 'phd'
            else:
                phd = None
            education = ''.join([i for i in [banchelors, masters, phd] if i])
                

            
            # Assign job goes here
            this_job["posted"] = job[0]

            this_job["jobID"] = jobId = [i for i in bs.find('div', {"class": "cmp-job-listing-hero__labels-container"}).text.split('\n') if i][-1]
            this_job["origin_search"] = "https://www.accenture.com/us-en/careers/jobsearch?jk=&sb=1&vw=0&is_rj=0&pg=1"
            this_job['jobTitle'] = bs.find('div', {"class": "cmp-job-listing-hero__title-container"}).text
            this_job['companyName'] = "Accenture"
            this_job["link"] = job[1]
            this_job["jobLocation"] = {"remote": remote, "city": city, "state": state, "country": None}
            this_job["educationRequirement"] = {"education": education, "major": None}
            this_job["jobType"] = None
            this_job["visaSponsorship"] = {"none": True, "cpt_opt": False, "h1b": False, "eb": False}
            this_job["salary"] = {"min":None, "max":None}
            this_job["benefits"] = {
                "_401k": False,
                "paidTimeOff": False,
                "insurance": {
                    "medical": False,
                    "dental": False,
                    "vision": False,
                    "life": False
                },
                "other": []
                }
            this_job["requirements"] = [bs.find_all('div', {'class': "description-content"})[1].text.lstrip()]
            this_job["jobDescription"] = bs.find('div', {'class': "cmp-job-listing-details__desc-block"}).text
            to_save.append(this_job)
            time.sleep(random.randint(3, 9))
        except:
            pass
    
    # goes to next page
    page_index += 1
    wd.quit()
    time.sleep(random.randint(3, 9))
    # save the file if it reaches the number
    if len(to_save) >= 100:
        saveFile(to_save, file_count)
        file_count += 1
        to_save = []

    if file_count > 1:
        break

wd.quit()