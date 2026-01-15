import unittest

from integration_service.domain.mappers.cert.dto_enum_mapper import (
    CERT_STATE_DTO_MAP,
    to_dto_cert_state
)
from integration_service.api.models.cert_state import CertState
from integration_service.domain.exceptions import MissingCertState


class TestCertStateMapper(unittest.TestCase):

    def test_to_dto_cert_state_maps_pending(self):
        result = to_dto_cert_state('PENDING')
        self.assertEqual(result, CertState.PENDING)

    def test_to_dto_cert_state_maps_assigned(self):
        result = to_dto_cert_state('ASSIGNED')
        self.assertEqual(result, CertState.ASSIGNED)

    def test_to_dto_cert_state_maps_active(self):
        result = to_dto_cert_state('ACTIVE')
        self.assertEqual(result, CertState.ACTIVE)

    def test_to_dto_cert_state_maps_expired(self):
        result = to_dto_cert_state('EXPIRED')
        self.assertEqual(result, CertState.EXPIRED)

    def test_to_dto_cert_state_maps_revoked(self):
        result = to_dto_cert_state('REVOKED')
        self.assertEqual(result, CertState.REVOKED)

    def test_to_dto_cert_state_maps_orphaned(self):
        result = to_dto_cert_state('ORPHANED')
        self.assertEqual(result, CertState.ORPHANED)

    def test_to_dto_cert_state_raises_exception_for_unknown_state(self):
        with self.assertRaises(MissingCertState) as context:
            to_dto_cert_state('UNKNOWN_STATE')

        self.assertIn('UNKNOWN_STATE', str(context.exception))

    def test_to_dto_cert_state_raises_exception_for_lowercase(self):
        with self.assertRaises(MissingCertState):
            to_dto_cert_state('pending')

    def test_to_dto_cert_state_raises_exception_for_mixed_case(self):
        with self.assertRaises(MissingCertState):
            to_dto_cert_state('Pending')

    def test_to_dto_cert_state_raises_exception_for_empty_string(self):
        with self.assertRaises(MissingCertState):
            to_dto_cert_state('')

    def test_to_dto_cert_state_raises_exception_for_invalid_state(self):
        invalid_states = ['INACTIVE', 'DISABLED', 'DELETED', 'UNKNOWN']

        for invalid_state in invalid_states:
            with self.assertRaises(MissingCertState):
                to_dto_cert_state(invalid_state)

    def test_cert_state_dto_map_contains_all_states(self):
        expected_states = ['PENDING', 'ASSIGNED', 'ACTIVE', 'EXPIRED', 'REVOKED', 'ORPHANED']

        for state in expected_states:
            self.assertIn(state, CERT_STATE_DTO_MAP)

    def test_cert_state_dto_map_has_correct_size(self):
        self.assertEqual(len(CERT_STATE_DTO_MAP), 6)

    def test_cert_state_dto_map_values_are_cert_state_enum(self):
        for value in CERT_STATE_DTO_MAP.values():
            self.assertIsInstance(value, CertState)

    def test_to_dto_cert_state_with_all_valid_states(self):
        valid_mappings = {
            'PENDING': CertState.PENDING,
            'ASSIGNED': CertState.ASSIGNED,
            'ACTIVE': CertState.ACTIVE,
            'EXPIRED': CertState.EXPIRED,
            'REVOKED': CertState.REVOKED,
            'ORPHANED': CertState.ORPHANED
        }

        for domain_state, expected_dto in valid_mappings.items():
            result = to_dto_cert_state(domain_state)
            self.assertEqual(result, expected_dto)

    def test_to_dto_cert_state_raises_exception_for_whitespace(self):
        with self.assertRaises(MissingCertState):
            to_dto_cert_state('PENDING ')

        with self.assertRaises(MissingCertState):
            to_dto_cert_state(' PENDING')

        with self.assertRaises(MissingCertState):
            to_dto_cert_state(' PENDING ')

    def test_to_dto_cert_state_exception_message_includes_state(self):
        invalid_state = 'INVALID_STATE'

        with self.assertRaises(MissingCertState) as context:
            to_dto_cert_state(invalid_state)

        self.assertIn(invalid_state, str(context.exception))

    def test_cert_state_dto_map_keys_are_uppercase(self):
        for key in CERT_STATE_DTO_MAP.keys():
            self.assertEqual(key, key.upper())

    def test_to_dto_cert_state_is_case_sensitive(self):
        self.assertEqual(to_dto_cert_state('PENDING'), CertState.PENDING)

        with self.assertRaises(MissingCertState):
            to_dto_cert_state('pending')

        with self.assertRaises(MissingCertState):
            to_dto_cert_state('Pending')

    def test_to_dto_cert_state_with_special_characters_raises_exception(self):
        invalid_inputs = ['PENDING!', 'ACTIVE@', 'REVOKED#', 'PENDING-STATE']

        for invalid_input in invalid_inputs:
            with self.assertRaises(MissingCertState):
                to_dto_cert_state(invalid_input)

    def test_cert_state_dto_map_has_no_duplicate_values(self):
        values = list(CERT_STATE_DTO_MAP.values())
        unique_values = set(values)

        self.assertEqual(len(values), len(unique_values))

    def test_to_dto_cert_state_with_numeric_input_raises_exception(self):
        with self.assertRaises(MissingCertState):
            to_dto_cert_state('123')

    def test_to_dto_cert_state_lifecycle_states(self):
        lifecycle_states = ['PENDING', 'ASSIGNED', 'ACTIVE', 'REVOKED']

        for state in lifecycle_states:
            result = to_dto_cert_state(state)
            self.assertIsInstance(result, CertState)

    def test_to_dto_cert_state_terminal_states(self):
        terminal_states = ['EXPIRED', 'REVOKED', 'ORPHANED']

        for state in terminal_states:
            result = to_dto_cert_state(state)
            self.assertIsInstance(result, CertState)