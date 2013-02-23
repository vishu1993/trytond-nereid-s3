# -*- coding: utf-8 -*-
"""
    static_file

    Static File

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import ModelSQL, ModelView, fields
from trytond.pyson import Eval, Bool
from boto.s3.connection import S3Connection
from boto.s3.key import Key


class NereidStaticFolder(ModelSQL, ModelView):
    _name = "nereid.static.folder"
    _description = __doc__
    _rec_name = "folder_name"

    s3_use_bucket = fields.Boolean("Use S3 Bucket?")
    s3_access_key = fields.Char(
        "S3 Access Key",
        states={'required': Bool(Eval('s3_use_bucket'))}
    )
    s3_secret_key = fields.Char(
        "S3 Secret Key",
        states={'required': Bool(Eval('s3_use_bucket'))}
    )
    s3_bucket_name = fields.Char(
        "S3 Bucket Name",
        states={'required': Bool(Eval('s3_use_bucket'))}
    )
    s3_cloudfront_cname = fields.Char(
        "S3 Cloudfront CNAME",
        states={'required': Bool(Eval('s3_use_bucket'))}
    )
    s3_object_prefix = fields.Char("S3 Object Prefix")

    def __init__(self):
        super(NereidStaticFolder, self).__init__()

        self._constraints += [
            ('check_cloudfront_cname', 'invalid_cname'),
        ]
        self._error_messages.update({
            "invalid_cname": "Cloudfront CNAME with '/' at the end is not " +
                "allowed",
        })

    def default_s3_cloudfront_cname(self):
        """
        Sets default for Cloudfront CNAME
        """
        return "http://your-domain.cloudfront.net"

    def check_cloudfront_cname(self, ids):
        """
        Checks for '/' at the end of Cloudfront CNAME
        """
        for folder in self.browse(ids):
            if folder.s3_cloudfront_cname.endswith('/'):
                return False
        return True


NereidStaticFolder()


class NereidStaticFile(ModelSQL, ModelView):
    _name = "nereid.static.file"
    _description = __doc__

    folder = fields.Many2One(
        'nereid.static.folder', 'Folder', select=True, required=True,
        domain=[('s3_use_bucket', '=', Eval('is_s3_bucket'))],
        depends=['is_s3_bucket'],
    )
    type = fields.Selection([
        ('local', 'Local File'),
        ('remote', 'Remote File'),
        ('s3', 'S3'),
    ], 'File Type', on_change=['type', 's3_bucket'])

    is_s3_bucket = fields.Function(
        fields.Boolean("S3 Bucket?"), 'get_is_s3_bucket'
    )
    s3_key = fields.Function(fields.Char("S3 key"), "get_s3_key")

    def get_s3_key(self, ids, name):
        """
        Returns s3 key for static file
        """
        res = {}
        for file in self.browse(ids):
            if file.folder.s3_object_prefix:
                res[file.id] = '/'.join(
                    [file.folder.s3_object_prefix, file.name]
                )
            else:
                res[file.id] = file.name
        return res

    def _get_url(self, static_file):
        """
        Return the URL for the given static file

        :param static_file: Browse Record of the static file
        """
        if static_file.type == 's3':
            return '/'.join(
                [static_file.folder.s3_cloudfront_cname, static_file.s3_key]
            )
        return super(NereidStaticFile, self)._get_url(static_file)

    def _set_file_binary(self, static_file, value):
        """
        Stores the file to amazon s3

        :param static_file: Browse record of the static file
        """
        if not value:
            return
        if static_file.type == "s3":
            bucket = self.get_bucket(static_file)
            key = Key(bucket)
            key.key = static_file.s3_key
            return key.set_contents_from_string(value)
        return super(NereidStaticFile, self)._set_file_binary(
            static_file, value
        )

    def _get_file_binary(self, static_file):
        '''
        Getter for the binary_file field. This fetches the file from the
        Amazon s3

        :param ids: the ids of the sales
        :return: Dictionary with ID as key and file buffer as value
        '''
        if static_file.type == "s3":
            bucket = self.get_bucket(static_file)
            key = Key(bucket)
            key.key = static_file.s3_key
            return buffer(key.get_contents_as_string())
        return super(NereidStaticFile, self)._get_file_binary(static_file)

    def _get_file_path(self, static_file):
        """
        Returns path for given static file

        :param static_file: Browse record of the static file
        """
        if static_file.type == "s3":
            return '/'.join(
                [static_file.folder.s3_cloudfront_cname, static_file.s3_key]
            )
        return super(NereidStaticFile, self)._get_file_path(static_file)

    def on_change_type(self, vals):
        """
        Changes the value of functional field when type is changed

        :param vals: Dictionary of fields and their values
        :return: Updated value of functional field
        """
        return {
            'is_s3_bucket': vals['type'] == 's3'
        }

    def get_bucket(self, static_file):
        '''
        Return an S3 bucket for the static file
        '''
        s3_conn = S3Connection(
            static_file.folder.s3_access_key, static_file.folder.s3_secret_key
        )
        return s3_conn.get_bucket(static_file.folder.s3_bucket_name)

    def get_is_s3_bucket(self, ids, name):
        """
        Gets value of s3_use_bucket of folder

        :param ids: List of ids
        "param name: Field name
        :return: A dictionary with value for each ids
        """
        res = {}
        for file in self.browse(ids):
            res[file.id] = bool(file.folder.s3_use_bucket)
        return res

    def check_use_s3_bucket(self, ids):
        """
        Checks if type is S3 then folder must have use_s3_bucket
        """
        for files in self.browse(ids):
            if files.type == "s3" and not files.folder.s3_use_bucket:
                return False
        return True

    def __init__(self):
        super(NereidStaticFile, self).__init__()

        self._constraints += [
            ('check_use_s3_bucket', 's3_bucket_required'),
        ]
        self._error_messages.update({
            "s3_bucket_required": "Folder must have s3 bucket if type is 'S3'",
        })

NereidStaticFile()
