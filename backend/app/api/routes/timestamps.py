from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def get_timestamps():
    
    return {
        "status": "success",
        "timestamps": [
            {"time": 5, "label": "Introduction"},
            {"time": 15, "label": "Skills Discussion"},
            {"time": 30, "label": "Experience"},
        ]
    }