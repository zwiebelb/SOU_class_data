from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import pandas as pd
import sqlite3


class WebScraper:
    def __init__(self, url):
        self.url = url
        self.driver = webdriver.Firefox()
        self.select = None
    
    def get_options_from_dropdown(self, dropdown_id, start_option):
        self.driver.get(self.url)
        select = Select(WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, dropdown_id))))
        options = [option.text for option in select.options]
        start_index = options.index(start_option)
        options = options[start_index:]
        # Filter options to only include terms with a year greater than or equal to 2005 and less than or equal to 2023
        options = [option for option in options if int(option.split()[-1]) >= 2006 and int(option.split()[-1]) <= 2023]
        self.select = select
        return options
    
    def scrape_courses_for_term(self, term):
        self.select.select_by_visible_text(term)
        button = self.driver.find_element(By.ID, 'cls-search')
        button.click()
        time.sleep(10)
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        courses = soup.find('tbody').find_all('tr')
        data = []
        for course in courses:
            crn = course.find('td', {'data-label': 'CRN'})
            if crn is not None:
                crn = crn.text.strip()
            subject = course.find('td', {'data-label': 'Subject'})
            if subject is not None:
                subject = subject.text.strip()
            number = course.find('td', {'data-label': 'Number'})
            if number is not None:
                number = number.text.strip()
            title = course.find('td', {'data-label': 'Title'})
            if title is not None:
                title = title.text.strip()
            credits = course.find('td', {'data-label': 'Credits'})
            if credits is not None:
                credits = credits.text.strip()
            instructor = course.find('td', {'data-label': 'Instructor'})
            if instructor is not None:
                instructor = instructor.text.strip()
            data.append([term, crn, subject, number, title, credits, instructor])
        return data



class DatabaseManager:
    def __init__(self, database_name):
        self.database_name = database_name
        self.conn = sqlite3.connect(self.database_name)
    
    def write_to_database(self, data):
        df = pd.DataFrame(data, columns=['Term', 'CRN', 'Subject', 'Number', 'Title', 'Credits', 'Instructor'])
        df.to_sql('courses', self.conn, if_exists='replace')
    
    def close_database(self):
        self.conn.close()
        

if __name__ == '__main__':
    # URL of the webpage to scrape
    url = 'https://inside.sou.edu/schedule/schedule.html'

    scraper = WebScraper(url)
    options = scraper.get_options_from_dropdown('terms', 'Summer 2023')

    data = []
    for option in options:
        data.extend(scraper.scrape_courses_for_term(option))

    scraper.driver.quit()

    db_manager = DatabaseManager('courses.db')
    db_manager.write_to_database(data)
    db_manager.close_database()

    df = pd.DataFrame(data, columns=['Term', 'CRN', 'Subject', 'Number', 'Title', 'Credits', 'Instructor'])
    print(df)
