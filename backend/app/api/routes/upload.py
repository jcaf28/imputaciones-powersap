# PATH: backend/app/api/routes/upload.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from app.services import file_processor

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
  if not file.filename.endswith('.xlsx'):
    raise HTTPException(status_code=400, detail="Invalid file type. Only .xlsx allowed")
  contents = await file.read()
  try:
    new_filename = file_processor.process_file(file.filename, contents)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  return FileResponse(
    new_filename,
    media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    filename=new_filename
  )
