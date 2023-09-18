from typing import Dict

import aiohttp
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

description = """
### Usage
Add `fx` before your `gall.dcinside.com` link to make it `gall.fxdcinside.com`
"""

app = FastAPI(
    title="Fx dcinside",
    summary="Fix dcinside link preview on Discord.",
    description=description,
    license_info={
        "name": "MIT",
        "url": "https://github.com/KOZ39/fxdcinside.com/blob/master/LICENSE",
    },
    docs_url="/",
    redoc_url=None
)

templates = Jinja2Templates(directory="templates")


async def fetch_open_graph_meta_tags(url: str) -> Dict[str, str]:
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
            }
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                soup = BeautifulSoup(await resp.text(), "html.parser")
                return {
                    'title': soup.find("meta", property="og:title")["content"],
                    'description': soup.find("meta", property="og:description")["content"],
                    'image': soup.find("meta", property="og:image")["content"]
                }
    except (aiohttp.ClientError, AttributeError, KeyError, TypeError):
        return {
            'title': "갤러리 - 커뮤니티 포털 디시인사이드",
            'description': "디시인사이드는 다양한 주제를 갤러리, 마이너 갤러리, 미니 갤러리 커뮤니티 서비스로 제공합니다. 통합검색을 이용해 여러 갤러리를 확인해 보세요.",
            'image': "https://nstatic.dcinside.com/dc/w/images/descrip_img.png"
        }


async def render_template(request: Request, id: str, no: int, base_url: str = "https://gall.dcinside.com", infix: str = "", share_url: bool = False) -> templates.TemplateResponse:
    if share_url:
        url = f"{base_url}{infix}/{id}/{no}"
    else:
        url = f"{base_url}{infix}/board/view/?id={id}&no={no}"

    og = await fetch_open_graph_meta_tags(url)
    return templates.TemplateResponse("redirect.html", {'request': request, 'og': og, 'url': url})


@app.get("/board/view/", response_class=HTMLResponse)
async def gallery(request: Request, id: str, no: int):
    return await render_template(request, id, no)


@app.get("/mgallery/board/view/", response_class=HTMLResponse)
async def minor_gallery(request: Request, id: str, no: int):
    return await render_template(request, id, no, infix="/mgallery")


@app.get("/mini/board/view/", response_class=HTMLResponse)
async def mini_gallery(request: Request, id: str, no: int):
    return await render_template(request, id, no, infix="/mini")


@app.get("/{id}/{no}", response_class=HTMLResponse)
async def gallery(request: Request, id: str, no: int):
    return await render_template(request, id, no, share_url=True)


@app.get("/m/{id}/{no}", response_class=HTMLResponse)
async def minor_gallery(request: Request, id: str, no: int):
    return await render_template(request, id, no, infix="/m", share_url=True)


@app.get("/mini/{id}/{no}", response_class=HTMLResponse)
async def mini_gallery(request: Request, id: str, no: int):
    return await render_template(request, id, no, infix="/mini", share_url=True)


@app.get("/board/{id}/{no}", response_class=HTMLResponse)
async def mobile(request: Request, id: str, no: int):
    return await render_template(request, id, no, base_url="https://m.dcinside.com", infix="/board", share_url=True)
