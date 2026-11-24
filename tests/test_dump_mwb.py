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


if __name__ == '__main__':
    unittest.main()
