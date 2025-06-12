import scrapy
import logging
from scrapy.shell import inspect_response  # Useful for debugging

class TexasHOASpider(scrapy.Spider):
    name = 'texas_hoa_scraper'
    start_urls = ['https://www.texas-homeowners-associations.com/texas_hoa_p_list.php?mastertable=texashoacounty&masterkey1=Collin']
    logging.getLogger('scrapy').setLevel(logging.WARNING)  # Suppress excessive Scrapy logs

    def parse(self, response):
        """
        Parses the initial page listing Collin County HOAs and extracts the links to individual HOA pages.
        """
        for row in response.xpath('//table[@class="hoatable"]/tr[position() > 1]'):
            hoa_name = row.xpath('./td[1]/a/text()').get()
            relative_url = row.xpath('./td[1]/a/@href').get()
            if relative_url:
                absolute_url = response.urljoin(relative_url)
                yield scrapy.Request(absolute_url, callback=self.parse_hoa_details, meta={'hoa_name': hoa_name})

    def parse_hoa_details(self, response):
        """
        Parses individual HOA pages to extract address and website information.
        Handles potential variations in page structure.
        """
        hoa_name = response.meta['hoa_name']
        logging.info(f'Scraping details for: {hoa_name} from {response.url}')

        # 1. Attempt to extract address using a more robust XPath
        address = response.xpath('//div[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "address")]/following-sibling::div/text()').get()
        if not address:
            address = response.xpath('//strong[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "address")]/following-sibling::text()').get()
        if not address:
            address = response.xpath('//div[@class="field-item even"]/p/text()').get()
        if not address:
            address = response.xpath('//div[@class="field-item odd"]/p/text()').get()
        if not address:
            address = response.xpath('//div[@class="field-label"]/following-sibling::div/text()').get()
        if not address:
             address = response.xpath('//span[@class="office-address"]/text()').get()
        if not address:
            address = "Address Not Found"
            logging.warning(f'Address not found for {hoa_name} on {response.url}')

        # 2. Attempt to extract website URL
        website_link = response.xpath('//a[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "website")]/@href').get()
        if not website_link:
            website_link = response.xpath('//a[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "web site")]/@href').get()
        if not website_link:
            website_link = response.xpath('//a[contains(@rel, "noopener")]/@href').get()
        if not website_link:
            website_link = "Website Not Found"
            logging.warning(f'Website not found for {hoa_name} on {response.url}')

        yield {
            'HOA Name': hoa_name,
            'Address': address.strip() if address else "Address Not Found",
            'Website': website_link.strip() if website_link else "Website Not Found",
            'Source URL': response.url,  # Include the source URL for reference
        }

    def closed(self, reason):
        if reason == 'finished':
            logging.info("Scraping completed successfully.")
        else:
            logging.warning(f"Scraping was stopped due to: {reason}")
