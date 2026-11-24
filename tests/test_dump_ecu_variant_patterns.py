import contextlib
import io
import os
import tempfile
import unittest

from tests import script_stubs  # noqa: F401
import dumpECUVariantPatterns


KWP_PARAMETER = 'MB_Identification_Read'
UDS_PARAMETER = 'DiagnServi_ReadDataByIdentASAMODXFileIdent'


class FakeObjectLoader:
    # variants: list of (name, [pattern, ...]); a pattern is a list of (primitive object ID, expected value)
    def __init__(self, variants):
        self.variants = dict(variants)

    def load_object_by_id(self, project_folder_path, pool_id, object_id):
        if object_id == '#RtGen_DB_PROJECT_DATA':
            return {
                'ecu_variant_ref_collection': [{'name': name, 'reference': name} for name in self.variants],
                'ecu_base_variant_ref': {'object_id': 'BV_Test'}
            }
        return {}

    def load_object_by_reference(self, project_folder_path, reference):
        patterns = self.variants[reference]
        return {
            'ecu': {'long_name': reference, 'description': None, 'short_name': reference},
            'matching_patterns': [
                {'matching_parameters': [
                    {'diag_com_primitive_ref': {'attrib_obj_ref': {'object_id': object_id}},
                     'expected_value_string': value}
                    for (object_id, value) in pattern
                ]}
                for pattern in patterns
            ]
        }


def _dump(variants):
    output_folder = tempfile.TemporaryDirectory()
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        dumpECUVariantPatterns.dump_patterns_for_base_variant(
            FakeObjectLoader(variants), 'project', 'BV_Test.bv.db', output_folder.name)
    return output_folder, stdout.getvalue()


class DumpPatternsKwpVariantTest(unittest.TestCase):
    def test_kwp_variant_does_not_stop_following_variants(self):
        output_folder, output = _dump([
            ('EV_Kwp', [[(KWP_PARAMETER, None)]]),
            ('EV_Uds', [[(UDS_PARAMETER, 'EV_Uds')]]),
        ])
        with output_folder:
            variant_folder = os.path.join(output_folder.name, 'BV_Test')
            self.assertTrue(os.path.isfile(os.path.join(variant_folder, 'PAT_EV_Uds.c')))
            self.assertFalse(os.path.exists(os.path.join(variant_folder, 'PAT_EV_Kwp.c')))
        self.assertIn('Not for UDS', output)

    def test_kwp_service_in_second_pattern_skips_only_that_variant(self):
        output_folder, output = _dump([
            ('EV_Mixed', [[(UDS_PARAMETER, 'EV_Mixed')], [('DCX_Identification_Read', None)]]),
            ('EV_Uds', [[(UDS_PARAMETER, 'EV_Uds')]]),
        ])
        with output_folder:
            variant_folder = os.path.join(output_folder.name, 'BV_Test')
            self.assertFalse(os.path.exists(os.path.join(variant_folder, 'PAT_EV_Mixed.c')))
            self.assertTrue(os.path.isfile(os.path.join(variant_folder, 'PAT_EV_Uds.c')))
        self.assertIn('Not for UDS', output)


if __name__ == '__main__':
    unittest.main()
