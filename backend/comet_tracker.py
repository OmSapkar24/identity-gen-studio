import os
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    import comet_ml
    from comet_ml import Experiment, API
    COMET_AVAILABLE = True
except ImportError:
    COMET_AVAILABLE = False
    print("[CometTracker] comet_ml not installed. Tracking disabled.")


class CometTracker:
    """
    Wrapper around Comet ML for experiment tracking, artifact logging,
    and model registry management for identity-gen-studio.
    """

    def __init__(self):
        self.api_key = os.getenv("COMET_API_KEY")
        self.project_name = os.getenv("COMET_PROJECT_NAME", "identity-gen-studio")
        self.workspace = os.getenv("COMET_WORKSPACE")
        self.enabled = COMET_AVAILABLE and bool(self.api_key)
        self._api = None

        if self.enabled:
            print(f"[CometTracker] Initialized for project: {self.project_name}")
        else:
            print("[CometTracker] Running in offline mode (no tracking).")

    @property
    def api(self):
        if self._api is None and self.enabled:
            self._api = API(api_key=self.api_key)
        return self._api

    def start_image_experiment(self, job_id: str, params: Dict[str, Any]) -> Optional[Any]:
        """Start a Comet experiment for an image generation job."""
        if not self.enabled:
            return None

        experiment = Experiment(
            api_key=self.api_key,
            project_name=self.project_name,
            workspace=self.workspace,
        )
        experiment.set_name(f"image-{job_id[:8]}")
        experiment.add_tag("image")
        experiment.add_tag(params.get("identity_method", "instantid"))

        # Log hyperparameters
        experiment.log_parameters({
            "job_id": job_id,
            "mode": "image",
            "prompt": params.get("prompt", ""),
            "negative_prompt": params.get("negative_prompt", ""),
            "seed": params.get("seed", -1),
            "cfg_scale": params.get("cfg_scale", 7.5),
            "steps": params.get("steps", 30),
            "width": params.get("width", 1024),
            "height": params.get("height", 1024),
            "sampler": params.get("sampler", "DPM++ 2M Karras"),
            "identity_strength": params.get("identity_strength", 0.8),
            "model_checkpoint": params.get("model_checkpoint", ""),
            "identity_method": params.get("identity_method", "instantid"),
        })

        return experiment

    def start_video_experiment(self, job_id: str, params: Dict[str, Any]) -> Optional[Any]:
        """Start a Comet experiment for a video generation job."""
        if not self.enabled:
            return None

        experiment = Experiment(
            api_key=self.api_key,
            project_name=self.project_name,
            workspace=self.workspace,
        )
        experiment.set_name(f"video-{job_id[:8]}")
        experiment.add_tag("video")
        experiment.add_tag("animatediff")

        experiment.log_parameters({
            "job_id": job_id,
            "mode": "video",
            "prompt": params.get("prompt", ""),
            "negative_prompt": params.get("negative_prompt", ""),
            "seed": params.get("seed", -1),
            "cfg_scale": params.get("cfg_scale", 7.5),
            "steps": params.get("steps", 25),
            "motion_bucket_id": params.get("motion_bucket_id", 127),
            "num_frames": params.get("num_frames", 16),
            "fps": params.get("fps", 8),
            "width": params.get("width", 512),
            "height": params.get("height", 512),
            "identity_strength": params.get("identity_strength", 0.75),
            "motion_adapter": params.get("motion_adapter", ""),
            "model_checkpoint": params.get("model_checkpoint", ""),
        })

        return experiment

    def log_reference_image(self, experiment, image_path: str):
        """Log the reference face image as an artifact."""
        if experiment is None:
            return
        experiment.log_image(image_path, name="reference_face")

    def log_output_image(self, experiment, image_path: str, step: int = 0):
        """Log the generated output image."""
        if experiment is None:
            return
        experiment.log_image(image_path, name="generated_output", step=step)

    def log_output_video(self, experiment, video_path: str):
        """Log the generated output video as an artifact."""
        if experiment is None:
            return
        experiment.log_asset(video_path, file_name="generated_video.mp4")

    def log_metric(self, experiment, name: str, value: float, step: int = 0):
        """Log a scalar metric."""
        if experiment is None:
            return
        experiment.log_metric(name, value, step=step)

    def log_likeness_score(self, experiment, score: float):
        """Log facial likeness score (0-1)."""
        if experiment is None:
            return
        experiment.log_metric("likeness_score", score)
        if score >= 0.8:
            experiment.add_tag("best-likeness")
        elif score < 0.5:
            experiment.add_tag("low-likeness")

    def end_experiment(self, experiment):
        """End and upload the experiment."""
        if experiment is None:
            return
        experiment.end()

    def list_experiments(
        self,
        limit: int = 20,
        mode: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List experiments from Comet ML project."""
        if not self.enabled or self.api is None:
            return self._mock_experiments(limit)

        try:
            project = self.api.get(self.workspace, self.project_name)
            experiments_raw = project.get_experiments()

            results = []
            for exp in experiments_raw[:limit]:
                params = exp.get_parameters_summary() or {}
                tags = exp.get_tags() or []

                if mode and mode not in tags:
                    continue
                if tag and tag not in tags:
                    continue

                results.append({
                    "experiment_id": exp.id,
                    "experiment_name": exp.name or "",
                    "mode": "video" if "video" in tags else "image",
                    "prompt": next((p["valueCurrent"] for p in params if p["name"] == "prompt"), ""),
                    "seed": int(next((p["valueCurrent"] for p in params if p["name"] == "seed"), -1)),
                    "cfg_scale": float(next((p["valueCurrent"] for p in params if p["name"] == "cfg_scale"), 7.5)),
                    "status": "completed",
                    "comet_url": exp.url,
                    "output_preview_url": None,
                    "created_at": str(exp.start_server_timestamp),
                    "tags": tags,
                })
            return results
        except Exception as e:
            print(f"[CometTracker] Error listing experiments: {e}")
            return []

    def register_model(self, experiment, model_name: str, checkpoint_path: str):
        """Register a model version in Comet Model Registry."""
        if experiment is None:
            return
        experiment.log_model(model_name, checkpoint_path)

    def promote_model(
        self,
        model_name: str,
        version: str,
        stage: str = "production"
    ) -> Dict[str, Any]:
        """Promote a model version to a given stage in Comet Registry."""
        if not self.enabled or self.api is None:
            return {"status": "skipped", "reason": "Comet not enabled"}

        try:
            model = self.api.get_model(workspace=self.workspace, model_name=model_name)
            model.set_status(version=version, status=stage)
            return {"status": "success", "model": model_name, "version": version, "stage": stage}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _mock_experiments(self, limit: int) -> List[Dict[str, Any]]:
        """Return mock experiments when Comet is not configured."""
        modes = ["image", "video"]
        prompts = [
            "a portrait of a person in cyberpunk city, neon lights",
            "professional headshot, studio lighting, sharp focus",
            "fantasy warrior, detailed armor, epic lighting",
        ]
        results = []
        for i in range(min(limit, 3)):
            results.append({
                "experiment_id": f"mock-exp-{i+1:03d}",
                "experiment_name": f"{'image' if i % 2 == 0 else 'video'}-demo-{i+1:03d}",
                "mode": modes[i % 2],
                "prompt": prompts[i % len(prompts)],
                "seed": 42 + i,
                "cfg_scale": 7.5,
                "status": "completed",
                "comet_url": None,
                "output_preview_url": None,
                "created_at": datetime.utcnow().isoformat(),
                "tags": [modes[i % 2], "demo"],
            })
        return results
