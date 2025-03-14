import logging

import aiohttp
from bs4 import BeautifulSoup, SoupStrainer
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="Fx dcinside",
    summary="Fix dcinside link preview on Discord.",
    docs_url="/docs",
    redoc_url=None,
)

templates = Jinja2Templates(directory="templates")

only_meta_tags = SoupStrainer("meta")


async def fetch_open_graph_meta_tags(url: str) -> dict[str, str]:
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            }
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                soup = BeautifulSoup(await resp.text(), "html.parser", parse_only=only_meta_tags)

                return {
                    "title": soup.find("meta", property="og:title")["content"],
                    "description": soup.find("meta", property="og:description")["content"],
                    "image": soup.find("meta", property="og:image")["content"],
                }
    except Exception as e:
        logging.exception(e)

        return {
            "title": "We are with you all the way! IT is Life! 디시인사이드 입니다.",
            "description": "접속불가",
            "image": "https://nstatic.dcinside.com/dc/w/images/descrip_img.png",
        }


async def render_template(
    request: Request,
    id: str,
    no: int,
    base_url: str = "https://gall.dcinside.com",
    infix: str = "",
):
    url = f"{base_url}{infix}/{id}/{no}"
    og = await fetch_open_graph_meta_tags(url)

    return templates.TemplateResponse(
        "redirect.html", {"request": request, "og": og, "url": url}
    )


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("https://github.com/KOZ39/fxdcinside.com")


@app.get("/board/view/", response_class=HTMLResponse)
async def gallery(id: str, no: int, request: Request):
    return await render_template(request, id, no)


@app.get("/m/{id}/{no}", response_class=HTMLResponse)
@app.get("/mgallery/board/view/", response_class=HTMLResponse)
async def minor_gallery(id: str, no: int, request: Request):
    return await render_template(request, id, no, infix="/m")


@app.get("/mini/{id}/{no}", response_class=HTMLResponse)
@app.get("/mini/board/view/", response_class=HTMLResponse)
async def mini_gallery(id: str, no: int, request: Request):
    return await render_template(request, id, no, infix="/mini")


# HACK: 마이너 갤러리 단축 주소의 301 리다이렉션 판단 불가
# Ref: https://github.com/KOZ39/fxdcinside.com/issues/1
@app.get("/board/{id}/{no}", response_class=HTMLResponse) # Mobile
@app.get("/{id}/{no}", response_class=HTMLResponse) # Short
async def short_or_mobile(id: str, no: int, request: Request):
    return await render_template(request, id, no, base_url="https://m.dcinside.com", infix="/board")
