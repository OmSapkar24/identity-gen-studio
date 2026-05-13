import os
import uuid
import asyncio
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from celery.result import AsyncResult

from models import (
    ImageJobRequest, VideoJobRequest,
    JobResponse, JobStatusResponse,
    PresetRequest, PresetResponse,
    ExperimentsResponse, PromoteModelRequest
)
from worker import celery_app, run_image_job, run_video_job
from comet_tracker import CometTracker

app = FastAPI(
    title="Identity Gen Studio API",
    description="Identity-preserving image & video generation with Comet ML tracking",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REFERENCE_DIR = Path("./references")
REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")
comet = CometTracker()


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/upload/reference", tags=["Upload"])
async def upload_reference_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    save_path = REFERENCE_DIR / f"{file_id}.{ext}"
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)
    return {"reference_id": file_id, "path": str(save_path)}


@app.post("/jobs/image", response_model=JobResponse, tags=["Jobs"])
async def submit_image_job(request: ImageJobRequest):
    job_id = str(uuid.uuid4())
    run_image_job.apply_async(args=[job_id, request.dict()], task_id=job_id)
    return JobResponse(job_id=job_id, status="queued", message="Image generation job queued")


@app.post("/jobs/video", response_model=JobResponse, tags=["Jobs"])
async def submit_video_job(request: VideoJobRequest):
    job_id = str(uuid.uuid4())
    run_video_job.apply_async(args=[job_id, request.dict()], task_id=job_id)
    return JobResponse(job_id=job_id, status="queued", message="Video generation job queued")


@app.get("/jobs/{job_id}", response_model=JobStatusResponse, tags=["Jobs"])
async def get_job_status(job_id: str):
    result = AsyncResult(job_id, app=celery_app)
    if result.state == "PENDING":
        return JobStatusResponse(job_id=job_id, status="queued", progress=0)
    elif result.state == "STARTED":
        info = result.info or {}
        return JobStatusResponse(job_id=job_id, status="processing", progress=info.get("progress", 10))
    elif result.state == "SUCCESS":
        data = result.result
        return JobStatusResponse(
            job_id=job_id, status="completed", progress=100,
            output_url=data.get("output_url"),
            comet_experiment_url=data.get("comet_url"),
            metadata=data.get("metadata")
        )
    elif result.state == "FAILURE":
        return JobStatusResponse(job_id=job_id, status="failed", progress=0, error=str(result.result))
    return JobStatusResponse(job_id=job_id, status=result.state.lower(), progress=50)


@app.get("/jobs/{job_id}/artifact", tags=["Jobs"])
async def download_artifact(job_id: str):
    for ext in ["png", "jpg", "mp4", "gif"]:
        candidate = OUTPUT_DIR / f"{job_id}.{ext}"
        if candidate.exists():
            return FileResponse(str(candidate), filename=f"identity-gen-{job_id}.{ext}")
    raise HTTPException(status_code=404, detail="Artifact not found")


@app.get("/experiments", response_model=ExperimentsResponse, tags=["Experiments"])
async def list_experiments(limit: int = 20, mode: Optional[str] = None, tag: Optional[str] = None):
    experiments = comet.list_experiments(limit=limit, mode=mode, tag=tag)
    return ExperimentsResponse(experiments=experiments, total=len(experiments))


@app.post("/presets", response_model=PresetResponse, tags=["Presets"])
async def save_preset(request: PresetRequest):
    preset_id = str(uuid.uuid4())
    return PresetResponse(preset_id=preset_id, name=request.name, parameters=request.parameters)


@app.post("/models/promote", tags=["Models"])
async def promote_model(request: PromoteModelRequest):
    result = comet.promote_model(model_name=request.model_name, version=request.version, stage=request.stage)
    return {"success": True, "message": f"Model {request.model_name} v{request.version} promoted to {request.stage}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
