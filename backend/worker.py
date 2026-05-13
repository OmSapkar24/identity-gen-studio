import os
import time
import random
from pathlib import Path
from typing import Dict, Any

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "identity_gen_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
)

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@celery_app.task(bind=True, name="worker.run_image_job")
def run_image_job(self, job_id: str, params: Dict[str, Any]):
    """
    Celery task for running an image generation job.
    Uses InstantID + SDXL pipeline.
    """
    from comet_tracker import CometTracker
    from pipelines.image_pipeline import ImagePipeline

    comet = CometTracker()
    experiment = comet.start_image_experiment(job_id, params)

    try:
        self.update_state(state="STARTED", meta={"progress": 5})

        # Resolve seed
        seed = params.get("seed", -1)
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        params["seed"] = seed

        self.update_state(state="STARTED", meta={"progress": 10})

        # Log reference image
        reference_path = Path("./references") / f"{params['reference_id']}.*"
        ref_files = list(Path("./references").glob(f"{params['reference_id']}.*"))
        if ref_files and experiment:
            comet.log_reference_image(experiment, str(ref_files[0]))

        self.update_state(state="STARTED", meta={"progress": 20})

        # Run pipeline
        pipeline = ImagePipeline()
        output_path = OUTPUT_DIR / f"{job_id}.png"

        def progress_callback(step, total):
            pct = int(20 + (step / total) * 70)
            self.update_state(state="STARTED", meta={"progress": pct})

        pipeline.generate(
            reference_path=str(ref_files[0]) if ref_files else None,
            output_path=str(output_path),
            params=params,
            progress_callback=progress_callback,
        )

        # Log output
        if output_path.exists() and experiment:
            comet.log_output_image(experiment, str(output_path))
            comet.log_metric(experiment, "generation_seed", seed)

        self.update_state(state="STARTED", meta={"progress": 95})
        comet.end_experiment(experiment)

        return {
            "job_id": job_id,
            "output_url": f"/outputs/{job_id}.png",
            "comet_url": experiment.url if experiment else None,
            "metadata": {"seed": seed, "mode": "image"},
        }

    except Exception as e:
        comet.end_experiment(experiment)
        raise e


@celery_app.task(bind=True, name="worker.run_video_job")
def run_video_job(self, job_id: str, params: Dict[str, Any]):
    """
    Celery task for running a video generation job.
    Uses AnimateDiff pipeline with identity conditioning.
    """
    from comet_tracker import CometTracker
    from pipelines.video_pipeline import VideoPipeline

    comet = CometTracker()
    experiment = comet.start_video_experiment(job_id, params)

    try:
        self.update_state(state="STARTED", meta={"progress": 5})

        seed = params.get("seed", -1)
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        params["seed"] = seed

        self.update_state(state="STARTED", meta={"progress": 10})

        ref_files = list(Path("./references").glob(f"{params['reference_id']}.*"))
        if ref_files and experiment:
            comet.log_reference_image(experiment, str(ref_files[0]))

        self.update_state(state="STARTED", meta={"progress": 20})

        pipeline = VideoPipeline()
        output_path = OUTPUT_DIR / f"{job_id}.mp4"

        def progress_callback(step, total):
            pct = int(20 + (step / total) * 70)
            self.update_state(state="STARTED", meta={"progress": pct})

        pipeline.generate(
            reference_path=str(ref_files[0]) if ref_files else None,
            output_path=str(output_path),
            params=params,
            progress_callback=progress_callback,
        )

        if output_path.exists() and experiment:
            comet.log_output_video(experiment, str(output_path))
            comet.log_metric(experiment, "generation_seed", seed)
            comet.log_metric(experiment, "num_frames", params.get("num_frames", 16))

        self.update_state(state="STARTED", meta={"progress": 95})
        comet.end_experiment(experiment)

        return {
            "job_id": job_id,
            "output_url": f"/outputs/{job_id}.mp4",
            "comet_url": experiment.url if experiment else None,
            "metadata": {"seed": seed, "mode": "video"},
        }

    except Exception as e:
        comet.end_experiment(experiment)
        raise e
