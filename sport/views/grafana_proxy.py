from revproxy.views import ProxyView


class GrafanaProxyView(ProxyView):
    upstream = 'http://grafana:3000/grafana/'

    def get_proxy_request_headers(self, request):
        headers = super(GrafanaProxyView, self).get_proxy_request_headers(request)
        # Pass authentication to Grafana
        headers['X-WEBAUTH-EMAIL'] = request.user.email
        # Set original Host
        headers['Host'] = request.get_host()
        return headers
