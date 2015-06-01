# -*- coding: utf-8 -*-
"""
    test_nereid_s3

    Test Nereid-S3

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import unittest

from mock import patch
from boto.s3 import connection
from boto.s3.bucket import Bucket
from boto.s3.key import Key
import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT, test_view,\
    test_depends
from trytond.transaction import Transaction
from trytond.exceptions import UserError


class TestNereidS3(unittest.TestCase):
    '''
    Test Nereid S3
    '''

    def setUp(self):
        trytond.tests.test_tryton.install_module('nereid_s3')
        self.static_file = POOL.get('nereid.static.file')
        self.static_folder = POOL.get('nereid.static.folder')

        # Mock S3Connection
        self.s3_api_patcher = patch(
            'boto.s3.connection.S3Connection', autospec=True
        )
        PatchedS3 = self.s3_api_patcher.start()

        # Mock S3Key
        self.s3_key_patcher = patch(
            'boto.s3.key.Key', autospec=True
        )
        PatchedS3Key = self.s3_key_patcher.start()

        PatchedS3.return_value = connection.S3Connection('ABCD', '123XYZ')
        PatchedS3.return_value.get_bucket = lambda bucket_name: Bucket(
            PatchedS3.return_value, 'tryton-test-s3'
        )

        PatchedS3Key.return_value = Key(
            Bucket(PatchedS3.return_value, 'tryton-test-s3'), 'some key'
        )
        PatchedS3Key.return_value.key = "some key"
        PatchedS3Key.return_value.get_contents_as_string = lambda *a: 'testfile'
        PatchedS3Key.return_value.set_contents_from_string = \
            lambda value: 'testfile'

    def tearDown(self):
        self.s3_api_patcher.stop()
        self.s3_key_patcher.stop()

    def test0005views(self):
        '''
        Test views.
        '''
        test_view('nereid_s3')

    def test0006depends(self):
        '''
        Test depends.
        '''
        test_depends()

    def test0010_static_file(self):
        """
        Checks that file is saved to amazon s3
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):

            # Create folder for amazon s3
            folder, = self.static_folder.create([{
                'folder_name': 's3store',
                'description': 'S3 Folder',
                's3_use_bucket': True,
                's3_access_key': 'ABCD',
                's3_secret_key': '123XYZ',
                's3_bucket_name': 'tryton-test-s3',
                's3_cloudfront_cname': 'http://test.cloudfront.net',
            }])
            self.assert_(folder.id)

            s3_folder = self.static_folder.search([
                ('s3_use_bucket', '=', True)
            ])[0]

            # Create static file for amazon s3 bucket
            file, = self.static_file.create([{
                'name': 'testfile.png',
                'type': 's3',
                'folder': s3_folder,
                'file_binary': buffer('testfile')
            }])
            self.assert_(file.id)

            self.assertEqual(
                file.file_binary, buffer('testfile')
            )

    def test0020_static_folder_with_invalid_cname(self):
        """
        Checks if error is raised for cname ending with '/'
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            # Create folder for amazon s3 with cname that ends with '/'
            self.assertRaises(
                UserError, self.static_folder.create, [{
                    'folder_name': 's3store',
                    'description': 'S3 Folder',
                    's3_use_bucket': True,
                    's3_access_key': 'ABCD',
                    's3_secret_key': '123XYZ',
                    's3_bucket_name': 'tryton-test-s3',
                    's3_cloudfront_cname': 'http://test.cloudfront.net/',
                }]
            )


def suite():
    """
    Define Test suite
    """
    test_suite = trytond.tests.test_tryton.suite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestNereidS3)
    )
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
