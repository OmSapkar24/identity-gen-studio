import os
import random
from typing import Optional, Callable, Dict, Any

import torch
from PIL import Image


class VideoPipeline:
    """AnimateDiff video generation pipeline with identity conditioning."""

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = None
        self._loaded = False

    def _load_models(self, checkpoint: str, motion_adapter_id: str):
        if self._loaded:
            return
        from diffusers import AnimateDiffPipeline, MotionAdapter, DDIMScheduler
        adapter = MotionAdapter.from_pretrained(
            motion_adapter_id,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        )
        self.pipe = AnimateDiffPipeline.from_pretrained(
            checkpoint,
            motion_adapter=adapter,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        ).to(self.device)
        self.pipe.scheduler = DDIMScheduler.from_pretrained(
            checkpoint, subfolder="scheduler",
            clip_sample=False, timestep_spacing="linspace",
            beta_schedule="linear", steps_offset=1,
        )
        if self.device == "cuda":
            self.pipe.enable_vae_slicing()
            self.pipe.enable_model_cpu_offload()
        self._loaded = True

    def generate(
        self,
        reference_path: Optional[str],
        output_path: str,
        params: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
    ) -> str:
        from diffusers.utils import export_to_video
        checkpoint = params.get("model_checkpoint", "runwayml/stable-diffusion-v1-5")
        motion_adapter = params.get("motion_adapter", "guoyww/animatediff-motion-adapter-v1-5-2")
        self._load_models(checkpoint, motion_adapter)

        seed = params.get("seed", random.randint(0, 2**32 - 1))
        generator = torch.Generator(device=self.device).manual_seed(seed)
        steps = params.get("steps", 25)
        cfg = params.get("cfg_scale", 7.5)
        num_frames = params.get("num_frames", 16)
        fps = params.get("fps", 8)
        width = params.get("width", 512)
        height = params.get("height", 512)
        prompt = params.get("prompt", "")
        negative_prompt = params.get("negative_prompt", "bad quality, worse quality")
        enhanced_prompt = f"{prompt}, high quality, masterpiece, best quality"

        def step_cb(pipe, step, timestep, cb_kwargs):
            if progress_callback:
                progress_callback(step, steps)
            return cb_kwargs

        with torch.inference_mode():
            result = self.pipe(
                prompt=enhanced_prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=steps,
                guidance_scale=cfg,
                num_frames=num_frames,
                width=width,
                height=height,
                generator=generator,
                callback_on_step_end=step_cb,
            )

        export_to_video(result.frames[0], output_path, fps=fps)
        print(f"[VideoPipeline] Saved to {output_path}")
        return output_path

    def unload(self):
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        self._loaded = False
