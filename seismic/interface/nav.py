class SimpleNavigator(object):
    base = '<ul class="nav nav-pills nav-stacked">{}</ul>'
    active = "<li class=\"active\"><a href=\"{1}\">{0}</a></li>"
    inactive = "<li><a href=\"{1}\">{0}</a></li>"

    def __init__(self, links):
        self.links = links

    def render_as(self, name):
        out = ""
        for link, path in self.links:
            if name != link:
                out += SimpleNavigator.inactive.format(link, path)
            else:
                out += SimpleNavigator.active.format(link, path)
        return SimpleNavigator.base.format(out)
