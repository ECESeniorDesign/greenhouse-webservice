class Router(object):
    def __init__(self, app):
        self.app = app
    
    def route(router_instance, base_url, only=[], exclude=[]):

        class route_decorator(object):
            def __init__(self, base_url, only, exclude):
                all_methods = ["index", "new", "create", "show",
                               "edit", "update", "destroy"]
                if only:
                    self.methods = only
                else:
                    self.methods = list(set(all_methods) - set(exclude))
                self.base_url = base_url
                self.app = router_instance.app

            def __call__(self, klass):
                mappings = {
                    'index': (self.base_url, 'GET'),
                    'new': (self.base_url + '/new', 'GET'),
                    'create': (self.base_url, 'POST'),
                    'show': (self.base_url + "/<id>", 'GET'),
                    'edit': (self.base_url + "/<id>/edit", 'GET'),
                    'update': (self.base_url + "/<id>", 'POST'), # Change to PATCH?
                    'destroy': (self.base_url + "/<id>", 'DELETE')
                }
                for method in self.methods:
                    action = getattr(klass, method)
                    mapping = mappings[method][0]
                    html_method = mappings[method][1]
                    wrapped_action = self.app.route(mapping,
                                                    methods=[html_method])(action)
                    wrapped_action = staticmethod(wrapped_action)
                    setattr(klass, method, wrapped_action)
                return klass

        return route_decorator(base_url, only, exclude)

    def root(self, controller, action):
        action_func = getattr(controller, action)
        wrapped_action = self.app.route("/")(action_func)
        wrapped_action = staticmethod(action)
        setattr(controller, action, wrapped_action)

