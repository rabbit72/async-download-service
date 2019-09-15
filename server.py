import asyncio
import logging
import os
from asyncio.subprocess import PIPE
from pathlib import Path

import aiofiles
from aiohttp import web

ROOT_PHOTO_DIR = Path("./test_photos").resolve()

routes = web.RouteTableDef()


@routes.get("/")
async def handle_index_page(request):
    async with aiofiles.open("index.html", mode="r") as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type="text/html")


async def get_archive_stream(photos_dir: Path, allowed_ext: str):
    get_files_command = f"cd {photos_dir} && ls $PWD/*.{allowed_ext}"
    get_zip_command = ("zip", "-j", "-@", "-")
    filenames_read, filenames_write = os.pipe()
    dev_null = await aiofiles.open(os.devnull, "w")

    try:
        await asyncio.create_subprocess_shell(
            get_files_command, stdout=filenames_write, stderr=dev_null
        )
        os.close(filenames_write)
        archive_stream = await asyncio.create_subprocess_exec(
            *get_zip_command, stdin=filenames_read, stdout=PIPE, stderr=dev_null
        )
    finally:
        os.close(filenames_read)
        dev_null.close()
    return archive_stream


async def stream_archive(
    photos_dir: Path, response: web.StreamResponse, allowed_ext: str = "jpg"
) -> None:
    chunk_number = 1
    chunk_size = 10 * 1024  # 10 KB
    archive_stream = await get_archive_stream(photos_dir, allowed_ext)
    try:
        while True:
            zip_chunk = await archive_stream.stdout.read(chunk_size)
            if not zip_chunk:
                break
            logging.debug(f"Sending archive chunk {chunk_number} for {photos_dir}")
            # await asyncio.sleep(1)
            await response.write(zip_chunk)
            chunk_number += 1
    except asyncio.CancelledError:
        logging.warning("Download was interrupted.")
        archive_stream.kill()
        raise


@routes.get("/archive/{archive_hash}/")
async def archive(request):
    archive_hash = request.match_info.get("archive_hash")

    photos_dir = ROOT_PHOTO_DIR / archive_hash
    if not photos_dir.exists():
        raise web.HTTPNotFound(text=f"The archive {archive_hash}.zip does not exist")

    response = web.StreamResponse()
    content_type = "application/zip"
    content_disposition = f'attachment; filename="{archive_hash}.zip"'
    response.headers["Content-Type"] = content_type
    response.headers["Content-Disposition"] = content_disposition
    # send HTTP headers before response streaming
    await response.prepare(request)

    try:
        await stream_archive(photos_dir, response)
    finally:
        response.force_close()
    return response


if __name__ == "__main__":
    console_format = "%(levelname)-8s: [%(asctime)s] %(message)s"
    logging.basicConfig(format=console_format, level=logging.DEBUG)

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)
