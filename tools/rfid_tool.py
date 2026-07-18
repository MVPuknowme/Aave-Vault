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
    requires_card_swap = False

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
    requires_card_swap = True

    UID_APDU = (0xFF, 0xCA, 0x00, 0x00, 0x00)
    READ_APDU = (0xFF, 0xB0, 0x00, 0x04, 0x10)
    WRITE_APDU_PREFIX = (0xFF, 0xD6, 0x00, 0x04, 0x10)

    def __init__(self, readers_provider=None):
        if readers_provider is None:
            try:
                from smartcard.System import readers
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError('pyscard is required for --backend pcsc') from exc
            readers_provider = readers

        self._readers = readers_provider

    @staticmethod
    def _transmit(connection, apdu, operation: str) -> bytes:
        response, sw1, sw2 = connection.transmit(list(apdu))
        if (sw1, sw2) != (0x90, 0x00):
            raise RuntimeError(f'{operation} failed: SW={sw1:02X}{sw2:02X}')
        return bytes(response)

    def _connect(self, expected_uid: str):
        expected_uid = normalize_uid(expected_uid)
        reader_list = self._readers()
        if not reader_list:
            raise RuntimeError('no PC/SC reader found')

        connection = reader_list[0].createConnection()
        connection.connect()
        uid_bytes = self._transmit(connection, self.UID_APDU, 'card UID read')
        actual_uid = normalize_uid(binascii.hexlify(uid_bytes).decode())
        if actual_uid != expected_uid:
            raise RuntimeError(
                f'card UID mismatch: expected {expected_uid}, found {actual_uid}'
            )
        return connection

    def read(self, uid: str) -> bytes:
        connection = self._connect(uid)
        # APDU for MIFARE Classic block read (block 4). Authentication is reader/card specific.
        return self._transmit(connection, self.READ_APDU, 'card read')

    def write(self, uid: str, payload: bytes) -> None:
        if len(payload) > 16:
            raise ValueError('pcsc backend currently writes max 16 bytes (1 block)')
        payload = payload.ljust(16, b'\x00')
        connection = self._connect(uid)
        apdu = self.WRITE_APDU_PREFIX + tuple(payload)
        self._transmit(connection, apdu, 'card write')


def normalize_uid(uid: str) -> str:
    normalized = uid.replace(':', '').replace('-', '').replace(' ', '').upper()
    if not normalized:
        raise ValueError('UID cannot be empty')
    if len(normalized) % 2:
        raise ValueError('UID must contain an even number of hexadecimal characters')
    if any(character not in '0123456789ABCDEF' for character in normalized):
        raise ValueError('UID must contain only hexadecimal characters')
    return normalized


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
        if source == target:
            raise ValueError('source and target UIDs must differ')

        payload = backend.read(source)
        if backend.requires_card_swap:
            input(f'Present target tag {target} and press Enter to continue...')
        backend.write(target, payload)
        print(f'copied {len(payload)} bytes from {source} to {target}')
        return 0

    return 1


if __name__ == '__main__':
    raise SystemExit(main())
