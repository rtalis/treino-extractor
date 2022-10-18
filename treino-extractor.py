import re
import os
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


EMAIL = input("Trei.no E-mail: ")
PASSWD = input("Trei.no Password: ")


def configure_driver():
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    if os.name == 'nt':
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options)
    else:
        driver = webdriver.Chrome(options = chrome_options)
    return driver


def get_workout(driver, no_workout):
    if no_workout == 1:
        driver.get("https://app.trei.no/#/painel/treino")
        try:
            WebDriverWait(driver, 10).until(
                lambda s: s.find_element(By.NAME, "email").is_displayed())
            email_field = driver.find_element(By.NAME, "email")           
            email_field.send_keys(EMAIL, Keys.ENTER)
            WebDriverWait(driver, 10).until(
                lambda s: s.find_element(By.NAME, "senha").is_displayed())
            pw_field = driver.find_element(By.NAME, "senha")
            pw_field.send_keys(PASSWD, Keys.ENTER)

        except TimeoutException:
            print("TimeoutException: Element not found")
            return None
    try:
        WebDriverWait(driver, 10).until(
            lambda s: s.find_element(By.XPATH, "/html/body/app-root/app-core/main/app-treino/section/button").is_displayed())
        wo_btn = driver.find_element(
            By.XPATH, "/html/body/app-root/app-core/main/app-treino/section/button")
        ActionChains(driver).click(wo_btn).perform()
        WebDriverWait(driver, 10).until(
            lambda s: s.find_element(By.XPATH, "/html/body/app-root/app-core/main/app-treino/section/app-menu-treino/div/div/ul/li[{}]".format(no_workout)).is_displayed())
        wo_select = driver.find_element(
            By.XPATH, "/html/body/app-root/app-core/main/app-treino/section/app-menu-treino/div/div/ul/li[{}]".format(no_workout))
        ActionChains(driver).click(wo_select).perform()
    except TimeoutException:
        driver.close()
        return None

    return driver


def get_exercises(driver, no_workout):
    soup = BeautifulSoup(driver.page_source, "lxml")
    workout_data = []
    print("--------------------------------------------")
    print("Workout {}\n".format(no_workout))
    for workout in soup.select("div.exercicios"):
        for card in workout.select("div.card-container"):
            biset = False
            row = 1         
            for card_status in card.find_all(attrs={"class":"card-status"}):
                try:
                    nextrow = card.select_one("div#card-row-{}".format(row+1)) #If there's a second exercise, then its a set.
                    if nextrow and row == 1:
                        workout_data.append((no_workout,"Set"))
                        biset = True
                    name_exerc = card.select_one("div#card-row-{}".format(row)).text
                    if biset:
                        name_exerc = '    ' + name_exerc
                    series = card_status.select_one("div#series p.color-transition").text
                    load = card_status.next_element.text
                    load_re = re.search('ries (.+?) carga', load) #format the string of the load
                    if load_re:
                        load = load_re.group(1)
                    else:
                        load = "N/A"
                    repetitions = card_status.select_one("div.col1.box-repeticao").text
                    workout_data.append((no_workout,name_exerc,series,load,repetitions))
                    row += 1
                except:
                    print("\n")
    #Print the final result in terminal  
    for data in workout_data:
        if data[1] != ("Set"):
            print("{}, S: {}, C: {}, R: {}".format(data[1],data[2],data[3],data[4])) 
        else:
            print("Set")


    return workout_data

driver = configure_driver()
no_workout = 1
workouts = []
while (True):
    driver = get_workout(driver, no_workout)
    if not driver:
        break
    exercises_data = get_exercises(driver, no_workout)
    no_workout += 1
    for exercise in exercises_data:
        workouts.append(exercise)
header = ('Training','Exercise','Series','Load','Repetitions')
with open('workouts.csv', 'w') as csvfile:
    writer = csv.writer(csvfile, delimiter=",")
    writer.writerow(header)
    writer.writerows(workouts)
    print("\nExported to 'workouts.csv'")



