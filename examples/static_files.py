# We have an version of this using aiofile and aiofiles
# This is an sync version without any dependencies is normally much faster in CPython and PyPy3
# In production we highly recommend to use CDN like CloudFlare or/and NGINX or similar for static files (in any language/framework)

# Some performance data from my personal machine (Debian 12/testing, i7-7700HQ, 32GB RAM, Samsung 970 PRO NVME)
# using oha -c 400 -z 5s http://localhost:3000/

# nginx     - try_files                 -  77630.15 req/s
# pypy3     - socketify static          -  16797.30 req/s
# python3   - socketify static          -  10140.19 req/s
# node.js   - @fastify/static           -   5437.16 req/s
# node.js   - express.static            -   4077.49 req/s
# python3   - socketify static_aiofile  -   2390.96 req/s
# python3   - socketify static_aiofiles -   1615.12 req/s
# python3   - scarlette static uvicorn  -   1335.56 req/s
# python3   - fastapi static gunicorn   -   1296.14 req/s
# pypy3     - socketify static_aiofile  -    639.70 req/s
# pypy3     - socketify static_aiofiles -    637.55 req/s
# pypy3     - fastapi static gunicorn   -    253.31 req/s
# pypy3     - scarlette static uvicorn  -    279.45 req/s

# Conclusions:
# With PyPy3 only static is really usable gunicorn/uvicorn, aiofiles and aiofile are really slow on PyPy3 maybe this changes with HPy
# Python3 with any option will be faster than gunicorn/uvicorn but with PyPy3 with static we got 4x (or almost this in case of fastify) performance of node.js
# But even PyPy3 + socketify static is 5x+ slower than NGINX

# Anyway we really recommends using NGINX or similar + CDN for production like everybody else
# Gunicorn production recommendations: https://docs.gunicorn.org/en/latest/deploy.html#deploying-gunicorn
# Express production recommendations: https://expressjs.com/en/advanced/best-practice-performance.html
# Fastify production recommendations: https://www.fastify.io/docs/latest/Guides/Recommendations/

from socketify import App, sendfile


app = App()


# send home page index.html
async def home(res, req):
    # sends the whole file with 304 and bytes range support
    await sendfile(res, req, "./public/index.html")


app.get("/", home)

# serve all files in public folder under /* route (you can use any route like /assets)
app.static("/", "./public")

app.listen(
    3000,
    lambda config: print("Listening on port http://localhost:%d now\n" % config.port),
)
app.run()
