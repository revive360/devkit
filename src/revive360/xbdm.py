"""XBDM client, adapted from Pedro's forcepush-360/tools/xbdm.py (MIT here).

Only explicit commands access a console. There is deliberately no reboot or raw
command interface. UDP logging does not open an XBDM connection.
"""
import argparse
import concurrent.futures
import ipaddress
import json
import ntpath
from pathlib import Path
import re
import socket
import struct
import sys


class XbdmError(Exception):
    pass


def remote_path(value):
    if any(c in value for c in '"\r\n\0'):
        raise ValueError('Remote paths cannot contain quotes or control delimiters')
    value = value.replace('/', '\\')
    if not re.match(r'^[A-Za-z][A-Za-z0-9]*:\\', value):
        raise ValueError('Use an absolute console path, e.g. HDD:\\Apps\\Hello\\default.xex')
    drive, path = value.split(':', 1)
    drive = 'HDD' if drive.upper() in ('HDD', 'HDD1') else drive.upper()
    return ntpath.normpath(drive + ':' + path)


class Xbdm:
    def __init__(self, host, port=730, timeout=8):
        self.socket = socket.create_connection((host, port), timeout=timeout)
        try:
            self.expect(201)
        except BaseException:
            self.socket.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.socket.close()

    def line(self):
        data = bytearray()
        while len(data) < 65536:
            byte = self.socket.recv(1)
            if not byte:
                raise XbdmError('Connection closed before CRLF')
            data += byte
            if data.endswith(b'\r\n'):
                return bytes(data[:-2])
        raise XbdmError('Status line exceeds 64 KiB')

    def exact(self, length):
        data = bytearray()
        while len(data) < length:
            part = self.socket.recv(min(65536, length - len(data)))
            if not part:
                raise XbdmError('Connection closed during binary transfer')
            data += part
        return bytes(data)

    def expect(self, wanted):
        line = self.line().decode('latin-1')
        if not re.match(r'^\d{3}[ -]', line):
            raise XbdmError(f'Invalid status: {line!r}')
        code = int(line[:3])
        if code != wanted:
            raise XbdmError(f'Expected {wanted}, got {line}')
        return line[4:].lstrip('- ')

    def send(self, command):
        if '\r' in command or '\n' in command or '\0' in command:
            raise ValueError('Invalid command delimiter')
        self.socket.sendall(command.encode('latin-1') + b'\r\n')

    def listing(self, remote):
        self.send(f'dirlist name="{remote_path(remote)}"')
        self.expect(202)
        lines = []
        while True:
            line = self.line()
            if line == b'.':
                return lines
            lines.append(line.decode('latin-1'))

    def mkdir(self, remote):
        self.send(f'mkdir name="{remote_path(remote)}"')
        # Never swallow 413: it can mean a running title prevents creation.
        try:
            self.expect(200)
        except XbdmError as error:
            if 'got 410' not in str(error):
                raise

    def put(self, local, remote):
        # Open before stat so the file we size is the one we stream.
        with Path(local).open('rb') as source:
            length = source.seek(0, 2)
            source.seek(0)
            self.send(f'sendfile name="{remote_path(remote)}" length=0x{length:x}')
            self.expect(204)
            remaining = length
            while remaining:
                chunk = source.read(min(65536, remaining))
                if not chunk:
                    raise XbdmError('Local file became shorter during transfer')
                self.socket.sendall(chunk)
                remaining -= len(chunk)
            self.expect(200)

    def get(self, remote, local):
        self.send(f'getfile name="{remote_path(remote)}"')
        self.expect(203)
        length = struct.unpack('<I', self.exact(4))[0]
        destination = Path(local)
        temporary = destination.with_name(destination.name + '.part')
        try:
            with temporary.open('wb') as output:
                while length:
                    chunk = self.exact(min(65536, length))
                    output.write(chunk)
                    length -= len(chunk)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)

    def run(self, remote):
        title = remote_path(remote)
        if not title.lower().endswith('.xex'):
            raise ValueError('run requires an absolute .xex path')
        folder = ntpath.dirname(title).rstrip('\\') + '\\'
        self.send(f'magicboot title="{title}" directory="{folder}"')
        # A title switch may close the connection without a status. Sending is
        # not proof that the title started; verify the screen and UDP startup log.

    def screenshot(self):
        self.send('screenshot')
        self.expect(203)
        header = self.line().decode('latin-1')
        fields = dict(re.findall(r'(\w+)=(0x[0-9a-fA-F]+|\d+)', header))
        info = {key: int(value, 0) for key, value in fields.items()}
        size = info.get('framebuffersize', info.get('pitch', 0) * info.get('height', 0))
        if not 0 < size <= 64 * 1024 * 1024:
            raise XbdmError(f'Invalid screenshot size: {header}')
        return info, self.exact(size)


def discover(network, timeout, port):
    net = ipaddress.ip_network(network, strict=False)
    if net.version != 4 or net.num_addresses > 256:
        raise ValueError('Discovery requires an explicit IPv4 /24 or smaller network')

    def probe(host):
        try:
            # Read the 201 greeting. Never send blank lines or test with /dev/tcp.
            with Xbdm(str(host), port=port, timeout=timeout):
                return str(host)
        except (OSError, XbdmError):
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        return [host for host in pool.map(probe, net.hosts()) if host]


def udp_log(bind, port, output=None, count=0):
    """xsdk datagrams start with a four-byte sequence number, in network order."""
    previous = {}
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listener:
        listener.bind((bind, port))
        print(f'UDP log listening on {bind}:{listener.getsockname()[1]}', flush=True)
        file = Path(output).open('a', encoding='utf-8') if output else None
        try:
            received = 0
            while not count or received < count:
                data, address = listener.recvfrom(65535)
                if len(data) < 4:
                    continue
                sequence = struct.unpack('!I', data[:4])[0]
                last = previous.get(address)
                gap = ''
                if last is not None and sequence != (last + 1) & 0xffffffff:
                    gap = f' [sequence gap/reset: previous={last}]'
                previous[address] = sequence
                line = f'{address[0]} seq={sequence}{gap} {data[4:].decode("utf-8", errors="replace").rstrip()}'
                print(line, flush=True)
                if file:
                    file.write(line + '\n')
                    file.flush()
                received += 1
        finally:
            if file:
                file.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    find = commands.add_parser('discover', help='Read greetings on an explicit local subnet')
    find.add_argument('--network', required=True)
    find.add_argument('--timeout', type=float, default=0.5)
    find.add_argument('--port', type=int, default=730)
    log = commands.add_parser('log', help='Receive UDP logs without connecting to a console')
    log.add_argument('--bind', default='0.0.0.0')
    log.add_argument('--port', type=int, default=7301)
    log.add_argument('--output')
    log.add_argument('--count', type=int, default=0, help='Stop after N datagrams; 0 waits until Ctrl+C')
    for name in ('ls', 'mkdir', 'put', 'get', 'run', 'shot'):
        command = commands.add_parser(name)
        command.add_argument('host')
        command.add_argument('--port', type=int, default=730)
        if name == 'put':
            command.add_argument('local')
        if name != 'shot':
            command.add_argument('remote')
        if name == 'get':
            command.add_argument('local')
        if name == 'shot':
            command.add_argument('output', help='Output prefix (.raw, .json, optional .png)')
            command.add_argument('--png', action='store_true')
            command.add_argument('--width', type=int)
            command.add_argument('--height', type=int)
    args = parser.parse_args(argv)
    try:
        if args.command == 'discover':
            found = discover(args.network, args.timeout, args.port)
            print('\n'.join(found) if found else 'No XBDM greeting found')
            return 0 if found else 1
        if args.command == 'log':
            if not 0 < args.port <= 65535 or args.count < 0:
                raise ValueError('Invalid UDP port or datagram count')
            udp_log(args.bind, args.port, args.output, args.count)
            return 0
        # Validate paths before making a connection.
        if hasattr(args, 'remote'):
            args.remote = remote_path(args.remote)
        with Xbdm(args.host, port=args.port) as client:
            if args.command == 'ls':
                print('\n'.join(client.listing(args.remote)))
            elif args.command in ('mkdir', 'put', 'get'):
                params = {'mkdir': (args.remote,), 'put': (getattr(args, 'local', None), args.remote),
                          'get': (args.remote, getattr(args, 'local', None))}
                getattr(client, args.command)(*params[args.command])
            elif args.command == 'run':
                client.run(args.remote)
                print('Launch command sent; verify the screen and startup log.')
            elif args.command == 'shot':
                info, raw = client.screenshot()
                Path(args.output + '.raw').write_bytes(raw)
                Path(args.output + '.json').write_text(json.dumps(info, indent=2) + '\n')
                if args.png:
                    from .screenshot import decode
                    decode(raw, info, args.width, args.height).save(args.output + '.png')
                print(f'Saved capture: {args.output}; verify dimensions before interpreting it.')
        return 0
    except (OSError, ValueError, XbdmError, ImportError) as error:
        print(f'xbdm: {error}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == '__main__':
    sys.exit(main())
