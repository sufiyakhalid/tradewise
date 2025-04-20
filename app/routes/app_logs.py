from fastapi import APIRouter
from fastapi.responses import JSONResponse
import re
from datetime import datetime
import pytz

router = APIRouter()

log_file_path = "app_logs.txt"

kolkata_timezone = pytz.timezone("Asia/Kolkata")

def parse_log_line(line: str, exclude=[]):
    log_pattern = r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (?P<level>\w+) - (?P<filename>\S+) - (?P<function>\S+) - (?P<message>.*)'
    
    match = re.match(log_pattern, line)
    if match:
        utc_time = datetime.strptime(match.group("timestamp"), "%Y-%m-%d %H:%M:%S,%f")
        local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(kolkata_timezone)
        if match.group("filename") in exclude:
            return None
        return {
            "timestamp": local_time.strftime("%Y-%m-%d %H:%M:%S,%f"),  
            "level": match.group("level"),
            "filename": match.group("filename"),
            "function": match.group("function"),
            "message": match.group("message")
        }
    return None

# Endpoint to fetch logs from file and return them as JSON
@router.get("/logs")
async def get_logs():
    logs = []
    
    # Read the log file and parse each line
    try:
        with open(log_file_path, "r") as file:
            for line in file:
                log_entry = parse_log_line(line, ["base.py", "models.py", "logger.py"])
                if log_entry:
                    logs.append(log_entry)
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"error": "Log file not found."})
    
    # Sort logs in descending order of timestamp
    sorted_logs = sorted(
        logs,
        key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S,%f"),
        reverse=True
    )
    
    # Return the sorted logs as a JSON response
    return JSONResponse(content=sorted_logs)
