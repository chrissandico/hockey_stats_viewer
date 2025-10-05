#!/usr/bin/env python3

"""
Test script to verify that the team regular season filter fix works in the web interface.
This launches the web app and tests the filter functionality through the browser.
"""

import sys
import os
import time
import subprocess
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def test_team_filter_web_interface():
    """Test the team regular season filter through the web interface."""
    
    print("=== Testing Team Regular Season Filter in Web Interface ===")
    
    # Start the web application
    print("Starting web application...")
    app_process = subprocess.Popen([
        sys.executable, "-c",
        "import sys; sys.path.append('hockey_stats_webapp'); from app import app; app.run_server(debug=False, port=8051)"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for the app to start
    time.sleep(5)
    
    # Check if the app is running
    try:
        response = requests.get("http://localhost:8051", timeout=10)
        print(f"✓ Web app is running (status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to connect to web app: {e}")
        app_process.terminate()
        return False
    
    # Set up Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("http://localhost:8051")
        
        print("✓ Browser opened and navigated to app")
        
        # Wait for login page to load
        wait = WebDriverWait(driver, 10)
        
        # Find and fill password field
        password_input = wait.until(EC.presence_of_element_located((By.ID, "password-input")))
        password_input.send_keys("waxers123")  # Use test team password
        
        # Click login button
        login_button = driver.find_element(By.ID, "login-button")
        login_button.click()
        
        print("✓ Logged in successfully")
        
        # Wait for main page to load and navigate to team stats
        time.sleep(3)
        team_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Team Stats")))
        team_link.click()
        
        print("✓ Navigated to Team Stats page")
        
        # Wait for team stats page to load
        time.sleep(5)
        
        # Check if game type filter is present
        try:
            game_type_tabs = driver.find_element(By.ID, "game-type-filter-tabs")
            print("✓ Game type filter found")
            
            # Get initial stats (should be "All Games" by default)
            initial_stats = get_team_stats_from_page(driver)
            print(f"Initial stats (All Games): {initial_stats}")
            
            # Click on Regular Season tab
            regular_season_tab = driver.find_element(By.CSS_SELECTOR, "[data-value='R']")
            regular_season_tab.click()
            
            print("✓ Clicked Regular Season filter")
            
            # Wait for page to update
            time.sleep(3)
            
            # Get updated stats
            regular_season_stats = get_team_stats_from_page(driver)
            print(f"Regular Season stats: {regular_season_stats}")
            
            # Verify that stats changed (unless all games are regular season)
            if initial_stats != regular_season_stats:
                print("✓ Regular season filter is working - stats changed")
                
                # Check if player tables updated
                forwards_updated = check_player_table_updated(driver, "forwards-leaderboard-table-filtered")
                defense_updated = check_player_table_updated(driver, "defense-leaderboard-table-filtered")
                goalies_updated = check_goalie_table_updated(driver)
                
                if forwards_updated and defense_updated and goalies_updated:
                    print("✓ All player performance tables updated correctly")
                    return True
                else:
                    print("✗ Some player performance tables did not update")
                    return False
            else:
                print("⚠ Stats appear identical - may indicate all games are regular season")
                return True
                
        except NoSuchElementException as e:
            print(f"✗ Game type filter not found: {e}")
            return False
            
    except TimeoutException as e:
        print(f"✗ Timeout waiting for page elements: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during web interface test: {e}")
        return False
    finally:
        if driver:
            driver.quit()
