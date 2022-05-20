import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common import by
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException
import random
caps = DesiredCapabilities.CHROME
caps['goog:loggingPrefs'] = {'performance': 'ALL'}
PATH = os.getcwd() + "/chromedriver"
#HELPER FUNCTIONS
#helper function, wait for page to load
def helper_wait(driver,t):
    time.sleep(t)

#helper function, logs into the MonolithTester account
def helper_login(driver):
    driver.get('https://monolith-ee461l.herokuapp.com/login/Welcome') #open the driver
    driver.maximize_window()

    textbox_username = driver.find_element(by.By.ID,"uname") #create username and input to reenter password box
    textbox_username.send_keys("MonolithTester")

    textbox_username = driver.find_element(by.By.ID,"password") #create username and input to reenter password box
    textbox_username.send_keys("MonolithTester")

    button = driver.find_element(by.By.ID,"submit1") #submit form
    button.click()

    helper_wait(driver,1) #wait for new page to load



#TEST FUNCTIONS
#Test a bad attempt to create a new user account
def testBadNewUser():
    driver = webdriver.Chrome(executable_path=PATH, desired_capabilities=caps)

    driver.get('https://monolith-ee461l.herokuapp.com/login/Welcome') #open the driver
    driver.maximize_window()
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)") #scroll to bottom of page 

    textbox_username = driver.find_element(by.By.ID,"new_uname") #create username and input to reenter password box
    textbox_username.send_keys("MonolithTester")

    textbox_username = driver.find_element(by.By.ID,"rpassword")
    textbox_username.send_keys("MonolithTester")


    button = driver.find_element(by.By.ID,"submit2") #submit form
    button.click()

    helper_wait(driver,2) #wait for new page to load
    url = driver.current_url
    assert url == "https://monolith-ee461l.herokuapp.com/login/Username%20or%20Password%20entered%20incorrectly" #should have redirected back to login page, with incorrect 
                                                                                                                 #password mentioned
    
    driver.close()

#precondition: the MonolithTester user is NOT in the database. 
#test a good user account creation attempt
def testGoodNewUser():
    driver = webdriver.Chrome(executable_path=PATH, desired_capabilities=caps)

    driver.get('https://monolith-ee461l.herokuapp.com/login/Welcome') #open the driver
    driver.maximize_window()
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)") #scroll to bottom of page 

    textbox_username = driver.find_element(by.By.ID,"new_uname") #create username and input to reenter password box
    textbox_username.send_keys("MonolithTester")

    textbox_username = driver.find_element(by.By.ID,"new_password") #create username and input to reenter password box
    textbox_username.send_keys("MonolithTester")

    textbox_username = driver.find_element(by.By.ID,"rpassword")
    textbox_username.send_keys("MonolithTester")


    button = driver.find_element(by.By.ID,"submit2") #submit form
    button.click()

    helper_wait(driver,2) #wait for new page to load
    url = driver.current_url
    assert url == "https://monolith-ee461l.herokuapp.com/home/MonolithTester" #should have redirected to home page
    
    #TEST JWTs
    driver.get("https://monolith-ee461l.herokuapp.com/home/MonolithTester") #reload the page to ensure json web tokens do not redirect you.
    # helper_wait(driver,2)
    url = driver.current_url
    assert url == "https://monolith-ee461l.herokuapp.com/home/MonolithTester" #this browser now has a json web token, so this should not redirect to the login page
    

    #test logout attempt and make sure you lose json web token
    driver.find_element(by.By.XPATH,"//a[contains(text(),'Logout')] ").click()
    helper_wait(driver,2) #wait for new page to load
    url = driver.current_url
    assert "https://monolith-ee461l.herokuapp.com/login/" in url #should have redirected back to login page

    #try to go to home page after losing JWT
    driver.get("https://monolith-ee461l.herokuapp.com/home/MonolithTester") #reload the page to ensure json web tokens do not redirect you.
    helper_wait(driver,2) #wait to go back to login 
    url = driver.current_url
    assert "https://monolith-ee461l.herokuapp.com/login/" in url #you should not be able to go to home page


    driver.close()




#precondition: testGoodNewUser was run prior to this test
#tests a good login attempt
def testGoodLogin():
    driver = webdriver.Chrome(executable_path=PATH, desired_capabilities=caps)
    
    driver.get('https://monolith-ee461l.herokuapp.com/login/Welcome') #open the driver
    driver.maximize_window()

    helper_login(driver)

    url = driver.current_url
    assert url == "https://monolith-ee461l.herokuapp.com/home/MonolithTester" #should have redirected back to login page

    driver.close()

def testDestroyAccount():
    driver = webdriver.Chrome(executable_path=PATH, desired_capabilities=caps)

    driver.get('https://monolith-ee461l.herokuapp.com/login/Welcome') #open the driver
    driver.maximize_window()

    helper_login(driver)

    #go to account page
    driver.find_element(by.By.XPATH,"//a[text()='Account']").click()
    helper_wait(driver,3)

    #delete account
    driver.find_element(by.By.XPATH,"//a[contains(text(),'Delete Account')] ").click()
    helper_wait(driver,3)

    url = driver.current_url
    assert "https://monolith-ee461l.herokuapp.com/login/" in url #should have redirected back to login page

    driver.close()

# #Tests for Project
# def testCreateProjectFromUser():
#     driver = webdriver.Chrome(executable_path=PATH, desired_capabilities=caps)

#     driver.get('https://monolith-ee461l.herokuapp.com/login/Welcome') #open the driver
#     driver.maximize_window()

#     helper_login(driver)

#     driver.get('https://monolith-ee461l.herokuapp.com/projects/MonolithTester/View%20or%20create%20projects')
#     helper_wait(driver,2) #wait for page to change

#     textbox_projectname = driver.find_element(by.By.ID, "project_name")
#     textbox_projectname.send_keys("ProjectTest" + str(random.randint(0,234234)))

#     textbox_projectid = driver.find_element(by.By.ID, "project_ID")
#     textbox_projectid.send_keys("115")

#     textbox_projectdesc = driver.find_element(by.By.ID, "project_description")
#     textbox_projectdesc.send_keys("Description")

#     button = driver.find_element(by.By.ID, "submitnew")
#     button.click()

#     helper_wait(driver,2) #page should reload with new project.
#     url = driver.current_url
#     assert url == "https://monolith-ee461l.herokuapp.com/projects/MonolithTester/Project%20added" #redirect to projects
    
#     driver.close()

# def testValidProjectID():
#     driver = webdriver.Chrome(executable_path=PATH, desired_capabilities=caps)
#     driver.get('https://monolith-ee461l.herokuapp.com/projects/MonolithTester')
#     driver.maximize_window()

#     textbox_projectdesc = driver.find_element(by.By.ID, "goToProject_ID")
#     textbox_projectdesc.send_keys("115")

#     button = driver.find_element(by.By.ID, "submitexist")
#     button.click()

#     helper_wait(driver,2) #wait for new page to load
#     url = driver.current_url
#     assert url == "https://monolith-ee461l.herokuapp.com/projects/MonolithTester/115/hwsets" #should have redirected to home page

# def testInvalidProjectID():
#     driver = webdriver.Chrome(executable_path=PATH, desired_capabilities=caps)
#     driver.get('https://monolith-ee461l.herokuapp.com/projects/MonolithTester')
#     driver.maximize_window()

#     textbox_projectdesc = driver.find_element(by.By.ID, "goToProject_ID")
#     textbox_projectdesc.send_keys("DNE")

#     button = driver.find_element(by.By.ID, "submitexist")
#     button.click()

#     helper_wait(driver,2) #wait for new page to load 
#     url = driver.current_url
#     assert url == "https://monolith-ee461l.herokuapp.com/projects/MonolithTester/No project with given project ID found%2C please try again" #should have redirected to home page

#     driver.close()

# #HWSETS
# def testAddHardwareSet1ToProject():
#     driver = webdriver.Chrome(executable_path=PATH, desired_capabilities=caps)
#     driver.get('https://monolith-ee461l.herokuapp.com/projects/MonolithTester/SL/hwsets')
#     driver.maximize_window()

#     button = driver.find_element(by.By.ID, "submitexist") #Need to figure out ID naming for for loops.
#     button.click()
#     # TODO



#Run these tests first to create the MonolithTester Account
testBadNewUser()
testGoodNewUser()
testGoodLogin()

###Run tests of website performance###

#Project
# testCreateProjectFromUser()
# testValidProjectID()
# testInvalidProjectID()

#Run this test last to delete MonolithTester
testDestroyAccount()