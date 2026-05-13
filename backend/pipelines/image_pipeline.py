import os
import random
from typing import Optional, Callable, Dict, Any

import torch
import numpy as np
from PIL import Image


class ImagePipeline:
    """
    Identity-preserving image generation pipeline.
    Supports InstantID and IP-Adapter methods with SDXL base.
    """

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = None
        self.face_analyzer = None
        self._loaded = False

    def _load_models(self, checkpoint: str, identity_method: str):
        if self._loaded:
            return
        print(f"[ImagePipeline] Loading models on {self.device}...")
        if identity_method == "instantid":
            self._load_instantid(checkpoint)
        else:
            self._load_ip_adapter(checkpoint)
        self._loaded = True

    def _load_instantid(self, checkpoint: str):
        from diffusers import StableDiffusionXLPipeline
        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            checkpoint,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            use_safetensors=True,
        ).to(self.device)
        try:
            from insightface.app import FaceAnalysis
            self.face_analyzer = FaceAnalysis(
                name="buffalo_l",
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
            )
            self.face_analyzer.prepare(ctx_id=0 if self.device == "cuda" else -1, det_size=(640, 640))
        except ImportError:
            print("[ImagePipeline] InsightFace not available.")
            self.face_analyzer = None

    def _load_ip_adapter(self, checkpoint: str):
        from diffusers import StableDiffusionXLPipeline
        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            checkpoint,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        ).to(self.device)
        self.pipe.load_ip_adapter(
            "h94/IP-Adapter",
            subfolder="sdxl_models",
            weight_name="ip-adapter_sdxl.bin",
        )

    def _extract_face_embedding(self, image_path: str):
        if self.face_analyzer is None:
            return None, None
        img = np.array(Image.open(image_path).convert("RGB"))
        faces = self.face_analyzer.get(img)
        if not faces:
            return None, None
        face = max(faces, key=lambda x: x.det_score)
        return face.embedding, face.kps

    def _get_scheduler(self, scheduler_name: str):
        from diffusers import (
            DPMSolverMultistepScheduler, DDIMScheduler,
            EulerAncestralDiscreteScheduler,
        )
        schedulers = {
            "DPM++ 2M Karras": DPMSolverMultistepScheduler,
            "DDIM": DDIMScheduler,
            "Euler a": EulerAncestralDiscreteScheduler,
        }
        sched_class = schedulers.get(scheduler_name, DPMSolverMultistepScheduler)
        return sched_class.from_config(self.pipe.scheduler.config)

    def generate(
        self,
        reference_path: Optional[str],
        output_path: str,
        params: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> str:
        checkpoint = params.get("model_checkpoint", "stabilityai/stable-diffusion-xl-base-1.0")
        identity_method = params.get("identity_method", "instantid")
        self._load_models(checkpoint, identity_method)

        sampler = params.get("sampler", "DPM++ 2M Karras")
        self.pipe.scheduler = self._get_scheduler(sampler)

        seed = params.get("seed", random.randint(0, 2**32 - 1))
        generator = torch.Generator(device=self.device).manual_seed(seed)

        steps = params.get("steps", 30)
        cfg = params.get("cfg_scale", 7.5)
        width = params.get("width", 1024)
        height = params.get("height", 1024)
        prompt = params.get("prompt", "")
        negative_prompt = params.get("negative_prompt", "")
        identity_strength = params.get("identity_strength", 0.8)

        def step_callback(pipe, step, timestep, callback_kwargs):
            if progress_callback:
                progress_callback(step, steps)
            return callback_kwargs

        with torch.inference_mode():
            if identity_method == "ip_adapter" and reference_path:
                ref_image = Image.open(reference_path).convert("RGB")
                self.pipe.set_ip_adapter_scale(identity_strength)
                result = self.pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    ip_adapter_image=ref_image,
                    num_inference_steps=steps,
                    guidance_scale=cfg,
                    width=width,
                    height=height,
                    generator=generator,
                    callback_on_step_end=step_callback,
                )
            else:
                result = self.pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    num_inference_steps=steps,
                    guidance_scale=cfg,
                    width=width,
                    height=height,
                    generator=generator,
                    callback_on_step_end=step_callback,
                )

        result.images[0].save(output_path)
        print(f"[ImagePipeline] Saved to {output_path}")
        return output_path

    def unload(self):
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        self._loaded = False
