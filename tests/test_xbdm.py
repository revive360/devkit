"""Loopback protocol tests. These never scan or contact a real console."""
from contextlib import contextmanager
import io
import json
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import unittest

from revive360.xbdm import Xbdm, XbdmError, discover, main, remote_path


def line(connection):
    data = bytearray()
    while not data.endswith(b'\r\n'):
        chunk = connection.recv(1)
        if not chunk:
            raise AssertionError('client closed before command CRLF')
        data += chunk
    return bytes(data)


def exact(connection, length):
    data = bytearray()
    while len(data) < length:
        part = connection.recv(length - len(data))
        if not part:
            raise AssertionError('client truncated upload')
        data += part
    return bytes(data)


@contextmanager
def monitor(handler):
    errors = []
    with socket.create_server(('127.0.0.1', 0)) as server:
        server.settimeout(3)
        port = server.getsockname()[1]

        def serve():
            try:
                with server.accept()[0] as connection:
                    connection.settimeout(3)
                    # Deliberately fragment the greeting across writes.
                    connection.sendall(b'20')
                    connection.sendall(b'1- loopback XBDM\r\n')
                    handler(connection)
            except BaseException as error:
                errors.append(error)

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        try:
            yield port
        finally:
            thread.join(4)
            if thread.is_alive():
                raise AssertionError('loopback server did not finish')
            if errors:
                raise errors[0]


class ProtocolTests(unittest.TestCase):
    def test_listing_uses_hdd_alias_and_crlf(self):
        def handler(connection):
            self.assertEqual(line(connection), b'dirlist name="HDD:\\Apps"\r\n')
            connection.sendall(b'202- list\r\nname="default.xex" sizehi=0x0 sizelo=0x7\r\n.\r\n')
        with monitor(handler) as port, Xbdm('127.0.0.1', port) as client:
            self.assertEqual(client.listing('Hdd1:/Apps'), ['name="default.xex" sizehi=0x0 sizelo=0x7'])

    def test_upload_streams_exact_binary(self):
        data = bytes(range(256)) * 1024
        def handler(connection):
            self.assertEqual(line(connection), b'sendfile name="HDD:\\Apps\\a.xex" length=0x40000\r\n')
            connection.sendall(b'204- send data\r\n')
            self.assertEqual(exact(connection, len(data)), data)
            connection.sendall(b'200- written\r\n')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.xex'; path.write_bytes(data)
            with monitor(handler) as port, Xbdm('127.0.0.1', port) as client:
                client.put(path, 'HDD:/Apps/a.xex')

    def test_download_preserves_existing_file_on_disconnect(self):
        def handler(connection):
            self.assertEqual(line(connection), b'getfile name="HDD:\\a"\r\n')
            connection.sendall(b'203- data\r\n' + struct.pack('<I', 20) + b'too short')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'download'; path.write_bytes(b'keep me')
            with monitor(handler) as port, Xbdm('127.0.0.1', port) as client:
                with self.assertRaises(XbdmError): client.get('HDD:/a', path)
            self.assertEqual(path.read_bytes(), b'keep me')
            self.assertFalse(path.with_suffix('.part').exists())

    def test_download_length_prefix_is_little_endian(self):
        data = b'\x00\xff\r\nXEX2' * 40
        def handler(connection):
            self.assertEqual(line(connection), b'getfile name="HDD:\\a"\r\n')
            connection.sendall(b'203- data\r\n' + struct.pack('<I', len(data)) + data)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'download'
            with monitor(handler) as port, Xbdm('127.0.0.1', port) as client: client.get('HDD:/a', path)
            self.assertEqual(path.read_bytes(), data)

    def test_launch_sets_working_directory_and_never_reboots(self):
        def handler(connection):
            self.assertEqual(line(connection), b'magicboot title="HDD:\\Apps\\Hello\\default.xex" directory="HDD:\\Apps\\Hello\\"\r\n')
            self.assertEqual(connection.recv(1), b'')
        with monitor(handler) as port, Xbdm('127.0.0.1', port) as client:
            client.run('Hdd1:/Apps/Hello/default.xex')

    def test_mkdir_413_is_not_swallowed(self):
        def handler(connection):
            self.assertEqual(line(connection), b'mkdir name="HDD:\\Apps"\r\n')
            connection.sendall(b'413- cannot create\r\n')
        with monitor(handler) as port, Xbdm('127.0.0.1', port) as client:
            with self.assertRaises(XbdmError): client.mkdir('HDD:/Apps')

    def test_discovery_reads_greeting_without_sending_anything(self):
        def handler(connection): self.assertEqual(connection.recv(1), b'')
        with monitor(handler) as port:
            self.assertEqual(discover('127.0.0.1/32', 1, port), ['127.0.0.1'])
        with self.assertRaises(ValueError): discover('127.0.0.0/8', 1, 730)

    def test_screenshot_accepts_comma_separated_header(self):
        def handler(connection):
            self.assertEqual(line(connection), b'screenshot\r\n')
            connection.sendall(b'203- pixels\r\nwidth=0x1, height=0x1, pitch=0x4, framebuffersize=0x4, format=0x18280086\r\n\x30\x20\x10\xff')
        with monitor(handler) as port, Xbdm('127.0.0.1', port) as client:
            info, raw = client.screenshot()
            self.assertEqual(info['width'], 1)
            self.assertEqual(raw, b'\x30\x20\x10\xff')

    def test_remote_injection_and_relative_paths_rejected(self):
        for value in ('a.xex', 'HDD:a.xex', 'HDD:/x" reboot', 'HDD:/x\r\nmagicboot cold'):
            with self.subTest(value=value), self.assertRaises(ValueError): remote_path(value)
        self.assertEqual(remote_path('Hdd1:/'), 'HDD:\\')

    def test_removed_reboot_command_rejected_by_parser(self):
        from contextlib import redirect_stderr
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
            main(['reboot', '127.0.0.1'])
        self.assertEqual(result.exception.code, 2)

    def test_udp_cli_framing_and_sequence_gap(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as reserve:
            reserve.bind(('127.0.0.1', 0)); port = reserve.getsockname()[1]
        process = subprocess.Popen([sys.executable, '-m', 'revive360.xbdm', 'log', '--bind', '127.0.0.1',
                                    '--port', str(port), '--count', '2'], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        try:
            self.assertIn('UDP log listening', process.stdout.readline())
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
                for sequence, text in [(17, b'start'), (19, b'exit')]:
                    sender.sendto(struct.pack('!I', sequence) + text, ('127.0.0.1', port))
            output, error = process.communicate(timeout=4)
            self.assertEqual(process.returncode, 0, error)
            self.assertIn('seq=17 start', output)
            self.assertIn('seq=19 [sequence gap/reset: previous=17] exit', output)
        finally:
            if process.poll() is None: process.kill(); process.communicate()


class ScreenshotTests(unittest.TestCase):
    def test_known_linear_pixel_and_partial_capture(self):
        from revive360.screenshot import decode
        info = {'width':1, 'height':1, 'pitch':4, 'format':0x18280086}
        self.assertEqual(decode(b'\x30\x20\x10\xff', info).getpixel((0,0)), (16,32,48))
        with self.assertRaises(ValueError): decode(b'\x00', info)
        with self.assertRaises(ValueError): decode(b'\x00'*4, {**info, 'format':0})


if __name__ == '__main__': unittest.main()
