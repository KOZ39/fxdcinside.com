# fxdcinside.com
> Fix dcinside link preview on Discord.

Implement [fixdcinside.com](https://github.com/iorphx/fixdcinside.com) with [FastAPI](https://fastapi.tiangolo.com/)

## Requirements
- Python 3.10+

## Running
```bash
git clone https://github.com/KOZ39/fxdcinside.com.git
cd fxdcinside.com
pip install -r requirements.txt
```

```bash
uvicorn main:app
# or
uvicorn main:app --port <port>
```

## Usage
- Add `fx` before your `gall.dcinside.com` link to make it `gall.fxdcinside.com`
- Add `fx` before your `m.dcinside.com` link to make it `m.fxdcinside.com`

## License
[MIT](https://github.com/KOZ39/fxdcinside.com/blob/master/LICENSE)
