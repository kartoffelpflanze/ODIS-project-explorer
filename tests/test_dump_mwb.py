import unittest

from tests import script_stubs  # noqa: F401
import dumpMWB


class FailingObjectLoader:
    def load_DOP_by_reference_without_PoolID(self, project_folder_path, layer_data_objects, db_object_ref):
        raise RuntimeError('DOP not found')


class ParseDopValueParameterTest(unittest.TestCase):
    def test_value_without_dop_reference_gets_error_marker(self):
        dop = {
            '#OBJECT_TYPE': 'MCD_DB_PARAMETER',
            'long_name': 'Parameter',
            'long_name_id': None,
            'description': None,
            'is_byte_pos_available': False,
            'bit_position': 0,
            'mcd_parameter_type': 'eVALUE',
            'default_mcd_value': None,
            'db_object_ref': None,
        }

        out = dumpMWB.parse_dop(FailingObjectLoader(), [], 'project', dop)

        self.assertEqual(out['dop'], {'#error': 'Access to database element failed - DOP with name: None'})


class FakeObjectLoader:
    """Serves referenced objects (constraints, units) from a plain dict."""

    def __init__(self, objects=None):
        self.objects = objects or {}

    def load_object_by_reference(self, project_folder_path, ref):
        return self.objects[ref]


def make_limit(data_type, value=0):
    return {'data_type': data_type, 'value': value}


def make_interval(lower_type='eA_UINT32', upper_type='eA_UINT32'):
    return {
        'lower_limit': make_limit(lower_type, 0),
        'lower_limit_type': 'eLIMIT_CLOSED',
        'upper_limit': make_limit(upper_type, 255),
        'upper_limit_type': 'eLIMIT_CLOSED',
    }


def make_scale_constraint(interval):
    return {
        'interval': interval,
        'range_info': 'eRANGE_VALID',
        'short_label': None,
        'description': None,
    }


def make_internal_constraint(interval, scale_constraints=()):
    return {
        'is_computed': False,
        'interval': interval,
        'scale_constraints': list(scale_constraints),
    }


def make_simple_dop(coded_type='eA_UINT32', **overrides):
    """Build a minimal DB_DOP_SIMPLE_BASE object; keyword arguments override or add fields."""
    dop = {
        '#OBJECT_TYPE': 'DB_DOP_SIMPLE_BASE',
        'diag_coded_type': {
            'is_condensed': False,
            'base_data_type_as_mcd_data_type': coded_type,
            'type': 'eSTANDARD_LENGTH_TYPE',
            'bit_length': 32,
            'bit_mask': bytearray(),
            'encoding': 'eNONE',
            'is_high_low_byte_order': True,
        },
        'compu_method': {
            'compu_category': 'eIDENTICAL',
            'compu_internal_to_phys': None,
            'compu_phys_to_internal': None,
        },
    }
    dop.update(overrides)
    return dop


def parse_simple_dop(dop, objects=None):
    return dumpMWB.parse_dop(FakeObjectLoader(objects), [], 'project', dop)


class ParseDopInternalConstraintTest(unittest.TestCase):
    def test_internal_constraint_upper_limit_type_is_checked(self):
        constraint = make_internal_constraint(make_interval('eA_UINT32', 'eA_INT32'))
        dop = make_simple_dop(internal_constraint_ref='ic')

        with self.assertRaisesRegex(RuntimeError, r'^IC limit data types do not match coded type: eA_UINT32, eA_INT32 vs A_UINT32$'):
            parse_simple_dop(dop, {'ic': constraint})

    def test_scale_constraint_upper_limit_type_is_checked(self):
        constraint = make_internal_constraint(
            make_interval(),
            [make_scale_constraint(make_interval('eA_UINT32', 'eA_INT32'))])
        dop = make_simple_dop(internal_constraint_ref='ic')

        with self.assertRaisesRegex(RuntimeError, r'^IC SCALE-CONSTR limit data types do not match coded type: eA_UINT32, eA_INT32 vs A_UINT32$'):
            parse_simple_dop(dop, {'ic': constraint})

    def test_internal_constraint_matching_types_pass(self):
        constraint = make_internal_constraint(
            make_interval(),
            [make_scale_constraint(make_interval())])
        dop = make_simple_dop(internal_constraint_ref='ic')

        out = parse_simple_dop(dop, {'ic': constraint})

        self.assertEqual(out['internal_constraint']['upper_limit']['type'], 'CLOSED')
        self.assertEqual(out['internal_constraint']['scale_constraints'][0]['upper_limit']['type'], 'CLOSED')


class ParseDopCalculationTypeTest(unittest.TestCase):
    def test_texttab_has_no_calculation_type(self):
        scale = {
            'lower_limit_as_coded_value': {'limit_type': 'eLIMIT_CLOSED', 'mcd_value': make_limit('eA_UINT32', 0)},
            'upper_limit_as_coded_value': {'limit_type': 'eLIMIT_CLOSED', 'mcd_value': make_limit('eA_UINT32', 0)},
            'compu_const': make_limit('eA_UNICODE2STRING', 'off'),
            'long_name_id': None,
        }
        dop = make_simple_dop(
            physical_type={
                'base_data_type_as_mcd_data_type': 'eA_UNICODE2STRING',
                'display_radix': 10,
                'is_precision_available': False,
                'precision': 0,
            },
            compu_method={
                'compu_category': 'eTEXTTAB',
                'compu_internal_to_phys': {'compu_scales': [scale], 'compu_default_value': None},
                'compu_phys_to_internal': None,
            })

        out = parse_simple_dop(dop)

        self.assertIsNone(out['calculation_type'])
        self.assertEqual(out['compu_category'], 'TEXTTABLE')

    def test_identical_has_no_calculation_type(self):
        out = parse_simple_dop(make_simple_dop())

        self.assertIsNone(out['calculation_type'])


if __name__ == '__main__':
    unittest.main()
