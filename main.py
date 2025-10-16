import config
from ue_scraper import UeScraper


def main():
    scraper = UeScraper(config.EMAIL_ADDRESS, config.PASSWORD)
    try:
        scraper.sign_in()
        scraper.navigate_to_driver_dashboard()
        results = scraper.get_weekly_results()
        scraper.save_results(results)
    except Exception as e:
        print(e)
    finally:
        scraper.quit()

##### メイン処理 #####
if __name__ == '__main__':
    main()

