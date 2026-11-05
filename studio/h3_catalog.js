/* Dolorain Studio's bundled H3 node catalog. Display metadata is not an execution registry. */
window.dolorainH3Catalog=[
  {
    "type": "UNETLoader",
    "display_name": "UNETLoader",
    "category": "ComfyUI / Core",
    "description": "H3 workflow node · UNETLoader",
    "inputs": [],
    "outputs": [
      {
        "name": "MODEL",
        "type": "MODEL"
      }
    ],
    "source": "comfy-core"
  },
  {
    "type": "VAELoader",
    "display_name": "VAELoader",
    "category": "Video / VAE",
    "description": "H3 workflow node · VAELoader",
    "inputs": [],
    "outputs": [
      {
        "name": "VAE",
        "type": "VAE"
      }
    ],
    "source": "comfy-core"
  },
  {
    "type": "LoadImage",
    "display_name": "LoadImage",
    "category": "ComfyUI / Core",
    "description": "H3 workflow node · LoadImage",
    "inputs": [],
    "outputs": [
      {
        "name": "IMAGE",
        "type": "IMAGE"
      },
      {
        "name": "MASK",
        "type": "MASK"
      }
    ],
    "source": "comfy-core"
  },
  {
    "type": "PixaromaLoadVideo",
    "display_name": "PixaromaLoadVideo",
    "category": "Video / VAE",
    "description": "H3 workflow node · PixaromaLoadVideo",
    "inputs": [],
    "outputs": [
      {
        "name": "video_frames",
        "type": "IMAGE"
      },
      {
        "name": "audio",
        "type": "AUDIO"
      },
      {
        "name": "frame_count",
        "type": "INT"
      },
      {
        "name": "fps",
        "type": "FLOAT"
      },
      {
        "name": "width",
        "type": "INT"
      },
      {
        "name": "height",
        "type": "INT"
      },
      {
        "name": "duration",
        "type": "FLOAT"
      }
    ],
    "source": "comfyui-pixaroma"
  },
  {
    "type": "MiniMaxH3ReferenceToVideo",
    "display_name": "MiniMaxH3ReferenceToVideo",
    "category": "Dolorain / H3",
    "description": "H3 workflow node · MiniMaxH3ReferenceToVideo",
    "inputs": [
      {
        "name": "clip",
        "type": "CLIP"
      },
      {
        "name": "vae",
        "type": "VAE"
      },
      {
        "name": "audio_vae",
        "type": "VAE"
      },
      {
        "name": "ref_images.ref_image_0",
        "type": "IMAGE"
      },
      {
        "name": "ref_images.ref_image_1",
        "type": "IMAGE"
      },
      {
        "name": "ref_images.ref_image_2",
        "type": "IMAGE"
      },
      {
        "name": "ref_images.ref_image_3",
        "type": "IMAGE"
      },
      {
        "name": "ref_images.ref_image_4",
        "type": "IMAGE"
      },
      {
        "name": "ref_videos.ref_video_0",
        "type": "IMAGE"
      },
      {
        "name": "ref_videos.ref_video_1",
        "type": "IMAGE"
      },
      {
        "name": "ref_videos.ref_video_2",
        "type": "IMAGE"
      },
      {
        "name": "ref_video_audios.ref_video_audio_0",
        "type": "AUDIO"
      },
      {
        "name": "ref_video_audios.ref_video_audio_1",
        "type": "AUDIO"
      },
      {
        "name": "ref_video_audios.ref_video_audio_2",
        "type": "AUDIO"
      },
      {
        "name": "ref_audios.ref_audio_0",
        "type": "AUDIO"
      },
      {
        "name": "ref_audios.ref_audio_1",
        "type": "AUDIO"
      },
      {
        "name": "ref_audios.ref_audio_2",
        "type": "AUDIO"
      },
      {
        "name": "prompt",
        "type": "STRING"
      },
      {
        "name": "width",
        "type": "INT"
      },
      {
        "name": "height",
        "type": "INT"
      },
      {
        "name": "length",
        "type": "INT"
      }
    ],
    "outputs": [
      {
        "name": "positive",
        "type": "CONDITIONING"
      },
      {
        "name": "LATENT",
        "type": "LATENT"
      }
    ],
    "source": "comfy-core"
  },
  {
    "type": "LoadLoraModel",
    "display_name": "LoadLoraModel",
    "category": "ComfyUI / Core",
    "description": "H3 workflow node · LoadLoraModel",
    "inputs": [
      {
        "name": "model",
        "type": "MODEL"
      },
      {
        "name": "loras.0.lora_name",
        "type": "COMBO"
      },
      {
        "name": "loras.0.strength",
        "type": "FLOAT"
      },
      {
        "name": "loras.0.enabled",
        "type": "BOOLEAN"
      }
    ],
    "outputs": [
      {
        "name": "MODEL",
        "type": "MODEL"
      }
    ],
    "source": "comfy-core"
  },
  {
    "type": "H3VideoController",
    "display_name": "H3VideoController",
    "category": "Dolorain / H3",
    "description": "H3 workflow node · H3VideoController",
    "inputs": [],
    "outputs": [
      {
        "name": "latent",
        "type": "LATENT"
      },
      {
        "name": "video_info",
        "type": "VHS_VIDEOINFO"
      },
      {
        "name": "frame_count",
        "type": "INT"
      },
      {
        "name": "fps",
        "type": "FLOAT"
      },
      {
        "name": "actual_duration_seconds",
        "type": "FLOAT"
      },
      {
        "name": "width",
        "type": "INT"
      },
      {
        "name": "height",
        "type": "INT"
      },
      {
        "name": "summary",
        "type": "STRING"
      }
    ],
    "source": "h3-video-controller"
  },
  {
    "type": "AmanSimplePrompt",
    "display_name": "AmanSimplePrompt",
    "category": "Dolorain / H3",
    "description": "H3 workflow node · AmanSimplePrompt",
    "inputs": [],
    "outputs": [
      {
        "name": "prompt",
        "type": "STRING"
      }
    ],
    "source": "h3-simple-prompt"
  },
  {
    "type": "H3AudioController",
    "display_name": "H3AudioController",
    "category": "Dolorain / H3",
    "description": "H3 workflow node · H3AudioController",
    "inputs": [
      {
        "name": "duration",
        "type": "FLOAT"
      }
    ],
    "outputs": [
      {
        "name": "audio",
        "type": "AUDIO"
      }
    ],
    "source": "h3-audio-controller"
  },
  {
    "type": "SamplerCustomAdvanced",
    "display_name": "SamplerCustomAdvanced",
    "category": "ComfyUI / Core",
    "description": "H3 workflow node · SamplerCustomAdvanced",
    "inputs": [
      {
        "name": "noise",
        "type": "NOISE"
      },
      {
        "name": "guider",
        "type": "GUIDER"
      },
      {
        "name": "sampler",
        "type": "SAMPLER"
      },
      {
        "name": "sigmas",
        "type": "SIGMAS"
      },
      {
        "name": "latent_image",
        "type": "LATENT"
      }
    ],
    "outputs": [
      {
        "name": "output",
        "type": "LATENT"
      },
      {
        "name": "denoised_output",
        "type": "LATENT"
      }
    ],
    "source": "comfy-core"
  },
  {
    "type": "BasicGuider",
    "display_name": "BasicGuider",
    "category": "ComfyUI / Core",
    "description": "H3 workflow node · BasicGuider",
    "inputs": [
      {
        "name": "model",
        "type": "MODEL"
      },
      {
        "name": "conditioning",
        "type": "CONDITIONING"
      }
    ],
    "outputs": [
      {
        "name": "GUIDER",
        "type": "GUIDER"
      }
    ],
    "source": "comfy-core"
  },
  {
    "type": "RandomNoise",
    "display_name": "RandomNoise",
    "category": "ComfyUI / Core",
    "description": "H3 workflow node · RandomNoise",
    "inputs": [],
    "outputs": [
      {
        "name": "NOISE",
        "type": "NOISE"
      }
    ],
    "source": "comfy-core"
  },
  {
    "type": "KSamplerSelect",
    "display_name": "KSamplerSelect",
    "category": "ComfyUI / Core",
    "description": "H3 workflow node · KSamplerSelect",
    "inputs": [],
    "outputs": [
      {
        "name": "SAMPLER",
        "type": "SAMPLER"
      }
    ],
    "source": "comfy-core"
  },
  {
    "type": "BasicScheduler",
    "display_name": "BasicScheduler",
    "category": "ComfyUI / Core",
    "description": "H3 workflow node · BasicScheduler",
    "inputs": [
      {
        "name": "model",
        "type": "MODEL"
      }
    ],
    "outputs": [
      {
        "name": "SIGMAS",
        "type": "SIGMAS"
      }
    ],
    "source": "comfy-core"
  },
  {
    "type": "CreateVideo",
    "display_name": "CreateVideo",
    "category": "Video / VAE",
    "description": "H3 workflow node · CreateVideo",
    "inputs": [
      {
        "name": "images",
        "type": "IMAGE"
      },
      {
        "name": "audio",
        "type": "AUDIO"
      },
      {
        "name": "fps",
        "type": "FLOAT"
      }
    ],
    "outputs": [
      {
        "name": "VIDEO",
        "type": "VIDEO"
      }
    ],
    "source": "comfy-core"
  },
  {
    "type": "SaveVideo",
    "display_name": "SaveVideo",
    "category": "Video / VAE",
    "description": "H3 workflow node · SaveVideo",
    "inputs": [
      {
        "name": "video",
        "type": "VIDEO"
      }
    ],
    "outputs": [
      {
        "name": "video",
        "type": "VIDEO"
      }
    ],
    "source": "comfy-core"
  },
  {
    "type": "VAEDecode",
    "display_name": "VAEDecode",
    "category": "Video / VAE",
    "description": "H3 workflow node · VAEDecode",
    "inputs": [
      {
        "name": "samples",
        "type": "LATENT"
      },
      {
        "name": "vae",
        "type": "VAE"
      }
    ],
    "outputs": [
      {
        "name": "IMAGE",
        "type": "IMAGE"
      }
    ],
    "source": "comfy-core"
  },
  {
    "type": "CLIPLoader",
    "display_name": "CLIPLoader",
    "category": "ComfyUI / Core",
    "description": "H3 workflow node · CLIPLoader",
    "inputs": [],
    "outputs": [
      {
        "name": "CLIP",
        "type": "CLIP"
      }
    ],
    "source": "comfy-core"
  },
  {
    "type": "MiniMaxH3TextEncoderCache",
    "display_name": "MiniMaxH3TextEncoderCache",
    "category": "Dolorain / H3",
    "description": "H3 workflow node · MiniMaxH3TextEncoderCache",
    "inputs": [
      {
        "name": "clip",
        "type": "CLIP"
      }
    ],
    "outputs": [
      {
        "name": "clip",
        "type": "CLIP"
      }
    ],
    "source": "linjian-ufo/comfyui-speed-minimaxH3"
  }
];
