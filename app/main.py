from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from app.core.config import settings
from app.core.database import connect_to_db
from app.core.scheduler import scheduler, setup_scheduled_tasks
from app.routes import portfolio, market, scrape_table, screener, app_logs
import logging

load_dotenv()

# Configure logging
logging.basicConfig(
    filename="app_logs.txt",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
logging.getLogger("logger.py").setLevel(logging.ERROR)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Manage your stock portfolio",
    version="1.0.0",
    contact={
        "name": "Mohd Khalid Siddiqui",
        "email": "khalidsiddiqui9550@gmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    docs_url=settings.DOCS_URL,
)

# Configure middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CLIENT_URL.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio Management"])
app.include_router(market.router, prefix="/market", tags=["Market"])
app.include_router(scrape_table.router, prefix="/scrape", tags=["Scrape Table"])
app.include_router(screener.router, prefix="/screener", tags=["Charlink Screener"])
app.include_router(app_logs.router, prefix="/app_logs", tags=["App Logs"])

# Setup scheduled tasks
setup_scheduled_tasks(scheduler)


@app.on_event("startup")
async def startup_event():
    logging.info("Starting the scheduler")
    await connect_to_db()
    scheduler.start()


@app.on_event("shutdown")
def shutdown_event():
    logging.info("Shutting down the scheduler")
    scheduler.shutdown()


@app.get("/")
async def root():
    return {"message": "Welcome to the Stock Portfolio App"}


@app.get("/testdb")
async def testdb():
    result = await connect_to_db()
    return JSONResponse(content=result)