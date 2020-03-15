import discord
import inspect
import ast
import signal
from contextlib import contextmanager
from dotenv import load_dotenv
import os

authorized = {163760317963304962}

@contextmanager
def timeout(time):
    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time)

    try:
        yield
    except TimeoutError:
        pass
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
        
def raise_timeout(signum, frame):
    raise TimeoutError

client = discord.Client()

def insert_returns(body):
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$list') and message.author.id in authorized:
        res = ""
        for user in authorized:
            res += str(user)+"\n"
    
        await message.channel.send(res)

    if message.content.startswith('$auth') and message.author.id in authorized:
        for mention in message.mentions:
            authorized.add( mention.id )

    if message.content.startswith('```py') and message.author.id in authorized:
        code = message.content[5:-3]
        print(code)
        
        fn_name = "_eval_expr"

        # add a layer of indentation
        code = "\n".join(f"    {i}" for i in code.splitlines())

        # wrap in async def body
        body = f"async def {fn_name}():\n{code}"

        parsed = ast.parse(body)
        body = parsed.body[0].body

        insert_returns(body)

        env = {
            'bot': client,
            'discord': discord,
            'message': message
        }
        
        with timeout(10):
            exec(compile(parsed, filename="<ast>", mode="exec"), env) #optionally add , env)

            result = (await eval(f"{fn_name}()", env))
            await message.channel.send(result)

load_dotenv()
client.run(os.getenv("apiKey"))