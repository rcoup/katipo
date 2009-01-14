from django import template

register = template.Library()

@register.simple_tag
def percent_change(new, old):
    try:
        d = (float(new)-float(old)) / float(old)
        s = "%s%0.1f%%" % (((d>=0) and "+" or ""), 100.0 * d)
        return s
    except:
        return ""
    
