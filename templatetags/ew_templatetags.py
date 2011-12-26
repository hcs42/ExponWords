from __future__ import with_statement
import os

from django import template

register = template.Library()

class CustomHead(template.Node):

    def __init__(self, filepath):
        self.filepath = filepath

    def render(self, context):
        if os.path.exists(self.filepath):
            with open(self.filepath) as f:
                return f.read()
        else:
            return ''

@register.tag(name='include_if_exists')
def include_if_exists(parser, token):

    try:
        tag_name, filename = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
                  'include_if_exists tag requires a single argument')
    if not (filename[0] == filename[-1] and
            filename[0] in ('"', "'")):
        raise template.TemplateSyntaxError(
                  "include_if_exists tag's argument should be in quotes")
    filename = filename[1:-1] # Remove quotes
    
    filepath = os.path.join('ew', 'templates', filename)
    return CustomHead(filepath)
