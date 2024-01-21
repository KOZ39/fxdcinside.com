# fxdcinside.com
> Fix dcinside link preview on Discord.

Implement [fixdcinside.com](https://github.com/iorphx/fixdcinside.com) with [FastAPI](https://fastapi.tiangolo.com/)

## Requirements
- Python 3.8+

## Installation
```bash
git clone https://github.com/KOZ39/fxdcinside.com.git
cd fxdcinside.com
pip install -r requirements.txt
```

> [!WARNING]
> In order for the application to function properly, an SSL certificate and a web server like Nginx are required. Please make sure to configure SSL properly and set up a reverse proxy with Nginx or a similar web server.

```bash
uvicorn app:app
# or
uvicorn app:app --port <port>
```

## Usage
Add `fx` before your `gall.dcinside.com` link to make it `gall.fxdcinside.com`

## License
[MIT](https://github.com/KOZ39/fxdcinside.com/blob/master/LICENSE)
