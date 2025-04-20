from fastapi import APIRouter, HTTPException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from pydantic import BaseModel
import logging

router = APIRouter()


class ScrapingRequest(BaseModel):
    url: str
    table_id: str


def scrape_table_to_json(url: str, table_id: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.binary_location = "/usr/bin/chromium"

    # service = Service("/usr/bin/chromedriver")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        driver.implicitly_wait(10)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        table = soup.find("table", id=table_id)
        if not table:
            raise HTTPException(
                status_code=404,
                detail=f"Table with ID '{table_id}' not found on the page.",
            )

        headers = []
        header_row = table.find("thead").find_all("th")
        for header in header_row:
            headers.append(header.text.strip())

        table_data = []
        rows = table.find("tbody").find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            row_data = {}
            for i, cell in enumerate(cells):
                row_data[headers[i]] = cell.text.strip()
            table_data.append(row_data)

        if not table_data or (
            len(table_data) == 1
            and table_data[0].get("Sr.") == "No stocks filtered in the Scan"
        ):
            logging.warning("No valid stock data available to process.")
            return []
        return table_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        driver.quit()


@router.post("/table")
async def scrape_table(request: ScrapingRequest):
    try:
        table_data = scrape_table_to_json(request.url, request.table_id)
        return {"data": table_data}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to scrape table data: {str(e)}"
        )
