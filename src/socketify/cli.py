import inspect
import os
import logging
import glob
import signal
import threading
from . import App, AppOptions, AppListenOptions

help = """
Usage: python -m socketify APP [OPTIONS] 
       python3 -m socketify APP [OPTIONS]
       pypy3 -m socketify APP [OPTIONS]

Options:
    --help                                              Show this Help
    --host or -h TEXT                                   Bind socket to this host.  [default:127.0.0.1]
    --port or -p INTEGER                                Bind socket to this port.  [default: 8000]
    --workers or -w INTEGER                             Number of worker processes. Defaults to the WEB_CONCURRENCY 
                                                        environment variable if available, or 1
        
    --uds TEXT                                          Bind to a UNIX domain socket, this options disables --host or -h and --port or -p.
    --ws [auto|none|module:ws]                          If informed module:ws will auto detect to use socketify.py or ASGI websockets
                                                        interface and disabled if informed none [default: auto]
    --ws-max-size INTEGER                               WebSocket max size message in bytes [default: 16777216]
    --ws-auto-ping BOOLEAN                              WebSocket auto ping sending  [default: True]
    --ws-idle-timeout INT                               WebSocket idle timeout  [default: 20]
    --ws-reset-idle-on-send BOOLEAN                     Reset WebSocket idle timeout on send [default: True]
    --ws-per-message-deflate BOOLEAN                    WebSocket per-message-deflate compression [default: False]
    --ws-max-lifetime INT                               Websocket maximum socket lifetime in minutes before forced closure, 0 to disable [default: 0]
    --ws-max-backpressure INT                           WebSocket maximum backpressure in bytes [default: 16777216]
    --ws-close-on-backpressure-limit BOOLEAN            Close connections that hits maximum backpressure [default: False]
    --lifespan [auto|on|off]                            Lifespan implementation.  [default: auto]
    --interface [auto|asgi|asgi3|wsgi|ssgi|socketify]   Select ASGI (same as ASGI3), ASGI3, WSGI or SSGI as the application interface. [default: auto]
    --disable-listen-log BOOLEAN                        Disable log when start listenning [default: False]
    --version or -v                                     Display the socketify.py version and exit.
    --ssl-keyfile TEXT                                  SSL key file
    --ssl-certfile TEXT                                 SSL certificate file
    --ssl-keyfile-password TEXT                         SSL keyfile password
    --ssl-ca-certs TEXT                                 CA certificates file
    --ssl-ciphers TEXT                                  Ciphers to use (see stdlib ssl module's) [default: TLSv1]
    --req-res-factory-maxitems INT                      Pre allocated instances of Response and Request objects for socketify interface [default: 0]
    --ws-factory-maxitems INT                           Pre allocated instances of WebSockets objects for socketify interface [default: 0]
    --task-factory-maxitems INT                         Pre allocated instances of Task objects for socketify, ASGI interface [default: 100000]

    --reload                                            Enable auto-reload. This options also disable --workers or -w option.
    --reload-ignore-patterns                           Comma delimited list of ignore strings Default "__pycache__,node_modules,build,target,.git"  could include gitignore?

Example:
    python3 -m socketify main:app -w 8 -p 8181 

"""

# --reload-dir PATH                                   Set reload directories explicitly, instead of using the current working directory.
# --reload-include TEXT                               Set extensions to include while watching for files.
#                                                     Includes '.py,.html,.js,.png,.jpeg,.jpg and .webp' by default;
#                                                     these defaults can be overridden with `--reload-exclude`.
# --reload-exclude TEXT                               Set extensions to include while watching for files.
# --reload-delay INT                                  Milliseconds to delay reload between file changes. [default: 1000]

    
def is_wsgi(module):
    return (
        hasattr(module, "__call__") and len(inspect.signature(module).parameters) == 2
    )


def is_asgi(module):
    return (
        hasattr(module, "__call__") and len(inspect.signature(module).parameters) == 3
    )


def is_ssgi(module):
    return False  # no spec yet


def is_ssgi(module):
    return False  # no spec yet


def is_socketify(module):
    return (
        hasattr(module, "__call__") and len(inspect.signature(module).parameters) == 1
    )


def is_factory(module):
    return (
        hasattr(module, "__call__") and len(inspect.signature(module).parameters) == 0
    )


def str_bool(text):
    text = str(text).lower()
    return text == "true"

class ReloadState:
    # Class object to store reload state
    # Windows only catches (SIGTERM) but it's also used
    # for other purposes, so we set a switch 
    def __init__(self):
        self.reload_pending = False

reload_state = ReloadState()

def load_module(file, reload=False):
    try:
        [full_module, app] = file.split(":")
        import importlib

        module = importlib.import_module(full_module)
        if reload:
            importlib.reload(module)

        app = getattr(module, app)
        # if is an factory just auto call
        if is_factory(module):
            app = app()
        return app
    except Exception as error:
        logging.exception(error)
        return None


def execute(args):
    print('cli.execute')
    
    try:
        _execute(args)
    except SystemExit as se:
        print('caught System exit' + str(se), flush=True)
        if 'reload' in str(se) and  '--reload' in args and reload_state.reload_pending:
            logging.info('RELOADING...')
            reload_state.reload_pending = False
            import sys
            import os
            #print(args)
            #print(sys.argv)

            #os.execv(sys.executable, ['-m socketify'] + args[1:])
            #print(sys.executable, [sys.executable, '-m', 'socketify'] + args[1:])

            # The app.run has already caught SIGTERM which closes the loop then raises SystemExit.
            # SIGTERM works across both Windows and Linux
            # Now we respawn the process with the original arguments 
            # Windows
            if sys.platform == 'win32':
                import subprocess
                subprocess.Popen([sys.executable, '-m', 'socketify'] + args[1:])
                sys.exit(0)
            # *ix
            os.execv(sys.executable, [sys.executable, '-m', 'socketify'] + args[1:])
            #os.kill(os.getpid(), signal.SIGINT)  <-- this done in the file probe 
            #or os.popen("wmic process where processid='{}' call terminate".format(os.getpid()))

def _execute(args):
    arguments_length = len(args)
    if arguments_length <= 2:
        if arguments_length == 2 and (args[1] == "--help"):
            return print(help)
        if arguments_length == 2 and (args[1] == "--version" or args[1] == "-v"):
            import pkg_resources  # part of setuptools
            import platform

            version = pkg_resources.require("socketify")[0].version
            return print(
                f"Running socketify {version} with {platform.python_implementation()} {platform.python_version()} on {platform.system()}"
            )
        elif arguments_length < 2:
            return print(help)

    file = (args[1]).lower()
    module = load_module(file)

    if not module:
        return print(f"Cannot load module {file}")

    options_list = args[2:]
    options = {}
    selected_option = None
    # lets try argparse in parallel
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--reload', default=False, action='store_true', help='reload the server on file changes, see --reload-ignore-patterns')
    parser.add_argument('rem_args', nargs=argparse.REMAINDER)  # Can move the other options here too
    args = parser.parse_args()
    
    for option in options_list:
        if selected_option:
            options[selected_option] = option
            selected_option = None
        elif option.startswith("--") or option.startswith("-"):
            if selected_option is None: # ??
                selected_option = option # ??
            else:  # --factory, --reload etc
                options[selected_option] = True
        else:
            return print(f"Invalid option ${selected_option} see --help")
    if selected_option:  # --factory, --reload etc
        options[selected_option] = True
    print(options)
    print('OPTIONS', flush=True)
    print('BUG here, say i want to pass an arg to my app if you do --dev --reload you get "--dev": "--reload"')
    print(options.get('--reload'))
    print(args.reload)
    print(args.rem_args)
    interface = (options.get("--interface", "auto")).lower()

    if interface == "auto":
        if is_asgi(module):
            from . import ASGI as Interface

            interface = "asgi"
        elif is_wsgi(module):
            from . import WSGI as Interface

            interface = "wsgi"
        elif is_ssgi(module):
            from . import SSGI as Interface

            interface = "ssgi"
        else:
            interface = "socketify"

    elif interface == "asgi" or interface == "asgi3":
        from . import ASGI as Interface

        interface = "asgi"
        # you may use ASGI in SSGI so no checks here
        if is_wsgi(module):
            return print("Cannot use WSGI interface as ASGI interface")
        if not is_asgi(module):
            return print(
                "ASGI interface must be callable with 3 parameters async def app(scope, receive and send)"
            )
    elif interface == "wsgi":
        from . import WSGI as Interface

        # you may use WSGI in SSGI so no checks here
        if is_asgi(module):
            return print("Cannot use ASGI interface as WSGI interface")
        if not is_wsgi(module):
            return print(
                "WSGI interface must be callable with 2 parameters def app(environ, start_response)"
            )

    elif interface == "ssgi":
        # if not is_ssgi(module):
        #      return print("SSGI is in development yet but is comming soon")
        # from . import SSGI as Interface
        # interface = "ssgi"
        return print("SSGI is in development yet but is comming soon")
    elif interface != "socketify":
        return print(f"{interface} interface is not supported yet")

    auto_reload = options.get("--reload", False) or '--reload' in options_list or args.reload
    workers = int(
        options.get(
            "--workers", options.get("-w", os.environ.get("WEB_CONCURRENCY", 1))
        )
    )
    if workers < 1 or auto_reload:
        workers = 1

    port = int(options.get("--port", options.get("-p", 8000)))
    host = options.get("--host", options.get("-h", "127.0.0.1"))
    uds = options.get("--uds", None)
    lifespan = options.get("--lifespan", "auto")
    lifespan = False if lifespan == "off" else True
    task_factory_maxitems = int(options.get("--task-factory-maxitems", 100000))

    disable_listen_log = options.get("--disable-listen-log", False)
    websockets = options.get("--ws", "auto")

    if websockets == "none":
        # disable websockets
        websockets = None
    elif websockets == "auto":
        # if is ASGI serve websocket by default
        if is_asgi(module):
            websockets = True
        elif is_wsgi(module):
            # if is WSGI no websockets using auto
            websockets = False
        else:  # if is socketify websockets must be set in app
            websockets = False
    else:
        # websocket dedicated module
        ws_module = load_module(websockets)
        if not ws_module:
            return print(f"Cannot load websocket module {websockets}")
        websockets = ws_module

    key_file_name = options.get("--ssl-keyfile", None)

    if key_file_name:
        ssl_options = AppOptions(
            key_file_name=options.get("--ssl-keyfile", None),
            cert_file_name=options.get("--ssl-certfile", None),
            passphrase=options.get("--ssl-keyfile-password", None),
            ca_file_name=options.get("--ssl-ca-certs", None),
            ssl_ciphers=options.get("--ssl-ciphers", None),
        )
    else:
        ssl_options = None

    def listen_log(config):
        if not disable_listen_log:
            if uds:
                print(
                    f"Listening on {config.domain} {'https' if ssl_options else 'http'}://localhost now\n"
                )
            else:
                print(
                    f"Listening on {'https' if ssl_options else 'http'}://{config.host if config.host and len(config.host) > 1 else '127.0.0.1' }:{config.port} now\n"
                )

    if websockets:
        websocket_options = {
            "compression": int(
                1 if options.get("--ws-per-message-deflate", False) else 0
            ),
            "max_payload_length": int(options.get("--ws-max-size", 16777216)),
            "idle_timeout": int(options.get("--ws-idle-timeout", 20)),
            "send_pings_automatically": str_bool(options.get("--ws-auto-ping", True)),
            "reset_idle_timeout_on_send": str_bool(
                options.get("--ws-reset-idle-on-send", True)
            ),
            "max_lifetime": int(options.get("--ws-max-lifetime", 0)),
            "max_backpressure": int(options.get("--max-backpressure", 16777216)),
            "close_on_backpressure_limit": str_bool(
                options.get("--ws-close-on-backpressure-limit", False)
            ),
        }
    else:
        websocket_options = None

    if interface == "socketify":
        if is_asgi(websockets):
            return print("Cannot mix ASGI websockets with socketify.py interface yet")
        if is_asgi(module):
            return print("Cannot use ASGI interface as socketify interface")
        elif is_wsgi(module):
            return print("Cannot use WSGI interface as socketify interface")
        elif not is_socketify(module):
            return print(
                "socketify interface must be callable with 1 parameter def run(app: App)"
            )

        # file watcher
        def launch_with_file_probe(run_method, user_module_function, loop, poll_frequency=20):
            import asyncio
            import importlib.util
            directory = os.path.dirname(importlib.util.find_spec(user_module_function.__module__).origin)
            directory_glob = os.path.join(directory, '**')
            logging.info("Watching %s" % directory_glob)
            print("Watching %s" % directory_glob, flush=True)
            ignore_patterns = options.get("--reload-ignore-patterns", "node_modules,__pycache__,.git")    
            ignore_patterns = ignore_patterns.split(',')
            print(ignore_patterns)
            def _ignore(f):
                for ignore_pattern in ignore_patterns:
                    #if '__pycache__' in f or 'node_modules' in f:
                    if ignore_pattern in f:
                        return True

            # individual os.path.mtime after glob is slow, so try using scandir
            def get_files():
                new_files = {} # path, mtime
                # [f.stat().st_mtime for f in list(os.scandir('.'))]
                new_files = _get_dir(directory, new_files)
                print(new_files)
                return new_files

            def _get_dir(path, new_files):
                print(path, flush=True)
                for f_or_d in os.scandir(path):
                    if _ignore(f_or_d.path):
                        continue
                    if f_or_d.path in new_files:
                        continue
                    if f_or_d.is_dir(): # or f_or_d.is_symlink():
                        new_files = _get_dir(f_or_d.path, new_files)
                    if f_or_d.is_file():
                        f_path = f_or_d.path
                        new_files[f_path] = f_or_d.stat().st_mtime
                return new_files

            def get_files_glob_version_slow():
                new_files = {}  # path, mtime
                print(f"getfiles1... {datetime.now()}", flush=True)
                    
                for f in glob.glob(directory_glob, recursive=True):
                    if _ignore(f):
                        continue
                    new_files[f] = os.path.getmtime(f)
                print(f"getfiles2... {datetime.now()}", flush=True)
                return new_files



            def do_check(prev_files, thread):
                from datetime import datetime 
                print(f"Doing check... {datetime.now()}", flush=True)
                new_files = get_files()
                print(f"got new files... {datetime.now()}", flush=True)
                print(new_files)
                
                if prev_files is not None and new_files != prev_files:
                    # Call exit, the wrapper will restart the process
                    print('Reload')
                    logging.info("Reloading files...")
                    reload_state.reload_pending = True  #signal for Exeute to know whether it is a real SIGTERM or our own
                    print('running sigill')
                    import signal, sys
                    signal.raise_signal(signal.SIGTERM)
                    # os.kill(os.getpid(), RELOAD_SIGNAL) #doesnt work windows # call sigusr1 back on main thread which is caught by App.run()
                    #if sys.platform == 'win32':
                    #    os.kill(os.getpid(),signal.SIGINT)  # call sigint back on main thread which is caught by App.run()
                    """print('running sysexit')
                    import sys
                    sys.exit(0)
                    print('ran sysexit')
                    """

                return new_files, thread
                    

            print('rnt 0')
            def poll_check():
                thread = None
                # poll_frequency = 1
                files = None
                while True:
                    #print('polling fs', flush=True)
                    import time
                    time.sleep(poll_frequency)
                    files, thread = do_check(files, thread)
                    #await asyncio.wait_for(thread, poll_frequency)
            thread = None
            # thread = threading.Thread(target=run_method, kwargs={from_main_thread': False}, daemon=True)
            thread = threading.Thread(target=poll_check, kwargs={}, daemon=True)
            thread.start()
            run_method()
        """
        async def launch_with_file_probe(run_method, user_module_function, loop, poll_frequency=0.5):
            import asyncio
            import importlib.util
            directory = os.path.dirname(importlib.util.find_spec(user_module_function.__module__).origin)
            logging.info("Watching %s" % directory)

            def get_files():
                new_files = {}  # path, mtime
                for f in glob.glob(directory):
                    if '__pycache__' in f:
                        continue
                    new_files[f] = os.path.getmtime(f)
                return new_files



            def run_new_thread(thread):
                #try:
                #    loop = asyncio.get_running_loop()
                #except Exception:
                #    loop = asyncio.new_event_loop()
                #if loop and thread:
                #    loop.stop()
                #    await loop.shutdown_default_executor()
                async def arun():
                    run_method(from_main_thread=False)
                # new_task = loop.create_task(arun())
                loop.call_later(delay=1, callback=check_loop, loop)
                new_task = loop.run_once(arun())
                print(type(new_task))
                print(dir(new_task))
                print('new thread')
                return new_task
                #new_thread = threading.Thread(target=run_method, args=[], kwargs={'from_main_thread': False}, daemon=True)
                #new_thread.start()
                #return new_thread



            async def do_check(prev_files, thread):
                new_files = get_files()

                if prev_files is not None and new_files != prev_files:
                    thread.cancel()
                    try:
                        await thread
                    except asyncio.CancelledError:
                        pass
                    print('reload')
                    logging.info("Reloading files...")
                    thread = run_new_thread(thread)

                return new_files, thread
                    

            import asyncio
            print('rnt 0')
            thread = run_new_thread(None)
            files = None
            poll_frequency = 0.5 
            while True:
                import time
                print('awaiting')
                # time.sleep(poll_frequency)
                done, pending = await asyncio.wait([thread], timeout=poll_frequency)
                print(pending, done)
                #await asyncio.sleep(poll_frequency)
                files, thread = await do_check(files, thread)
                #await asyncio.wait_for(thread, poll_frequency)
        # file watcher
        async def launch_with_file_probe(run_method, user_module_function, loop, poll_frequency=0.5):
            import asyncio
            import importlib.util
            directory = os.path.dirname(importlib.util.find_spec(user_module_function.__module__).origin)
            logging.info("Watching %s" % directory)

            def get_files():
                new_files = {}  # path, mtime
                for f in glob.glob(directory):
                    if '__pycache__' in f:
                        continue
                    new_files[f] = os.path.getmtime(f)
                return new_files



            def run_new_thread(thread):
                #try:
                #    loop = asyncio.get_running_loop()
                #except Exception:
                #    loop = asyncio.new_event_loop()
                #if loop and thread:
                #    loop.stop()
                #    await loop.shutdown_default_executor()
                async def arun():
                    run_method(from_main_thread=False)
                # new_task = loop.create_task(arun())
                loop.call_later(delay=1, callback=check_loop, loop)
                new_task = loop.run_once(arun())
                print(type(new_task))
                print(dir(new_task))
                print('new thread')
                return new_task
                #new_thread = threading.Thread(target=run_method, args=[], kwargs={'from_main_thread': False}, daemon=True)
                #new_thread.start()
                #return new_thread



            async def do_check(prev_files, thread):
                new_files = get_files()

                if prev_files is not None and new_files != prev_files:
                    thread.cancel()
                    try:
                        await thread
                    except asyncio.CancelledError:
                        pass
                    print('reload')
                    logging.info("Reloading files...")
                    thread = run_new_thread(thread)

                return new_files, thread
                    

            import asyncio
            print('rnt 0')
            thread = run_new_thread(None)
            files = None
            poll_frequency = 0.5 
            while True:
                import time
                print('awaiting')
                # time.sleep(poll_frequency)
                done, pending = await asyncio.wait([thread], timeout=poll_frequency)
                print(pending, done)
                #await asyncio.sleep(poll_frequency)
                files, thread = await do_check(files, thread)
                #await asyncio.wait_for(thread, poll_frequency)
                """




        # run app with the settings desired
        def run_app():
            fork_app = App(
                ssl_options,
                int(options.get("--req-res-factory-maxitems", 0)),
                int(options.get("--ws-factory-maxitems", 0)),
                task_factory_maxitems,
                lifespan,
            )
            module(fork_app)  # call module factory

            if (
                websockets
            ):  # if socketify websockets are added using --ws in socketify interface we can set here
                websockets.update(websocket_options)  # set websocket options
                fork_app.ws("/*", websockets)
            if uds:
                fork_app.listen(AppListenOptions(domain=uds), listen_log)
            else:
                fork_app.listen(AppListenOptions(port=port, host=host), listen_log)

            if auto_reload:
                # there's watchfiles module but socketify currently has no external dependencies so
                # we'll roll our own for now...
                # from watchfiles import arun_process
                logging.info(' LAUNCHING WITH RELOAD ')
                print(' LAUNCHING WITH RELOAD ', flush=True)
                launch_with_file_probe(fork_app.run, module, fork_app.loop)
            else: # run normally
                fork_app.run()

        pid_list = []
        # fork limiting the cpu count - 1
        for _ in range(1, workers):
            pid = os.fork()
            # n greater than 0 means parent process
            if not pid > 0:
                run_app()
                break
            pid_list.append(pid)

        run_app()  # run app on the main process too :)

        # sigint everything to gracefull shutdown
        import signal
        for pid in pid_list:
            os.kill(pid, signal.SIGINT)
    else:

        if uds:
            Interface(
                module,
                options=ssl_options,
                websocket=websockets,
                websocket_options=websocket_options,
                task_factory_max_items=task_factory_maxitems,
                lifespan=lifespan,
            ).listen(AppListenOptions(domain=uds), listen_log).run(workers=workers)
        else:
            Interface(
                module,
                options=ssl_options,
                websocket=websockets,
                websocket_options=websocket_options,
                task_factory_max_items=task_factory_maxitems,
                lifespan=lifespan,
            ).listen(AppListenOptions(port=port, host=host), listen_log).run(
                workers=workers
            )
