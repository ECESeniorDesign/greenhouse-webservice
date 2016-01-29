# -*- coding: utf-8 -*-
"""
    flaskext.coffee
    ~~~~~~~~~~~~~

    A CoffeeScript extension for Flask

    :copyright: (c) 2011 by Col Wilson.
    :license: MIT, see LICENSE for more details.
"""

import os, subprocess

def coffee(app):
    @app.before_request
    def _render_coffee():

        if not hasattr(app, 'static_url_path'):
            from warnings import warn
            warn(DeprecationWarning('static_path is called '
                                    'static_url_path since Flask 0.7'),
                                    stacklevel=2)

            static_url_path = app.static_path

        else:
            static_url_path = app.static_url_path

        static_dir = app.root_path + app.static_url_path


        coffee_paths = []
        for path, subdirs, filenames in os.walk(static_dir):
            coffee_paths.extend([
                os.path.join(path, f)
                for f in filenames if os.path.splitext(f)[1] == '.coffee'
            ])

        for coffee_path in coffee_paths:
            # CHASE: FIXED issue where the js_path had a .coffee extension
            # that resulted in compilation every time...
            js_path = os.path.splitext(coffee_path)[0] + '.js'
            if not os.path.isfile(js_path):
                js_mtime = -1
            else:
                js_mtime = os.path.getmtime(js_path)
            coffee_mtime = os.path.getmtime(coffee_path)
            if coffee_mtime >= js_mtime:
                subprocess.call(['coffee', '-c', coffee_path], shell=False)
