import time
import cloudinary

import cloudinary.utils
import cloudinary.uploader

from fastapi.concurrency import run_in_threadpool


def _sign(params_to_sign: dict) -> dict:
    """Sign a set of params and attach the public config the client needs."""

    config = cloudinary.config()
    signature = cloudinary.utils.api_sign_request(params_to_sign, config.api_secret)

    return {
        **params_to_sign,
        "signature": signature,
        "api_key": config.api_key,
        "cloud_name": config.cloud_name,
    }


def generate_upload_signatures() -> dict:
    """Signed params for uploading BOTH the video and its thumbnail directly to Cloudinary."""

    timestamp = int(time.time())

    video = _sign({
        "timestamp": timestamp,
        "folder": "instream/videos",
        "eager": "sp_hd/m3u8",
        "eager_async": "true",
    })

    thumbnail = _sign({
        "timestamp": timestamp,
        "folder": "instream/thumbnail",
    })

    return {"video": video, "thumbnail": thumbnail}


async def destroy_asset(public_id: str, resource_type: str) -> None:
    """Delete an asset from Cloudinary and purge its CDN cache. Resource_type is "video" for the video, "image" for the thumbnail.
    """
    
    await run_in_threadpool(
        cloudinary.uploader.destroy,
        public_id,
        resource_type=resource_type,
        invalidate=True,
    )
