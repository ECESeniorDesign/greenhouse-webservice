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
                defined_methods = [method for method in dir(klass)
                                   if not method.startswith("__")]
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
                    action.__name__ = "{}.{}".format(
                        klass.__name__, action.__name__)
                    mapping = mappings[method][0]
                    html_method = mappings[method][1]
                    wrapped_action = self.app.route(mapping,
                                                    methods=[html_method])(action)
                    wrapped_action = staticmethod(wrapped_action)
                    setattr(klass, method, wrapped_action)
                for method in defined_methods:
                    action = getattr(klass, method)
                    if hasattr(action, "EP"):
                        html_method, end_url = action.EP
                        action = action.__func__
                        del action.EP
                        action.__name__ = "{}.{}".format(
                            klass.__name__, action.__name__)
                        wrapped_action = self.app.route(
                            self.base_url + "/" + end_url,
                            methods=[html_method])(action)
                        wrapped_action = staticmethod(wrapped_action)
                        setattr(klass, method, wrapped_action)
                return klass

        return route_decorator(base_url, only, exclude)

    def endpoint(router_instance, end_url, method="GET"):
        def wrapper(instance_method):
            instance_method.EP = (method, end_url)
            return instance_method
        return wrapper

    def root(self, controller, action):
        action_func = getattr(controller, action)
        wrapped_action = self.app.route("/")(action_func)
        wrapped_action = staticmethod(action)
        setattr(controller, action, wrapped_action)

