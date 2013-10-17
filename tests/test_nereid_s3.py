# -*- coding: utf-8 -*-
"""
    test_nereid_s3

    Test Nereid-S3

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""

import sys
import os
DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(__file__, '..', '..', '..', '..', '..', 'trytond')
    )
)
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT, test_view,\
    test_depends
from trytond.transaction import Transaction


class TestNereidS3(unittest.TestCase):
    '''
    Test Company module.
    '''

    def setUp(self):
        trytond.tests.test_tryton.install_module('nereid_s3')
        self.static_file = POOL.get('nereid.static.file')
        self.static_folder = POOL.get('nereid.static.folder')

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
            folder = self.static_folder.create({
                'folder_name': 's3store',
                'description': 'S3 Folder',
                's3_use_bucket': True,
                's3_access_key': 'AKIAJLJFWNMNMDQOVUJQ',
                's3_secret_key': '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',
                's3_bucket_name': 'tryton-test-s3',
                's3_cloudfront_cname': 'http://d84c7ijfqqzfi.cloudfront.net',
            })
            self.assert_(folder.id)

            s3_folder = self.static_folder.search([
                ('s3_use_bucket', '=', True)
            ])[0]

            # Create static file for amazon s3 bucket
            file = self.static_file.create({
                'name': 'testfile.png',
                'type': 's3',
                'folder': s3_folder,
                'file_binary': buffer('testfile')
            })
            self.assert_(file.id)

            self.assertEqual(
                file.file_binary, buffer('testfile')
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
