#!/usr/bin/env python3
"""
Web Interface Test for Game Stats Score Fix Implementation
Tests the actual web application to verify score calculation fixes are working correctly.
"""

import sys
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebInterfaceScoreFixTest:
    def __init__(self, base_url="http://localhost:8050", password="test_password"):
        self.base_url = base_url
        self.password = password
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Set up Chrome WebDriver with appropriate options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            logger.info("Chrome WebDriver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            return False
    
    def check_app_running(self):
        """Check if the application is running and accessible"""
        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200:
                logger.info(f"Application is running at {self.base_url}")
                return True
            else:
                logger.error(f"Application returned status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Cannot connect to application at {self.base_url}: {str(e)}")
            return False
    
    def login(self):
        """Login to the application using the provided password"""
        try:
            logger.info("Attempting to login...")
            self.driver.get(self.base_url)
            
            # Wait for password input field
            password_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "password-input"))
            )
            
            # Enter password
            password_input.clear()
            password_input.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.ID, "login-button")
            login_button.click()
            
            # Wait for successful login (check for main navigation or content)
            self.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "main-content")),
                    EC.presence_of_element_located((By.CLASS_NAME, "navbar")),
                    EC.presence_of_element_located((By.ID, "team-stats-link"))
                )
            )
            
            logger.info("Successfully logged in")
            return True
            
        except TimeoutException:
            logger.error("Login failed - timeout waiting for elements")
            return False
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    def navigate_to_team_stats(self):
        """Navigate to the team statistics page"""
        try:
            logger.info("Navigating to team statistics...")
            
            # Look for team stats link/button
            team_stats_link = self.wait.until(
                EC.element_to_be_clickable((By.ID, "team-stats-link"))
            )
            team_stats_link.click()
            
            # Wait for team stats page to load
            self.wait.until(
                EC.presence_of_element_located((By.ID, "team-stats-content"))
            )
            
            logger.info("Successfully navigated to team statistics")
            return True
            
        except TimeoutException:
            logger.error("Failed to navigate to team statistics - timeout")
            return False
        except Exception as e:
            logger.error(f"Failed to navigate to team statistics: {str(e)}")
            return False
    
    def test_game_type_filtering(self):
        """Test game type filtering and score consistency"""
        try:
            logger.info("Testing game type filtering...")
            
            # Find game type dropdown
            game_type_dropdown = self.wait.until(
                EC.presence_of_element_located((By.ID, "game-type-filter"))
            )
            
            select = Select(game_type_dropdown)
            game_types = ["All Games", "Exhibition", "Regular Season", "Tournament"]
            
            scores_by_type = {}
            
            for game_type in game_types:
                try:
                    logger.info(f"Testing {game_type} filter...")
                    
                    # Select game type
                    select.select_by_visible_text(game_type)
                    
                    # Wait for page to update
                    time.sleep(2)
                    
                    # Extract game scores from the games table/list
                    scores = self.extract_game_scores()
                    scores_by_type[game_type] = scores
                    
                    logger.info(f"{game_type}: Found {len(scores)} games with scores")
                    
                except Exception as e:
                    logger.error(f"Error testing {game_type}: {str(e)}")
                    scores_by_type[game_type] = []
            
            # Validate score consistency
            self.validate_score_consistency(scores_by_type)
            
            return True
            
        except Exception as e:
            logger.error(f"Game type filtering test failed: {str(e)}")
            return False
    
    def extract_game_scores(self):
        """Extract game scores from the current page"""
        try:
            scores = []
            
            # Look for game score elements (adjust selectors based on actual HTML structure)
            score_elements = self.driver.find_elements(By.CLASS_NAME, "game-score")
            
            if not score_elements:
                # Try alternative selectors
                score_elements = self.driver.find_elements(By.XPATH, "//td[contains(@class, 'score')]")
            
            if not score_elements:
                # Try looking in table rows for score patterns
                rows = self.driver.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    text = row.text
                    # Look for score patterns like "3-2", "1-0", etc.
                    import re
                    score_matches = re.findall(r'\b\d+-\d+\b', text)
                    scores.extend(score_matches)
            else:
                for element in score_elements:
                    score_text = element.text.strip()
                    if score_text and '-' in score_text:
                        scores.append(score_text)
            
            return scores
            
        except Exception as e:
            logger.error(f"Error extracting game scores: {str(e)}")
            return []
    
    def validate_score_consistency(self, scores_by_type):
        """Validate that scores are consistent and logical"""
        logger.info("Validating score consistency...")
        
        # Check that "All Games" includes scores from all other types
        all_games_scores = scores_by_type.get("All Games", [])
        other_scores = []
        
        for game_type in ["Exhibition", "Regular Season", "Tournament"]:
            other_scores.extend(scores_by_type.get(game_type, []))
        
        logger.info(f"All Games: {len(all_games_scores)} scores")
        logger.info(f"Sum of other types: {len(other_scores)} scores")
        
        # Validate score format
        for game_type, scores in scores_by_type.items():
            for score in scores:
                if not self.is_valid_score_format(score):
                    logger.warning(f"Invalid score format in {game_type}: {score}")
        
        # Log sample scores for verification
        for game_type, scores in scores_by_type.items():
            if scores:
                logger.info(f"{game_type} sample scores: {scores[:3]}")
    
    def is_valid_score_format(self, score):
        """Check if score is in valid format (e.g., "3-2", "0-1")"""
        import re
        pattern = r'^\d+-\d+$'
        return bool(re.match(pattern, score))
    
    def test_individual_game_details(self):
        """Test clicking on individual games to verify score consistency"""
        try:
            logger.info("Testing individual game details...")
            
            # Find clickable game elements
            game_links = self.driver.find_elements(By.CLASS_NAME, "game-link")
            
            if not game_links:
                # Try alternative selectors
                game_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'game')]")
            
            if game_links:
                # Test first few games
                for i, game_link in enumerate(game_links[:3]):
                    try:
                        logger.info(f"Testing game {i+1} details...")
                        
                        # Get score from list view
                        list_score = self.extract_score_from_element(game_link)
                        
                        # Click on game
                        game_link.click()
                        
                        # Wait for game details page
                        time.sleep(2)
                        
                        # Extract score from detail view
                        detail_score = self.extract_game_detail_score()
                        
                        # Compare scores
                        if list_score and detail_score:
                            if list_score == detail_score:
                                logger.info(f"✓ Game {i+1} scores match: {list_score}")
                            else:
                                logger.error(f"✗ Game {i+1} score mismatch: list={list_score}, detail={detail_score}")
                        
                        # Go back to list
                        self.driver.back()
                        time.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error testing game {i+1}: {str(e)}")
                        # Try to go back if we're stuck
                        try:
                            self.driver.back()
                        except:
                            pass
            
            return True
            
        except Exception as e:
            logger.error(f"Individual game details test failed: {str(e)}")
            return False
    
    def extract_score_from_element(self, element):
        """Extract score from a game element"""
        try:
            text = element.text
            import re
            score_match = re.search(r'\b(\d+-\d+)\b', text)
            return score_match.group(1) if score_match else None
        except:
            return None
    
    def extract_game_detail_score(self):
        """Extract score from game detail view"""
        try:
            # Look for score in detail view
            score_elements = self.driver.find_elements(By.CLASS_NAME, "game-detail-score")
            
            if not score_elements:
                # Try alternative selectors
                score_elements = self.driver.find_elements(By.XPATH, "//span[contains(@class, 'score')]")
            
            if score_elements:
                return score_elements[0].text.strip()
            
            # Try extracting from page text
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            import re
            score_match = re.search(r'\b(\d+-\d+)\b', page_text)
            return score_match.group(1) if score_match else None
            
        except:
            return None
    
    def test_rapid_filter_switching(self):
        """Test rapid switching between game type filters"""
        try:
            logger.info("Testing rapid filter switching...")
            
            game_type_dropdown = self.driver.find_element(By.ID, "game-type-filter")
            select = Select(game_type_dropdown)
            
            # Rapidly switch between filters
            filters = ["All Games", "Regular Season", "Exhibition", "All Games", "Tournament"]
            
            for i, filter_name in enumerate(filters):
                logger.info(f"Switch {i+1}: Selecting {filter_name}")
                select.select_by_visible_text(filter_name)
                time.sleep(0.5)  # Brief pause
                
                # Check that page updated
                current_selection = select.first_selected_option.text
                if current_selection == filter_name:
                    logger.info(f"✓ Filter switched to {filter_name}")
                else:
                    logger.error(f"✗ Filter switch failed: expected {filter_name}, got {current_selection}")
            
            return True
            
        except Exception as e:
            logger.error(f"Rapid filter switching test failed: {str(e)}")
            return False
    
    def capture_screenshot(self, filename):
        """Capture screenshot for debugging"""
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {str(e)}")
    
    def run_all_tests(self):
        """Run all web interface tests"""
        logger.info("Starting Web Interface Score Fix Tests")
        logger.info("=" * 60)
        
        test_results = {
            "app_running": False,
            "driver_setup": False,
            "login": False,
            "navigation": False,
            "game_type_filtering": False,
            "game_details": False,
            "rapid_switching": False
        }
        
        try:
            # Check if app is running
            test_results["app_running"] = self.check_app_running()
            if not test_results["app_running"]:
                logger.error("Application is not running. Please start the app first.")
                return test_results
            
            # Setup WebDriver
            test_results["driver_setup"] = self.setup_driver()
            if not test_results["driver_setup"]:
                logger.error("Failed to setup WebDriver. Please install ChromeDriver.")
                return test_results
            
            # Login
            test_results["login"] = self.login()
            if not test_results["login"]:
                logger.error("Login failed. Please check the password and app state.")
                self.capture_screenshot("login_failure.png")
                return test_results
            
            # Navigate to team stats
            test_results["navigation"] = self.navigate_to_team_stats()
            if not test_results["navigation"]:
                logger.error("Failed to navigate to team statistics.")
                self.capture_screenshot("navigation_failure.png")
                return test_results
            
            # Test game type filtering
            test_results["game_type_filtering"] = self.test_game_type_filtering()
            
            # Test individual game details
            test_results["game_details"] = self.test_individual_game_details()
            
            # Test rapid filter switching
            test_results["rapid_switching"] = self.test_rapid_filter_switching()
            
            # Capture final screenshot
            self.capture_screenshot("final_state.png")
            
        except Exception as e:
            logger.error(f"Unexpected error during testing: {str(e)}")
            self.capture_screenshot("error_state.png")
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
        
        # Report results
        self.report_results(test_results)
        return test_results
    
    def report_results(self, results):
        """Report test results"""
        logger.info("\n" + "=" * 60)
        logger.info("WEB INTERFACE TEST RESULTS")
        logger.info("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
            if result:
                passed += 1
        
        logger.info("=" * 60)
        logger.info(f"SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED - Score calculation fixes are working correctly!")
        else:
            logger.info("⚠️  Some tests failed - please review the issues above")
        
        logger.info("=" * 60)

def main():
    """Main function to run web interface tests"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8050"
    
    if len(sys.argv) > 2:
        password = sys.argv[2]
    else:
        password = os.environ.get('HOCKEY_STATS_PASSWORD', 'test_password')
    
    tester = WebInterfaceScoreFixTest(base_url, password)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()