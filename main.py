import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from time import monotonic

import aiohttp
from bs4 import BeautifulSoup, SoupStrainer
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


logger = logging.getLogger(__name__)

HTTP_TIMEOUT = aiohttp.ClientTimeout(
    total=15,
    connect=5,
    sock_read=8,
)

MAX_HEAD_BYTES = 512 * 1024

OG_CACHE_TTL_SECONDS = 10 * 60
OG_CACHE_MAX_SIZE = 512

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/158.0.0.0 Safari/537.36"
)


class HtmlHeadTooLargeError(ValueError):
    """The HTML head exceeds the allowed size."""


@dataclass(slots=True)
class CacheEntry:
    value: dict[str, str]
    expires_at: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_session = aiohttp.ClientSession(
        timeout=HTTP_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
    )
    app.state.og_cache: dict[str, CacheEntry] = {}
    app.state.og_cache_lock = asyncio.Lock()

    try:
        yield
    finally:
        await app.state.http_session.close()


app = FastAPI(
    title="Fx dcinside",
    summary="Fix dcinside link preview on Discord.",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

only_meta_tags = SoupStrainer("meta")


def make_fallback_og(image_url: str) -> dict[str, str]:
    return {
        "title": (
            "We are with you all the way! "
            "IT is Life! 디시인사이드 입니다."
        ),
        "description": "접속불가",
        "image": image_url,
    }


async def get_cached_og_tags(
    request: Request,
    url: str,
) -> dict[str, str] | None:
    cache: dict[str, CacheEntry] = request.app.state.og_cache
    lock: asyncio.Lock = request.app.state.og_cache_lock
    now = monotonic()

    async with lock:
        entry = cache.get(url)

        if entry is None:
            return None

        if entry.expires_at <= now:
            del cache[url]
            return None

        return entry.value.copy()


async def cache_og_tags(
    request: Request,
    url: str,
    og: dict[str, str],
) -> None:
    cache: dict[str, CacheEntry] = request.app.state.og_cache
    lock: asyncio.Lock = request.app.state.og_cache_lock
    now = monotonic()

    async with lock:
        expired_urls = [
            cached_url
            for cached_url, entry in cache.items()
            if entry.expires_at <= now
        ]

        for expired_url in expired_urls:
            del cache[expired_url]

        cache.pop(url, None)

        while len(cache) >= OG_CACHE_MAX_SIZE:
            oldest_url = next(iter(cache))
            del cache[oldest_url]

        cache[url] = CacheEntry(
            value=og.copy(),
            expires_at=now + OG_CACHE_TTL_SECONDS,
        )


async def fetch_og_tags(
    request: Request,
    url: str,
    fallback_image_url: str,
) -> dict[str, str]:
    cached_og = await get_cached_og_tags(request, url)

    if cached_og is not None:
        logger.debug("OG cache hit: url=%s", url)
        return cached_og

    session: aiohttp.ClientSession = request.app.state.http_session
    buf = bytearray()

    try:
        async with session.get(url) as response:
            response.raise_for_status()

            async for chunk in response.content.iter_chunked(16 * 1024):
                buf.extend(chunk)

                lowered_buf = buf.lower()
                head_end = lowered_buf.find(b"</head>")

                if head_end != -1:
                    head_end += len(b"</head>")

                    if head_end > MAX_HEAD_BYTES:
                        raise HtmlHeadTooLargeError(f"HTML head exceeded {MAX_HEAD_BYTES} bytes")

                    del buf[head_end:]
                    break

                if len(buf) > MAX_HEAD_BYTES:
                    raise HtmlHeadTooLargeError(f"HTML head exceeded {MAX_HEAD_BYTES} bytes")

        soup = BeautifulSoup(bytes(buf), "html.parser", parse_only=only_meta_tags)

        og = {
            "title": soup.find("meta", property="og:title")["content"],
            "description": soup.find("meta", property="og:description")["content"],
            "image": "",
        }

        await cache_og_tags(request, url, og)

        return og

    except aiohttp.ClientResponseError as exc:
        logger.warning("dcinside returned an error: url=%s status=%s", url, exc.status)

    except (asyncio.TimeoutError, aiohttp.ClientError) as exc:
        logger.warning("failed to fetch dcinside metadata: url=%s error=%r", url, exc)

    except HtmlHeadTooLargeError:
        logger.warning("dcinside response head was too large: url=%s limit=%s", url, MAX_HEAD_BYTES)

    except Exception:
        logger.exception("failed to process OG metadata: url=%s", url)

    return make_fallback_og(fallback_image_url)


async def template_or_redirect(
    request: Request,
    id: str,
    no: int,
    base_url: str = "https://gall.dcinside.com",
    infix: str = "",
):
    url = f"{base_url}{infix}/{id}/{no}"
    ua = (request.headers.get("user-agent") or "").lower()

    if "discordbot" in ua:
        canonical_url = str(request.url)
        fallback_image_url = str(
            request.url_for(
                "static",
                path="descrip_img.png",
            )
        )
        og = await fetch_og_tags(
            request,
            url,
            fallback_image_url,
        )

        return templates.TemplateResponse(
            request,
            "index.html",
            context={
                "og": og,
                "canonical_url": canonical_url,
            },
        )
    else:
        return RedirectResponse(url)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("https://github.com/KOZ39/fxdcinside.com")


@app.get("/board/view/", response_class=HTMLResponse)
async def gallery(id: str, no: int, request: Request):
    return await template_or_redirect(request, id, no)


@app.get("/m/{id}/{no}", response_class=HTMLResponse)
@app.get("/mgallery/board/view/", response_class=HTMLResponse)
async def minor_gallery(id: str, no: int, request: Request):
    return await template_or_redirect(request, id, no, infix="/m")


@app.get("/mini/{id}/{no}", response_class=HTMLResponse)
@app.get("/mini/board/view/", response_class=HTMLResponse)
async def mini_gallery(id: str, no: int, request: Request):
    return await template_or_redirect(request, id, no, infix="/mini")


@app.get("/person/{id}/{no}", response_class=HTMLResponse)
@app.get("/person/board/view/", response_class=HTMLResponse)
async def person_gallery(id: str, no: int, request: Request):
    return await template_or_redirect(request, id, no, infix="/person")


# HACK: 마이너 갤러리 단축 주소의 301 리다이렉션 판단 불가
# Ref: https://github.com/KOZ39/fxdcinside.com/issues/1
@app.get("/board/{id}/{no}", response_class=HTMLResponse) # Mobile
@app.get("/{id}/{no}", response_class=HTMLResponse) # Short
async def short_or_mobile(id: str, no: int, request: Request):
    return await template_or_redirect(request, id, no, base_url="https://m.dcinside.com", infix="/board")
