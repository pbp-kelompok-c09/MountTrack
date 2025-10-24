import time
import json
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

class DataGunungScraper:
    def __init__(self, headless=True):
        self.base_url = "https://datagunung.com"
        self.gunung_url = f"{self.base_url}/gunung"
        self.mountains = []
        self.headless = headless
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    
    def scroll_and_load_all(self, driver):
        """Scroll down to trigger lazy loading until all content is loaded"""
        print("Loading all mountains (this may take a minute)...")
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        no_change_count = 0
        scroll_pause = 2  # seconds to wait after each scroll
        
        while True:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for page to load
            time.sleep(scroll_pause)
            
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            # Count mountains currently loaded
            mountains = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/gunung/"][href*="/info"]')
            print(f"  Loaded {len(mountains)} mountains so far...", end='\r')
            
            if new_height == last_height:
                no_change_count += 1
                if no_change_count >= 3:  # If no change after 3 attempts, we're done
                    print(f"\n✓ Finished loading. Total: {len(mountains)} mountains")
                    break
            else:
                no_change_count = 0
            
            last_height = new_height
    
    def extract_mountains_from_html(self, html_content):
        """Extract mountain data from the HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all mountain links - the href contains /gunung/[name]/info
        mountain_links = soup.find_all('a', href=lambda x: x and '/gunung/' in x and '/info' in x)
        
        print(f"Found {len(mountain_links)} mountain links in HTML")
        
        mountains_data = []
        processed_names = set()
        
        for link in mountain_links:
            try:
                url = link.get('href')
                if not url:
                    continue
                
                full_url = self.base_url + url if url.startswith('/') else url
                
                # Extract mountain name from URL
                url_match = re.search(r'/gunung/([^/]+)/info', url)
                if not url_match:
                    continue
                    
                name = url_match.group(1).replace('%20', ' ')
                
                # Skip duplicates
                if name in processed_names:
                    continue
                processed_names.add(name)
                
                # Find the parent div that contains all mountain info
                # Structure: multiple parent divs up to find the one with all data
                parent = link
                for _ in range(10):  # Go up max 10 levels
                    parent = parent.find_parent('div')
                    if not parent:
                        break
                    # Check if this parent has both name and height info
                    if parent.find('span', string=lambda x: x and 'm.' in str(x)):
                        break
                
                if not parent:
                    continue
                
                # Extract name from the bold span with text-indigo-800 class
                name_span = parent.find('span', class_=lambda x: x and 'text-indigo-800' in str(x) and 'font-bold' in str(x))
                if name_span:
                    name_text = name_span.get_text(strip=True)
                    if name_text:
                        name = name_text
                
                # Extract height from span with "m." text
                height = None
                all_spans = parent.find_all('span')
                for span in all_spans:
                    text = span.get_text(strip=True)
                    if 'm.' in text:
                        height_match = re.search(r'(\d+)\s*m\.?', text)
                        if height_match:
                            height = int(height_match.group(1))
                            break
                
                # Extract province from div with text-indigo-700 class
                province = 'Unknown'
                province_div = parent.find('div', class_=lambda x: x and 'text-indigo-700' in str(x))
                if province_div:
                    province = province_div.get_text(strip=True)
                
                # Extract image URL from img tag
                img = link.find('img')
                image_url = None
                if img:
                    image_url = img.get('src')
                    if image_url and image_url.startswith('/'):
                        image_url = self.base_url + image_url
                
                mountain_data = {
                    'name': name,
                    'url': full_url,
                    'height_mdpl': height,
                    'province': province,
                    'image_url': image_url
                }
                
                mountains_data.append(mountain_data)
                
            except Exception as e:
                print(f"\nError parsing link: {e}")
                continue
        
        print(f"Successfully extracted {len(mountains_data)} mountains")
        return mountains_data
    
    def scrape_mountain_detail(self, driver, mountain_data):
        """Scrape additional details from individual mountain page"""
        print(f"  Getting details for: {mountain_data['name']}")
        
        try:
            driver.get(mountain_data['url'])
            time.sleep(2)  # Wait for page to load
            
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract description
            paragraphs = soup.find_all('p')
            description_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 50:
                    description_parts.append(text)
            
            if description_parts:
                mountain_data['description'] = ' '.join(description_parts[:3])
            
            # Find Google Maps link
            maps_link = soup.find('a', href=lambda x: x and 'google.com/maps' in x)
            if maps_link:
                mountain_data['maps_link'] = maps_link.get('href')
            
            # Try to extract coordinates
            page_text = soup.get_text()
            coord_pattern = r'(-?\d+\.\d+),\s*(-?\d+\.\d+)'
            coord_match = re.search(coord_pattern, page_text)
            if coord_match:
                mountain_data['latitude'] = float(coord_match.group(1))
                mountain_data['longitude'] = float(coord_match.group(2))
            
        except Exception as e:
            print(f"    Error: {e}")
        
        return mountain_data
    
    def scrape_all_mountains(self, include_details=True):
        """Main scraping function with lazy loading support"""
        print("=" * 60)
        print("Starting DataGunung Scraper with Lazy Loading Support")
        print("=" * 60)
        
        driver = None
        try:
            # Setup Selenium driver
            print("\nInitializing browser...")
            driver = self.setup_driver()
            
            # Load the page
            print(f"Opening {self.gunung_url}...")
            driver.get(self.gunung_url)
            time.sleep(3)  # Initial wait for page load
            
            # Scroll and load all mountains
            self.scroll_and_load_all(driver)
            
            # Get the final HTML
            html_content = driver.page_source
            
            # Save HTML for debugging
            with open('debug_full_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("✓ Saved full page HTML to debug_full_page.html\n")
            
            # Extract mountain data
            print("Extracting mountain data...")
            mountains_data = self.extract_mountains_from_html(html_content)
            print(f"✓ Extracted data for {len(mountains_data)} mountains\n")
            
            # Get detailed info if requested
            if include_details and mountains_data:
                print("Fetching detailed information...")
                print("=" * 60)
                for i, mountain in enumerate(mountains_data, 1):
                    print(f"[{i}/{len(mountains_data)}]", end=" ")
                    try:
                        updated_data = self.scrape_mountain_detail(driver, mountain)
                        mountains_data[i-1] = updated_data
                        time.sleep(1)  # Be polite
                    except Exception as e:
                        print(f"  Error: {e}")
            
            self.mountains = mountains_data
            return mountains_data
            
        except Exception as e:
            print(f"\n✗ Error during scraping: {e}")
            return []
        
        finally:
            if driver:
                driver.quit()
                print("\n✓ Browser closed")
    
    def save_to_csv(self, filename='gunung_data.csv'):
        """Save scraped data to CSV"""
        if not self.mountains:
            print("No data to save")
            return None
        
        df = pd.DataFrame(self.mountains)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✓ Data saved to {filename}")
        return df
    
    def save_to_json(self, filename='gunung_data.json'):
        """Save scraped data to JSON"""
        if not self.mountains:
            print("No data to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.mountains, f, ensure_ascii=False, indent=2)
        print(f"✓ Data saved to {filename}")
    
    def print_summary(self):
        """Print summary of scraped data"""
        if not self.mountains:
            print("No data available")
            return
        
        print("\n" + "=" * 60)
        print("SCRAPING SUMMARY")
        print("=" * 60)
        print(f"Total mountains scraped: {len(self.mountains)}")
        
        # Group by province
        provinces = {}
        for m in self.mountains:
            prov = m.get('province', 'Unknown')
            provinces[prov] = provinces.get(prov, 0) + 1
        
        print(f"\nMountains by province:")
        for prov, count in sorted(provinces.items(), key=lambda x: x[1], reverse=True):
            print(f"  {prov}: {count}")
        
        # Highest mountains
        print(f"\nTop 10 highest mountains:")
        sorted_mountains = sorted(
            [m for m in self.mountains if m.get('height_mdpl')],
            key=lambda x: x.get('height_mdpl', 0),
            reverse=True
        )
        for i, m in enumerate(sorted_mountains[:10], 1):
            height = m.get('height_mdpl', 'N/A')
            print(f"  {i:2d}. {m['name']:30s} - {height:4d} mdpl ({m.get('province', 'N/A')})")


def main():
    print("=" * 60)
    print("DATAGUNUNG.COM SCRAPER (with Lazy Loading)")
    print("=" * 60)
    print("\nThis scraper uses Selenium to handle lazy loading.")
    print("Make sure you have Chrome installed!\n")
    
    # Ask user preferences
    print("Options:")
    print("1. Quick scrape (main page only - faster)")
    print("2. Detailed scrape (includes individual pages - slower)")
    choice = input("\nChoose option (1 or 2, default=1): ").strip() or "1"
    include_details = choice == "2"
    
    print("\nShow browser window while scraping?")
    headless_choice = input("(y=show browser, n=hidden, default=hidden): ").strip().lower()
    headless = headless_choice != 'y'
    
    # Create scraper and run
    scraper = DataGunungScraper(headless=headless)
    mountains = scraper.scrape_all_mountains(include_details=include_details)
    
    if mountains:
        # Save results
        print("\n" + "=" * 60)
        print("SAVING RESULTS")
        print("=" * 60)
        df = scraper.save_to_csv('gunung_data.csv')
        scraper.save_to_json('gunung_data.json')
        
        # Print summary
        scraper.print_summary()
        
        # Display sample
        print("\n" + "=" * 60)
        print("SAMPLE DATA (First 3 mountains)")
        print("=" * 60)
        for mountain in mountains[:3]:
            print(f"\n{mountain['name']}:")
            for key, value in mountain.items():
                if key == 'description':
                    desc = value[:150] + "..." if value and len(value) > 150 else value
                    print(f"  {key}: {desc}")
                elif key != 'name':
                    print(f"  {key}: {value}")
    else:
        print("\n✗ No data was scraped")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()