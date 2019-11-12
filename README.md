# python_concurrent_web_server

Python concurrent webserver that utilizes Python's WSGI to interact with
all Python Web Framework applications. Spawns new children for each incoming socket
client connection, and uses signals from children to reap processes
so as to not hog memory.
