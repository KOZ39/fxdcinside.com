# fxdcinside.com
> Fix dcinside link preview on Discord.

Implement [fixdcinside.com](https://github.com/iorphx/fixdcinside.com) with FastAPI

## Requirements
- Python 3.8+

## Installation
```
$ git clone https://github.com/KOZ39/fxdcinside.com.git
$ cd fxdcinside.com
$ pip install -r requirements.txt
```

## Usage
> **Warning**: In order for the application to function properly, an SSL certificate and a web server like Nginx are required. Please make sure to configure SSL properly and set up a reverse proxy with Nginx or a similar web server.

```
$ uvicorn app:app
# or
$ uvicorn app:app --port <port>
```

Add `fx` before your `gall.dcinside.com` link to make it `gall.fxdcinside.com`

## License
[MIT](https://github.com/KOZ39/fxdcinside.com/blob/master/LICENSE)
