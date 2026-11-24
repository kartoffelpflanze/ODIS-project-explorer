import unittest

from tests import script_stubs  # noqa: F401
import parseMWB


# Regression tests for the physical SCALE-CONSTR branch of get_dop_value in parseMWB.py.


def _limit(kind, value=None):
    return {'type': kind, 'value': value}


def _dop(validity, description):
    return {'type': 'DOP', 'coded_base_data_type': 'A_UINT32', 'diag_coded_type': 'STANDARD-LENGTH-TYPE',
            'bit_length': 8, 'bit_mask': None, 'encoding': 'NONE', 'endianness': 'big',
            'physical_base_data_type': 'A_UINT32', 'display_radix': 10, 'precision': None,
            'calculation_type': None, 'compu_category': 'IDENTICAL', 'units': None, 'internal_constraint': None,
            'physical_constraint': {'lower_limit': _limit('INFINITE'), 'upper_limit': _limit('INFINITE'),
                                    'scale_constraints': [{'lower_limit': _limit('CLOSED', 250),
                                                           'upper_limit': _limit('CLOSED', 255),
                                                           'validity': validity, 'short_label': 'Inv',
                                                           'description': description}]}}


class ParseMwbPhysicalScaleConstraintTest(unittest.TestCase):
    def test_invalid_physical_scale_constraint_raises_runtime_error(self):
        with self.assertRaisesRegex(RuntimeError, r'^Physical value 254 falls in SCALE-CONSTR with validity NOT-VALID \(Label Inv, DESC Signal invalid\)$'):
            parseMWB.get_dop_value(_dop('NOT-VALID', 'Signal invalid'), bytearray([0xFE]), 0)

    def test_invalid_physical_scale_constraint_without_description(self):
        with self.assertRaisesRegex(RuntimeError, r'\(Label Inv, DESC None\)$'):
            parseMWB.get_dop_value(_dop('NOT-VALID', None), bytearray([0xFE]), 0)

    def test_value_outside_scale_constraint_is_returned(self):
        self.assertEqual(parseMWB.get_dop_value(_dop('NOT-VALID', None), bytearray([0x07]), 0), (7, 7, '7'))

    def test_valid_scale_constraint_does_not_raise(self):
        self.assertEqual(parseMWB.get_dop_value(_dop('VALID', None), bytearray([0xFE]), 0), (254, 254, '254'))


if __name__ == '__main__':
    unittest.main()
