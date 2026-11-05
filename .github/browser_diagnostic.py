"""Observe browser startup for two local test files; run inside network isolation."""

import asyncio
import json
import os
import sys
import threading
import time
from pathlib import Path

import aiohttp
import pytest

sys.path.insert(0, str(Path.cwd()))
allowed = {
	'tests/ci/interactions/test_autocomplete_interaction.py',
	'tests/ci/browser/test_dom_serializer.py',
}
assert len(sys.argv) == 2 and sys.argv[1] in allowed
output = Path('diagnostic-output')
prefix = Path(sys.argv[1]).stem
processes = []
spawn = asyncio.create_subprocess_exec
request = aiohttp.ClientSession._request


async def observed_spawn(*args, **kwargs):
	"""Save Chrome output directly so evidence survives a hung pytest process."""
	if any(str(arg).startswith('--remote-debugging-port=') for arg in args):
		index = len(processes)
		print('DIAGNOSTIC launch', json.dumps(args), flush=True)
		with (output / f'{prefix}-{index}-stdout.log').open('wb') as stdout:
			with (output / f'{prefix}-{index}-stderr.log').open('wb') as stderr:
				kwargs.update(stdout=stdout, stderr=stderr)
				process = await spawn(*args, **kwargs)
		processes.append(process)
		print('DIAGNOSTIC pid', process.pid, flush=True)
		return process
	return await spawn(*args, **kwargs)


async def observed_request(self, method, url, **kwargs):
	"""Observe the existing readiness request without changing its timeout."""
	probe = str(url).startswith('http://127.0.0.1:') and str(url).endswith('/json/version')
	try:
		response = await request(self, method, url, **kwargs)
		if probe:
			print('DIAGNOSTIC CDP', str(url), response.status, flush=True)
		return response
	except BaseException as exc:
		if probe:
			print('DIAGNOSTIC CDP', str(url), type(exc).__name__, str(exc), flush=True)
		raise


def report_processes():
	"""Report exit status even while the test awaits browser startup."""
	while True:
		for process in list(processes):
			print('DIAGNOSTIC process', process.pid, 'returncode', process.returncode, flush=True)
		time.sleep(5)


asyncio.create_subprocess_exec = observed_spawn
aiohttp.ClientSession._request = observed_request
threading.Thread(target=report_processes, daemon=True).start()
print('DIAGNOSTIC environment keys', sorted(os.environ), flush=True)
exit_code = pytest.main([sys.argv[1], '-q'])
for process in processes:
	print('DIAGNOSTIC final', process.pid, 'returncode', process.returncode, flush=True)
sys.exit(exit_code)
