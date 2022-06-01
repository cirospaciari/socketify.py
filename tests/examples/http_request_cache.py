from socketify import App
import redis
import aiohttp
import asyncio
import json
from helpers.twolevel_cache import TwoLevelCache

#create redis poll + connections
redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
redis_conection = redis.Redis(connection_pool=redis_pool)
# 2 LEVEL CACHE (Redis to share amoung workers, Memory to be much faster)
# cache in memory is 5s, cache in redis is 10s duration 
cache = TwoLevelCache(redis_conection, 10, 10)

###
# Model
###

async def get_pokemon(session, number):
    async with session.get(f'https://pokeapi.co/api/v2/pokemon/{number}') as response:
        pokemon = await response.text()
        pokemon_name = json.loads(pokemon)['name']
        return pokemon_name

async def get_pokemon_by_number(number):
        async with aiohttp.ClientSession() as session:
            return await get_pokemon(session, number)

async def get_original_pokemons():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for number in range(1, 151):
            tasks.append(asyncio.ensure_future(get_pokemon(session, number)))
        result = await asyncio.gather(*tasks)
        return result


###
# Routes
###
def list_original_pokemons(res, req):
    
    #check cache for faster response
    value = cache.get("original_pokemons")
    if value != None: 
        return res.end(value)
    
    #get asynchronous from Model
    async def get_originals():
        value = await cache.run_once("original_pokemons", 5, get_original_pokemons)
        res.end(value)

    res.run_async(get_originals())


def list_pokemon(res, req):

    #get needed parameters
    try:
        number = int(req.get_parameter(0))
    except:
        #invalid number
        return req.set_yield(1) 

    #check cache for faster response
    key = f"pokemon-{number}"
    value = cache.get(key)
    if value != None: 
        return res.end(value)

    #get asynchronous from Model
    async def find_pokemon(number, res):
        #sync with redis lock to run only once
        #if more than 1 worker/request try to do this request, only one will call the Model and the others will get from cache
        value = await cache.run_once(key, 5, get_pokemon_by_number, number)
        res.end(value)

    res.run_async(find_pokemon(number, res))


app = App()
app.get("/", list_original_pokemons)
app.get("/:number", list_pokemon)
app.any("/*", lambda res, _: res.write_status(404).end("Not Found"))
app.listen(3000, lambda config: print("Listening on port http://localhost:%d now\n" % config.port))
app.run()
