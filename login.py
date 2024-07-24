from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def login_to_twitter(username, password, otp=None):
    # Set up the WebDriver
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    try:
        # Navigate to Twitter login page
        driver.get("https://twitter.com/login")

        # Allow the page to load
        time.sleep(5)

        # Find the username field and enter the username
        username_field = driver.find_element(By.CSS_SELECTOR, "input[name='text']")
        username_field.send_keys(username)

        # Debug: Print the username field value
        print("Entered username:", username_field.get_attribute("value"))

        # Find the next button and click it
        next_button_xpath = "//button[@role='button' and contains(@class, 'css-175oi2r') and contains(., 'Next')]"
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, next_button_xpath))
        )
        next_button.click()

        # Debug: Print a message after clicking the next button
        print("Clicked the next button")

        time.sleep(2)  # wait for 2 seconds

        # Wait for the password input field to appear
        password_field_xpath = "//input[@name='password']"
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, password_field_xpath))
        )

        # Enter the password
        password_field.send_keys(password)

        # Debug: Print the password field value (for debugging, avoid in production)
        print("Entered password:", password_field.get_attribute("value"))

        # Submit the form
        password_field.send_keys(Keys.RETURN)

        # Wait for the 2FA verification page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='text']"))
        )

        if otp:
            # Enter the OTP code
            otp_field = driver.find_element(By.CSS_SELECTOR, "input[name='text']")
            otp_field.send_keys(otp)

            # Find the next button and click it
            otp_next_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='ocfEnterTextNextButton']")
            otp_next_button.click()

            # Debug: Print a message after clicking the OTP next button
            print("Clicked the OTP next button")

        # Wait for a bit to ensure the login process completes
        time.sleep(5)

        # Debug: Print a message after login attempt
        print("Login attempt finished")

        # Get cookies
        cookies = driver.get_cookies()
        return cookies

    finally:
        # Close the browser
        driver.quit()
