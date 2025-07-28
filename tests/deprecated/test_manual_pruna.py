import replicate



output = replicate.run(
    "prunaai/flux-kontext-dev:c0a52f40fdf6cec07c33bbab573139ab1d1b12cb645922db65f17558a1b1f378",
    input={
        "seed": -1,
        "prompt": "Change the background to a beach while keeping the person in the exact same position, scale, and pose. Maintain identical subject placement, camera angle, framing, and perspective. Only replace the environment around them",
        "guidance": 2.5,
        "image_size": 1024,
        "speed_mode": "Juiced 🔥 (default)",
        "aspect_ratio": "match_input_image",
        "img_cond_path": "test_images/test-img.png",
        "output_format": "jpg",
        "output_quality": 80,
        "num_inference_steps": 30
    }
)

# To access the file URL:
print(output.url())