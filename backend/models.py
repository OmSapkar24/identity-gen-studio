from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ImageJobRequest(BaseModel):
    reference_id: str = Field(..., description="Reference face image ID from /upload/reference")
    prompt: str = Field(..., description="Text prompt for image generation")
    negative_prompt: str = Field(default="", description="Negative prompt")
    seed: int = Field(default=-1, description="Random seed (-1 for random)")
    cfg_scale: float = Field(default=7.5, ge=1.0, le=20.0, description="Classifier-free guidance scale")
    steps: int = Field(default=30, ge=10, le=100, description="Denoising steps")
    width: int = Field(default=1024, description="Output image width")
    height: int = Field(default=1024, description="Output image height")
    sampler: str = Field(default="DPM++ 2M Karras", description="Scheduler/sampler name")
    identity_strength: float = Field(default=0.8, ge=0.0, le=1.0, description="Identity conditioning strength")
    model_checkpoint: str = Field(default="stabilityai/stable-diffusion-xl-base-1.0", description="Base model")
    identity_method: str = Field(default="instantid", description="Identity method: instantid or ip-adapter")


class VideoJobRequest(BaseModel):
    reference_id: str = Field(..., description="Reference face image ID")
    prompt: str = Field(..., description="Text prompt for video generation")
    negative_prompt: str = Field(default="", description="Negative prompt")
    seed: int = Field(default=-1)
    cfg_scale: float = Field(default=7.5, ge=1.0, le=20.0)
    steps: int = Field(default=25, ge=10, le=50)
    motion_bucket_id: int = Field(default=127, ge=1, le=255, description="AnimateDiff motion bucket")
    num_frames: int = Field(default=16, ge=8, le=32, description="Number of video frames")
    fps: int = Field(default=8, ge=4, le=24, description="Output frames per second")
    width: int = Field(default=512)
    height: int = Field(default=512)
    identity_strength: float = Field(default=0.75, ge=0.0, le=1.0)
    motion_adapter: str = Field(default="guoyww/animatediff-motion-adapter-v1-5-2", description="Motion adapter model")
    model_checkpoint: str = Field(default="runwayml/stable-diffusion-v1-5")


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # queued | processing | completed | failed
    progress: int = 0
    output_url: Optional[str] = None
    comet_experiment_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ExperimentInfo(BaseModel):
    experiment_id: str
    experiment_name: str
    mode: str  # image | video
    prompt: str
    seed: int
    cfg_scale: float
    status: str
    comet_url: Optional[str] = None
    output_preview_url: Optional[str] = None
    created_at: str
    tags: List[str] = []


class ExperimentsResponse(BaseModel):
    experiments: List[ExperimentInfo]
    total: int


class PresetRequest(BaseModel):
    name: str = Field(..., description="Preset name")
    parameters: Dict[str, Any] = Field(..., description="Parameter values to save")


class PresetResponse(BaseModel):
    preset_id: str
    name: str
    parameters: Dict[str, Any]


class PromoteModelRequest(BaseModel):
    model_name: str = Field(..., description="Comet registry model name")
    version: str = Field(..., description="Model version to promote")
    stage: str = Field(default="production", description="Target stage: staging | production")
