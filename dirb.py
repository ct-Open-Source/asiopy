#!/usr/bin/env python3

"""
Copyright (c) 2023 Oliver Lau, Heise Medien GmbH & Co. KG

Diese Software wurde zu Lehr- und Demonstrationszwecken 
geschaffen und ist nicht für den produktiven Einsatz vorgesehen.
Heise Medien und der Autor haften daher nicht für Schäden, die
aus der Nutzung der Software entstehen, und übernehmen keine
Gewähr für ihre Vollständigkeit, Fehlerfreiheit und Eignung für
einen bestimmten Zweck.
"""

import argparse
import sys
import io
from tornado.httpclient import AsyncHTTPClient, HTTPClientError, HTTPRequest
import asyncio
from typing import Iterable

class Dirb:
    def __init__(self, base_url: str, **kwargs) -> None:
        self.base_url = base_url
        self.found_callback = kwargs.get('found_callback', None)
        self.error_callback = kwargs.get('error_callback', None)
        self.pre_fetch_callback = kwargs.get('pre_fetch_callback', None)
        self.user_agent = kwargs.get('user_agent', None)
        self.follow_redirects = kwargs.get('follow_redirects', False)
        self.probe_extensions = kwargs.get('probe_extensions', [])
        self.probe_variations = kwargs.get('probe_variations', [])
        self.cookies = kwargs.get('cookies', None)
        self.headers = kwargs.get('headers', None)
        credentials = kwargs.get('credentials', None)
        self.auth_user_name, self.auth_password = credentials.split(':') \
            if isinstance(credentials, str) else None, None
        self.queue = asyncio.Queue()
        self.num_workers = kwargs.get('num_workers', 10)
        self.results = []

    async def run(self, paths: Iterable[str]) -> None:
        # sanitize input stream
        paths = set([path.strip() for path in paths])
        for url in paths:
            await self.queue.put(url)
            for ext in self.probe_extensions:
                await self.queue.put(f'{url}{ext}')
        # spawn workers
        workers = [asyncio.create_task(self.worker()) 
                   for _ in range(self.num_workers)]
        # wait for queue to be processed
        await self.queue.join()
        for worker in workers:
            worker.cancel()

    async def try_url(self) -> None:
        path = await self.queue.get()
        if not path.startswith('/'):
            path = '/' + path
        url = f'{self.base_url}{path}'
        if callable(self.pre_fetch_callback):
            await self.pre_fetch_callback(path)
        try:
            http_client = AsyncHTTPClient()
            req = HTTPRequest(url,
                              user_agent=self.user_agent,
                              headers=self.headers,
                              follow_redirects=self.follow_redirects)
            response = await http_client.fetch(req)
            self.results.append({
                'path': path,
                'effective_url': response.effective_url,
                'status_code': response.code,
                'headers': [header for header in response.headers.get_all()],
            })
            if response.code == 200:
                for ext in self.probe_variations:
                    await self.queue.put(f'{path}{ext}')
            if callable(self.found_callback):
                await self.found_callback(path)
        except HTTPClientError as e:
            if callable(self.error_callback):
                await self.error_callback(f'{path} -> HTTP status code = {e.code}')
            self.results.append({
                'path': path,
                'effective_url': '',
                'status_code': e.code,
                'headers': [],
            })
        finally:
            self.queue.task_done()

    async def worker(self) -> None:
        while True:
            try:
                await self.try_url()
            except asyncio.CancelledError:
                return

    @property
    def result(self) -> Iterable[str]:
        return self.results

    def alive(self) -> Iterable[str]:
        return [r for r in self.results if r['status_code'] == 200]


async def main(base_url: str, verbose: int, word_files: Iterable[io.StringIO], **kwargs) -> None:

    lock = asyncio.Lock()

    async def pre_fetch_hook(url: str) -> None:
        async with lock:
            print(f'\rChecking {url} ... \u001b[0K', end='', flush=True)

    async def found_hook(url: str) -> None:
        async with lock:
            print(f'\n\u001b[32;1mFOUND {url}\u001b[0m')

    async def error_hook(message: str) -> None:
        async with lock:
            print(f'\n\u001b[31;1mERROR: {message}\u001b[0m')

    quiet = kwargs.get('quiet', False)
    kwargs['pre_fetch_callback'] = pre_fetch_hook \
        if not quiet else None
    kwargs['found_callback'] = found_hook \
        if not quiet and verbose > 0 else None
    kwargs['error_callback'] = error_hook \
        if not quiet and verbose > 0 else None

    dirb = Dirb(base_url, **kwargs)
    for word_file in word_files:
        await dirb.run(word_file.readlines())

    if kwargs.get('output_file'):
        output = open(kwargs.get('output_file'), 'w+')
    else:
        output = sys.stdout

    if kwargs.get('csv'):
        ESC_QUOTES = str.maketrans({'"': r'\"'})
        FIELDS = ['status_code', 'path', 'effective_url', 'headers']
        output.write(f'''{';'.join(FIELDS)}\n''')
        for result in dirb.results:
            output.write(f'''{result['status_code']};"{result['path'].translate(ESC_QUOTES)}";"{result['effective_url'].translate(ESC_QUOTES)}";''')
            headers = [f'"{h.translate(ESC_QUOTES)}:{v.translate(ESC_QUOTES)}"' for (h, v) in result['headers']]
            output.write(','.join(headers))
            output.write('\n')
    else:
        alive = dirb.alive()
        if len(alive) == 0:
            print('\n\u001b[31;1mNOTHING FOUND 🧐\u001b[0m')
        else:
            print(f'''\n\u001b[32;1mFound {len(alive)} accessible URL{'s' if len(alive) != 1 else ''}:\u001b[0m''')
            for d in alive:
                print(f'''- {d['path']}''')


if __name__ == '__main__':
    DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
    DEFAULT_NUM_WORKERS = 20
    parser = argparse.ArgumentParser(prog='dirb', description='Directory Buster')
    parser.add_argument('base_url', help='Base URL, e.g. https://example.com')
    parser.add_argument('-n', '--num-workers', help='parallelize scanning with n workers running concurrently', type=int, default=DEFAULT_NUM_WORKERS)
    parser.add_argument('-v', '--verbose', action='count', default=0)
    parser.add_argument('-q', '--quiet', action='store_true', default=False)
    parser.add_argument('-w', '--word-file', help='Word file', action='append', default=[])
    parser.add_argument('-a', '--user-agent', help='User agent', default=DEFAULT_USER_AGENT)
    parser.add_argument('-c', '--cookie', help='Cookie string')
    parser.add_argument('-H', '--header', help='Add header string', action='append', default=[])
    parser.add_argument('-u', '--credentials', help='username:password')
    parser.add_argument('-X', '--probe-extensions', help='do not only check the path itself, but also try every path by adding these extensions', default=None)
    parser.add_argument('-M', '--probe-variations', help='if a path is found, check these variations by appending them to the path', default=None)
    parser.add_argument('-f', '--follow-redirects', action='store_true', help='Follow 301/302 redirects', default=False)
    parser.add_argument('-t', '--csv', action='store_true', help='Generate CSV output', default=False)
    parser.add_argument('-o', '--output', help='Write output to file')
    args = parser.parse_args()
    word_files = [sys.stdin]
    if len(args.word_file) > 0:
        word_files = [open(filename, 'r') for filename in args.word_file]
    asyncio.run(main(
        args.base_url,
        args.verbose,
        word_files,
        quiet=args.quiet,
        user_agent=args.user_agent,
        cookie=args.cookie,
        headers=args.header,
        credentials=args.credentials,
        follow_redirects=args.follow_redirects,
        probe_extensions=args.probe_extensions.split(',') if isinstance(args.probe_extensions, str) else [],
        probe_variations=args.probe_variations.split(',') if isinstance(args.probe_variations, str) else [],
        num_workers=args.num_workers,
        csv=args.csv,
        output_file=args.output))
