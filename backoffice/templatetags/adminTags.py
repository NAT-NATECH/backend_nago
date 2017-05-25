from django import template
 
register = template.Library()

@register.assignment_tag
def bootstrap_mt(tags):
  """
  Convert django tag in bootstrap tag
  """
  return ('danger' if tags == 'error' else tags)