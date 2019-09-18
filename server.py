import asyncio
import logging
import os
from asyncio.subprocess import PIPE
from pathlib import Path

import aiofiles
import click
from aiohttp import web

routes = web.RouteTableDef()


@routes.get("/")
async def handle_index_page(request):
    async with aiofiles.open("index.html", mode="r") as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type="text/html")


async def stream_archive(photos_dir: Path, response: web.StreamResponse) -> None:
    delay = float(os.environ.get("DELAY", 0))
    chunk_size = int(os.environ["CHUNKSIZE"]) * 1024

    zip_command = ("zip", "-jr", "-", f"{photos_dir}")
    archive_stream = await asyncio.create_subprocess_exec(
        *zip_command, stdout=PIPE, stderr=PIPE
    )
    try:
        chunk_number = 1
        while True:
            zip_chunk = await archive_stream.stdout.read(chunk_size)
            if not zip_chunk:
                break
            await response.write(zip_chunk)
            logging.debug(f"Sending archive chunk {chunk_number} for {photos_dir}")
            if delay:
                await asyncio.sleep(delay)
            chunk_number += 1

    except asyncio.CancelledError:
        logging.warning("Download was interrupted.")
        archive_stream.kill()
        await archive_stream.communicate()
        raise


@routes.get("/archive/{archive_hash}/")
async def archive(request):
    archive_hash = request.match_info.get("archive_hash")
    root_photo_dir = Path(os.environ["ROOT_PHOTO_DIR"]).resolve()
    photos_dir = root_photo_dir / archive_hash
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


def set_logging(log_level: str):
    log_format = "%(levelname)-8s: [%(asctime)s] %(message)s"
    logging.basicConfig(format=log_format, level=log_level)


@click.command()
@click.option(
    "--photo-dir",
    "-p",
    type=click.Path(exists=True),
    default="./test_photos/",
    help="Path to root root directory",
)
@click.option(
    "--delay",
    "-d",
    type=click.FloatRange(0.1, 10),
    required=False,
    help="Delay after each zip chunk (in seconds)",
)
@click.option(
    "--log-level",
    "-l",
    type=click.Choice(["debug", "info", "warning", "error", "critical"]),
    default="info",
    show_default=True,
    required=False,
    callback=lambda cxt, param, value: value.upper(),
    help="Set logging level",
)
@click.option(
    "--chunk-size",
    type=click.IntRange(1, 1024),
    default=10,
    show_default=True,
    help="Set chunk size (KB)",
)
@click.option("--log/--no-log", default=True, show_default=True, help="Disable logging")
def main(photo_dir, delay, log, log_level, chunk_size):
    if log:
        set_logging(log_level)

    if delay:
        logging.debug(f"You defined {delay} sec. delay")
        os.environ["DELAY"] = f"{delay}"

    os.environ["ROOT_PHOTO_DIR"] = photo_dir
    os.environ["CHUNKSIZE"] = f"{chunk_size}"

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)


if __name__ == "__main__":
    main()
