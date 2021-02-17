import requests
import re
import json
import time
import logging
import pandas
from pathlib import Path
from collections import OrderedDict
from bs4 import BeautifulSoup
from datetime import datetime
from random import randint
# Importing a module
import sys
sys.path.append('alchemy_mod/')
from alchemy import *

# This script is for scraping data from seek
############################################### Functions
def date_str_obj(date_str):
    return datetime.strptime(date_str, '%d %b %Y').date()

def clean_salary(salary_strings):
    # Removing extra explanation of the salary
    reg_salary = re.findall("\$\d*(?:,|k|\d*)\d*", salary_strings)

    new_list = list()
    for item in reg_salary:
        new_item=item.replace('$','').replace(',','').replace('k','000').replace('K','000')
        # In case after regex, it's empty ''
        if (new_item==''):
            new_list.append(0)
        else:
            salary_int = int(new_item)
            new_list.append(salary_int)

    # If new_list is empty
    if (len(new_list)== 0):
        return 0
   # if new_list isn't empty
    else:
        if max(new_list)<500:
            # If it's hourly rate, return None
            return 0
        else:
            # Sometimes it's $100 - $120k
            if(new_list[0]<1000):
                new_list[0]=new_list[0]*1000
            # We want either one or two values $30k  or  average of $30k - $40k
            wanted_list = new_list[:2]
            return (sum(wanted_list)/len(wanted_list))

def get_bs(session, url):
    """ Makes a GET request using the given session object and returns a BeautifulSoup object"""
    r = None
    while True:
        r = session.get(url)
        time.sleep(randint(1,5))# 1,10
        if r.ok:
            break
    return BeautifulSoup(r.text,'lxml')

def get_pages(category_base_URL, session):
    """ Function to return all available page urls"""
    page_list = list()
    scraped_num = 1

    while True:
        time.sleep(randint(1,5))# 1,10
        appendix_str = '?page='+str(scraped_num)+"&sortmode=ListedDate" # Sort by date
        this_page_url = category_base_URL + appendix_str

        if (endOf_listing(this_page_url, session)):
            break
        else:
            page_list.append(this_page_url)
            scraped_num = scraped_num + 1
    return page_list

def get_pages_manually(category_base_URL, page_sum):
    """ Function to return all available page urls given number of pages in this job category"""
    page_list = list()
    page_num = 0

    while True:
        appendix_str = '?page='+str(page_num)+"&sortmode=ListedDate" # Sort by date
        this_page_url = category_base_URL + appendix_str

        if (page_num >= page_sum):
            break
        else:
            page_list.append(this_page_url)
            page_num = page_num + 1
    return page_list

def endOf_listing(page_url, session):
    """Function to check if this page contain any job listing"""
    job_listings_bs = get_bs(session, page_url).find('div', {"class":"_3MPUOLE"})
    return (job_listings_bs == None)

def get_job_url_id_list (page_url, session):
    """Function to scrape a list of JobID and JobListing URL"""
    """I want to make it only scrape JobID and url if it's not in previous_jobIDs_hs"""

    job_listings_bs = get_bs(session, page_url).find('div', {"class":"_3MPUOLE"}).select('div[data-search-sol-meta]')
    # Loop through job listing divs
    import ast
    job_list = list()
    for a in job_listings_bs:
        job_listing_info = list()
        map_str = a["data-search-sol-meta"]
        meta_map = ast.literal_eval(map_str)

        job_id = meta_map['jobId']
        # Only include the job_listing not scraped before (by making sure the jobId is not in previous_jobIDs_hs)
        if(not (job_id in previous_jobIDs_hs)):
            #jobs_to_scrape_today.add(job_id)
            job_listing_info.append(job_id)
            # Getting job_listing_url
            job_listing_url=a.find('a', {"class":"_2iNL7wI"})['href']
            job_listing_info.append(job_listing_url)
            job_list.append(job_listing_info)
    print("Got a list of job URLs and IDs from : {}".format(page_url))
    return job_list

def store_jobInfo(job_info_list,engine):
    """Function to store a job entry"""
    # Preparing for insert
    column_list = ['JobID', 'job_description', 'company_name', 'job_title', 'job_listing_date',
                   'job_location', 'work_type', 'job_classification', 'salary_original',
                    'salary_int']

    value_list = job_info_list
    query_dict = get_query_dict(column_list, value_list)
    # print(query_dict)
    tables_list = get_tables(engine)
    # Insert
    insert_value(engine, tables_list, 1, query_dict)

def scrape_a_job(job_listing_url, session, job_id, engine):
    print("Scraping " + job_listing_url)
    """Function to scrape a jon listing"""
    # Making sure that this page contains job_listings in case that the webpage content changes simultaneously

    job_information = list()
    job_information.append(job_id)
    seeker_bs = get_bs(session,job_listing_url)
    # Get the job descrition
    job_description = seeker_bs.find('div', {"class": "FYwKg WaMPc_4"}).text
    job_information.append(job_description)

    # Company name 2 scenarios
    company_nameA = seeker_bs.find('span', {"data-automation":"advertiser-name"})
    company_nameB = seeker_bs.find('span', {"data-automation":"job-header-company-review-title"})

    if (company_nameA):
        job_information.append(company_nameA.text)
    elif (company_nameB):
        job_information.append(company_nameB.text)
    else:
        job_information.append("company_name None")

    # Job title
    job_title = seeker_bs.find('span', {"class": "_3FrNV7v _12_uzrS E6m4BZb"}).text
    job_information.append(job_title)

    # Job info div <section aria-labelledby="jobInfoHeader">
    job_info_div = seeker_bs.find('section', {"aria-labelledby" : "jobInfoHeader"})
    ## Retrieving job information, including job_listing_time, job_location, work_type, job_classification
    job_info = job_info_div.find_all('span',{"class": "_3FrNV7v _3PZrylH E6m4BZb"})

    job_listing_time = job_info[0].text
    # Convert it to date object
    job_listing_date = date_str_obj(job_listing_time)
    job_information.append(job_listing_date)

    job_location = job_info[1].text
    job_information.append(job_location)

    if (len(job_info)==4):
        work_type = job_info[2].text
        job_information.append(work_type)
        job_classification = job_info[3].text
        job_information.append(job_classification)
        # Placeholders for salary
        job_information.append("Salary None")
        job_information.append(0)
    else:
        work_type = job_info[3].text
        job_information.append(work_type)
        job_classification = job_info[4].text
        job_information.append(job_classification)
        salary = job_info[2].text
        # Original salary description
        job_information.append(salary)
        # Convert str to int
        salary_int = clean_salary(salary)
        job_information.append(salary_int)
    # Storing it into sql database
    store_jobInfo(job_information, engine)
    # After successfully scraping a job listing, add it to previous_jobIDs_hs
    previous_jobIDs_hs.add(job_id)
    return job_information


def scrape_jobs (base_url, job_urls_list, limit, session, engine):
    """Function to scrape many job listings"""
    scraped_num=0
    info_container = list()
    for item in job_urls_list:
        job_url = item[1]
        job_listing_url = base_url+job_url
        time.sleep(randint(1,5)) #1, 10
        job_info = scrape_a_job(job_listing_url,session,item[0], engine)
        info_container.append(job_info)

        scraped_num += 1
        if(scraped_num>=limit):
            break

    return info_container

def retireve_jobIDs(engine):
    """Function to retrieve a list of existing jobIDs from mySQL table"""
    q = 'select JobID from seek;'
    with engine.begin() as con:
        result = con.execute(q).fetchall()

    jobIDs = [item[0] for item in result]
    return jobIDs

######################################################## End of functions
# Set up for scraping 
headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate",

    }
session = requests.session()
session.headers.update(headers)
logging.basicConfig(level=logging.INFO)
# Making database connection
engine = make_connection('scrap')
# Retrieving previous_jobIDs from mySQL
previous_jobIDs = retireve_jobIDs(engine)
previous_jobIDs_hs = set(previous_jobIDs)
#######################################################
# Checking if the website allows scraping. Anything other than 200 means No or partially
base_url = 'https://www.seek.com.au/'
r = session.get(base_url)
r.status_code
#########################################################
# Now I need to scrape a list of job url, job ID in IT
IT_base_URL = "https://www.seek.com.au/jobs-in-information-communication-technology"
category_base_URL = "https://www.seek.com.au/jobs-in-call-centre-customer-service" # Stopped at page 40
# Retriving available pages
# page_list = get_pages(IT_base_URL, session)
page_list = get_pages_manually(category_base_URL, 200) # We assume that for each category, there're a maximum of 200 pages
##########################################################################
"""🌸Scraper Version 1"""
for item in page_list:
    for i in range(3):
        time.sleep(30+60*i)
        try:
            # Getting all job_listing URLs from a page
            job_urls_list = get_job_url_id_list(item, session)
            time.sleep(randint(1,10))# 1,10
            # Number of job listings on this page
            num_job_listing = len(job_urls_list)
            # Scraping job listings from the page above
            base_url = "https://www.seek.com.au"
            seek_results = scrape_jobs(base_url, job_urls_list, num_job_listing, session, engine)
            logging.info('[!] Scraping finished. Total: {} from page: {}'.format(len(seek_results), item))
            break
        except:
            print("Error: {}".format(item))










#
