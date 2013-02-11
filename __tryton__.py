# -*- coding: UTF-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

{
    'name': 'Nereid-s3',
    'version': '2.4.0.1',
    'author': 'Openlabs Technologies & Consulting (P) Limited',
    'email': 'info@openlabs.co.in',
    'website': 'http://www.openlabs.co.in/',
    'description': '''Base configuration of Nereid-S3 that allows
    static files to be stored on Amazon-S3:
    ''',
    'depends': [
        'ir',
        'res',
        'company',
        'nereid',
    ],
    'xml':[
       'static_file.xml',
    ],
    'translation': [
    ],
}

