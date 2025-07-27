# mypy: disable - error - code = "no-untyped-def,misc"
import asyncio
import logging
import os
import csv
import json
from typing import Dict, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.services.vector_store import VectorStoreService
from langchain.document_loaders import PyPDFLoader
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the FastAPI app
app = FastAPI()
 
# Initialize vector store service
vector_store_service = VectorStoreService()

class UploadResponse(BaseModel):
    success: bool
    files_processed: List[str]
    error: str = None

class EscalationLogResponse(BaseModel):
    success: bool
    data: List[Dict[str, str]]
    total_records: int
 

@app.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    category: str = Form(...)
) -> UploadResponse:
    """Upload documents to the vector store with category"""
    try:
        if not vector_store_service:
            raise HTTPException(
                status_code=500,
                detail="Vector store service not initialized"
            )

        processed_files = []
        
        for file in files:
            # Check if file is PDF
            if not file.filename.lower().endswith('.pdf'):
                continue  # Skip non-PDF files
                
            # Create temporary file
            temp_file = None
            try:
                # Read file content
                contents = await file.read()
                
                # Create temporary file asynchronously
                def create_temp_file():
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                    temp_file.write(contents)
                    temp_file.flush()
                    temp_file.close()  # Close the file handle
                    return temp_file.name
                
                temp_file_path = await asyncio.to_thread(create_temp_file)
                
                # Load PDF using PyPDFLoader asynchronously
                def load_pdf():
                    loader = PyPDFLoader(temp_file_path)
                    return loader.load()
                
                documents = await asyncio.to_thread(load_pdf)
                
                # Add to vector store with specified category
                await vector_store_service.add_documents(documents=documents, category=category)
                processed_files.append(file.filename)
                
                print(f"Successfully processed '{file.filename}' -> Category: '{category}'")
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                raise e
            finally:
                # Cleanup temp file with retry logic asynchronously
                if temp_file_path and await asyncio.to_thread(os.path.exists, temp_file_path):
                    try:
                        await asyncio.to_thread(os.unlink, temp_file_path)
                    except OSError as e:
                        logger.warning(f"Could not delete temp file {temp_file_path}: {e}")
                        # On Windows, sometimes files need time to be released
                        await asyncio.sleep(0.1)
                        try:
                            await asyncio.to_thread(os.unlink, temp_file_path)
                        except OSError:
                            pass  # Give up if still can't delete
        
        if not processed_files:
            return UploadResponse(
                success=False,
                files_processed=[],
                error="No PDF files were processed"
            )
        
        return UploadResponse(
            success=True,
            files_processed=processed_files
        )
        
    except Exception as e:
        logger.error(f"Error in upload_documents: {str(e)}")
        return UploadResponse(
            success=False,
            files_processed=[],
            error=str(e)
        )

@app.get("/escalation-log", response_model=EscalationLogResponse)
async def get_escalation_log() -> EscalationLogResponse:
    """Get escalation log data from CSV file"""
    try:
        csv_file_path = "data/escalation_log.csv"
        
        if not os.path.exists(csv_file_path):
            raise HTTPException(
                status_code=404,
                detail="Escalation log file not found"
            )
        
        data = []
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                data.append(row)
        
        return EscalationLogResponse(
            success=True,
            data=data,
            total_records=len(data)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading escalation log: {str(e)}"
        )

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "vector_store_initialized": str(vector_store_service is not None)
    }
