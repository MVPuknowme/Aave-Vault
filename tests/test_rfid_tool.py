import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from tools import rfid_tool


class FakeConnection:
    def __init__(self, uid='04AABBCCDD', payload=b'payload', uid_status=(0x90, 0x00)):
        self.uid = bytes.fromhex(uid)
        self.payload = payload
        self.uid_status = uid_status
        self.connected = False
        self.transmissions = []

    def connect(self):
        self.connected = True

    def transmit(self, apdu):
        self.transmissions.append(apdu)
        if apdu == list(rfid_tool.PcscBackend.UID_APDU):
            return list(self.uid), *self.uid_status
        if apdu == list(rfid_tool.PcscBackend.READ_APDU):
            return list(self.payload), 0x90, 0x00
        if apdu[:5] == list(rfid_tool.PcscBackend.WRITE_APDU_PREFIX):
            return [], 0x90, 0x00
        raise AssertionError(f'unexpected APDU: {apdu}')


class FakeReader:
    def __init__(self, connection):
        self.connection = connection

    def createConnection(self):
        return self.connection


def backend_for(connection):
    return rfid_tool.PcscBackend(lambda: [FakeReader(connection)])


class NormalizeUidTests(unittest.TestCase):
    def test_normalizes_common_separators_and_case(self):
        self.assertEqual(rfid_tool.normalize_uid('04:aa-bb cc:dd'), '04AABBCCDD')

    def test_rejects_malformed_uids(self):
        for uid in ('', 'ABC', '04AAXX'):
            with self.subTest(uid=uid), self.assertRaises(ValueError):
                rfid_tool.normalize_uid(uid)


class PcscBackendTests(unittest.TestCase):
    def test_read_checks_matching_uid_before_reading_data(self):
        connection = FakeConnection(payload=b'hello')

        payload = backend_for(connection).read('04-aa-bb-cc-dd')

        self.assertEqual(payload, b'hello')
        self.assertEqual(
            connection.transmissions,
            [
                list(rfid_tool.PcscBackend.UID_APDU),
                list(rfid_tool.PcscBackend.READ_APDU),
            ],
        )

    def test_read_rejects_wrong_card_without_reading_data(self):
        connection = FakeConnection(uid='0499887766')

        with self.assertRaisesRegex(
            RuntimeError,
            'card UID mismatch: expected 04AABBCCDD, found 0499887766',
        ):
            backend_for(connection).read('04AABBCCDD')

        self.assertEqual(
            connection.transmissions,
            [list(rfid_tool.PcscBackend.UID_APDU)],
        )

    def test_write_rejects_wrong_card_without_writing_data(self):
        connection = FakeConnection(uid='0499887766')

        with self.assertRaises(RuntimeError):
            backend_for(connection).write('04AABBCCDD', b'hello')

        self.assertEqual(
            connection.transmissions,
            [list(rfid_tool.PcscBackend.UID_APDU)],
        )

    def test_write_checks_uid_and_pads_one_block(self):
        connection = FakeConnection()

        backend_for(connection).write('04AABBCCDD', b'hello')

        self.assertEqual(connection.transmissions[0], list(rfid_tool.PcscBackend.UID_APDU))
        self.assertEqual(
            connection.transmissions[1],
            list(rfid_tool.PcscBackend.WRITE_APDU_PREFIX) + list(b'hello'.ljust(16, b'\x00')),
        )

    def test_uid_read_failure_reports_status(self):
        connection = FakeConnection(uid_status=(0x63, 0x00))

        with self.assertRaisesRegex(RuntimeError, 'card UID read failed: SW=6300'):
            backend_for(connection).read('04AABBCCDD')

    def test_missing_reader_is_rejected(self):
        backend = rfid_tool.PcscBackend(lambda: [])

        with self.assertRaisesRegex(RuntimeError, 'no PC/SC reader found'):
            backend.read('04AABBCCDD')


class RecordingBackend(rfid_tool.RFIDBackend):
    requires_card_swap = True

    def __init__(self):
        self.calls = []

    def read(self, uid):
        self.calls.append(('read', uid))
        return b'copied data'

    def write(self, uid, data):
        self.calls.append(('write', uid, data))


class CopyCommandTests(unittest.TestCase):
    def test_pcsc_copy_prompts_for_target_between_read_and_write(self):
        backend = RecordingBackend()
        argv = [
            'rfid_tool.py',
            '--backend',
            'pcsc',
            'copy',
            '--source',
            '04AABBCCDD',
            '--target',
            '0499887766',
        ]

        with (
            patch.object(sys, 'argv', argv),
            patch.object(rfid_tool, 'build_backend', return_value=backend),
            patch('builtins.input') as prompt,
            redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(rfid_tool.main(), 0)

        prompt.assert_called_once_with(
            'Present target tag 0499887766 and press Enter to continue...'
        )
        self.assertEqual(
            backend.calls,
            [
                ('read', '04AABBCCDD'),
                ('write', '0499887766', b'copied data'),
            ],
        )

    def test_copy_rejects_identical_source_and_target(self):
        backend = RecordingBackend()
        argv = [
            'rfid_tool.py',
            'copy',
            '--source',
            '04AABBCCDD',
            '--target',
            '04-aa-bb-cc-dd',
        ]

        with (
            patch.object(sys, 'argv', argv),
            patch.object(rfid_tool, 'build_backend', return_value=backend),
            self.assertRaisesRegex(ValueError, 'source and target UIDs must differ'),
        ):
            rfid_tool.main()

        self.assertEqual(backend.calls, [])


if __name__ == '__main__':
    unittest.main()
