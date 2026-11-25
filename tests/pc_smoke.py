#!/usr/bin/env python3
"""Run the real PC app and UDP framing, then the real SDL gamepad fixture."""
import json
import os
from pathlib import Path
import re
import socket
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run():
    environment = {**os.environ, 'SDL_VIDEO_DRIVER': 'offscreen'}
    with tempfile.TemporaryDirectory() as work, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
        receiver.bind(('127.0.0.1', 0)); receiver.settimeout(2)
        port = receiver.getsockname()[1]
        Path(work, 'net_log.txt').write_text(f'127.0.0.1 {port}\n')
        normal = subprocess.run([str(ROOT / 'build/pc/hello'), '--frames', '10'], cwd=work,
                                env=environment, capture_output=True, text=True, timeout=15, check=True)
        required = ['hello: startup;', 'hello: first frame submitted', 'hello: normal exit; frames=10']
        for message in required:
            if message not in normal.stdout: raise AssertionError(f'Missing app log: {message}')
        packets = [receiver.recvfrom(65535)[0] for _ in range(3)]
        if [struct.unpack('!I', packet[:4])[0] for packet in packets] != [0, 1, 2]:
            raise AssertionError('Application UDP sequence header is wrong')
        for message, packet in zip(required, packets):
            if message not in packet[4:].decode(): raise AssertionError('Application UDP text is wrong')
        # Remove the destination so the input test doesn't fill the same socket.
        Path(work, 'net_log.txt').unlink()
        inputs = subprocess.run([str(ROOT / 'build/pc/hello-input-check')], cwd=work,
                                env=environment, capture_output=True, text=True, timeout=15, check=True)
        for message in ['gamepad: connected', 'button 0 down', 'button 0 up', 'hello: B exit']:
            if message not in inputs.stdout: raise AssertionError(f'Missing real SDL input event: {message}')
        frames = int(re.search(r'normal exit; frames=(\d+)', inputs.stdout)[1])
        if not 0 < frames < 600: raise AssertionError('Input test reached the frame limit instead of exiting by B')
    print(normal.stdout, end=''); print(inputs.stdout, end='')
    print(json.dumps({'pc_vulkan_frames': 10, 'udp_sequences': [0, 1, 2], 'sdl_virtual_gamepad_A_B': 'passed',
                      'input_exit_frames': frames, 'real_console_test': 'pending'}))


if __name__ == '__main__': run()
