#!/usr/bin/env python3
"""RFID read/write/copy utility.

This CLI supports two backends:
1. mock (default): stores tag data in a local JSON file for development/testing.
2. pcsc: reads/writes MIFARE Classic blocks through a PC/SC-compatible reader.

Examples:
  python tools/rfid_tool.py read --uid 04AABBCCDD
  python tools/rfid_tool.py write --uid 04AABBCCDD --data "hello"
  python tools/rfid_tool.py copy --source 04AABBCCDD --target 0499887766
"""

from __future__ import annotations

import argparse
import binascii
import json
from pathlib import Path
from typing import Dict

STORE_PATH = Path('.rfid_tags.json')


class RFIDBackend:
    def read(self, uid: str) -> bytes:
        raise NotImplementedError

    def write(self, uid: str, data: bytes) -> None:
        raise NotImplementedError


class MockBackend(RFIDBackend):
    def __init__(self, store_path: Path = STORE_PATH):
        self.store_path = store_path

    def _load(self) -> Dict[str, str]:
        if not self.store_path.exists():
            return {}
        return json.loads(self.store_path.read_text())

    def _save(self, data: Dict[str, str]) -> None:
        self.store_path.write_text(json.dumps(data, indent=2, sort_keys=True))

    def read(self, uid: str) -> bytes:
        data = self._load()
        if uid not in data:
            raise KeyError(f'tag {uid} not found')
        return binascii.unhexlify(data[uid])

    def write(self, uid: str, payload: bytes) -> None:
        data = self._load()
        data[uid] = binascii.hexlify(payload).decode()
        self._save(data)


class PcscBackend(RFIDBackend):
    def __init__(self):
        try:
            from smartcard.System import readers
            from smartcard.util import toHexString
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError('pyscard is required for --backend pcsc') from exc

        self._readers = readers
        self._to_hex = toHexString

    def _connect(self):
        reader_list = self._readers()
        if not reader_list:
            raise RuntimeError('no PC/SC reader found')
        connection = reader_list[0].createConnection()
        connection.connect()
        return connection

    def read(self, uid: str) -> bytes:
        connection = self._connect()
        # APDU for MIFARE Classic block read (block 4). Authentication is reader/card specific.
        apdu = [0xFF, 0xB0, 0x00, 0x04, 0x10]
        response, sw1, sw2 = connection.transmit(apdu)
        if (sw1, sw2) != (0x90, 0x00):
            raise RuntimeError(f'card read failed: SW={sw1:02X}{sw2:02X}')
        return bytes(response)

    def write(self, uid: str, payload: bytes) -> None:
        if len(payload) > 16:
            raise ValueError('pcsc backend currently writes max 16 bytes (1 block)')
        payload = payload.ljust(16, b'\x00')
        connection = self._connect()
        apdu = [0xFF, 0xD6, 0x00, 0x04, 0x10] + list(payload)
        _, sw1, sw2 = connection.transmit(apdu)
        if (sw1, sw2) != (0x90, 0x00):
            raise RuntimeError(f'card write failed: SW={sw1:02X}{sw2:02X}')


def normalize_uid(uid: str) -> str:
    return uid.replace(':', '').replace('-', '').upper()


def parse_data(raw: str, encoding: str) -> bytes:
    if encoding == 'hex':
        return binascii.unhexlify(raw)
    return raw.encode()


def build_backend(name: str) -> RFIDBackend:
    if name == 'mock':
        return MockBackend()
    if name == 'pcsc':
        return PcscBackend()
    raise ValueError(f'unsupported backend {name}')


def main() -> int:
    parser = argparse.ArgumentParser(description='RFID copy/read/write tool')
    parser.add_argument('--backend', choices=['mock', 'pcsc'], default='mock')

    subparsers = parser.add_subparsers(dest='command', required=True)

    read_parser = subparsers.add_parser('read', help='Read tag payload')
    read_parser.add_argument('--uid', required=True)
    read_parser.add_argument('--format', choices=['hex', 'text'], default='text')

    write_parser = subparsers.add_parser('write', help='Write payload to tag')
    write_parser.add_argument('--uid', required=True)
    write_parser.add_argument('--data', required=True)
    write_parser.add_argument('--encoding', choices=['text', 'hex'], default='text')

    copy_parser = subparsers.add_parser('copy', help='Copy payload from source tag to target tag')
    copy_parser.add_argument('--source', required=True)
    copy_parser.add_argument('--target', required=True)

    args = parser.parse_args()
    backend = build_backend(args.backend)

    if args.command == 'read':
        payload = backend.read(normalize_uid(args.uid))
        if args.format == 'hex':
            print(binascii.hexlify(payload).decode())
        else:
            print(payload.decode(errors='replace'))
        return 0

    if args.command == 'write':
        uid = normalize_uid(args.uid)
        payload = parse_data(args.data, args.encoding)
        backend.write(uid, payload)
        print(f'wrote {len(payload)} bytes to {uid}')
        return 0

    if args.command == 'copy':
        source = normalize_uid(args.source)
        target = normalize_uid(args.target)
        payload = backend.read(source)
        backend.write(target, payload)
        print(f'copied {len(payload)} bytes from {source} to {target}')
        return 0

    return 1


if __name__ == '__main__':
    raise SystemExit(main())
