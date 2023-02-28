{
    "name": """S3 Attachment Storage""",
    "summary": """Upload attachments on Amazon S3""",
    "category": "Tools",
    "images": [],
    "version": "14.0.3.0.1",
    "application": False,
    "author": "IT-Projects LLC, Ildar Nasyrov",
    "website": "https://twitter.com/OdooFree",
    "license": "Other OSI approved licence",  # MIT
    "depends": ["base_setup", "ir_attachment_url", "onesphere_oss", "web_notify"],
    "external_dependencies": {"python": ["boto3"], "bin": []},
    "data": ["data/ir_attachment_s3_data.xml", "views/res_config_settings_views.xml"],
    "qweb": [],
    "demo": [],
    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": "_ir_attachment_s3_post_init",
    "auto_install": False,
    "installable": True,
}
