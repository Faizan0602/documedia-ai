from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.file_service import FileService

router = APIRouter()

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    try:
        result = await FileService.save_upload_file(file)

        return {
            "status": "success",
            "message": "File uploaded successfully",
            "data": result
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))