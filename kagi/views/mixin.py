class OriginMixin(object):
    def get_origin(self):
        return "{scheme}://{host}".format(
            scheme=self.request.scheme, host=self.request.get_host()
        )
