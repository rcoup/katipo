from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404
from django import forms

from katipo.models import Run, Url

def run_detail(request, object_id):
    run = get_object_or_404(Run, pk=object_id)
    
    # handle requests for URL-lists
    if 'result' in request.REQUEST:
        r = request.REQUEST['result']
        if r in ('ERROR', 'TIMEOUT', 'GOOD', 'BAD', ''):
            qs = run.urls.filter(result=r)
            return render_to_response('katipo/_url_table.html', {'urls':qs})
        else:
            raise Http404
    
    class CompareRunForm(forms.Form):
        compare_run = forms.ModelChoiceField(queryset=run.profile.runs.exclude(pk=run.id), initial=run.profile.get_run_previous())
    
    run_c = None
    if 'compare_run' in request.REQUEST:
        compare_list_form = CompareRunForm(request.REQUEST)
        if compare_list_form.is_valid():
            run_c = compare_list_form.cleaned_data['compare_run']
    else:
        compare_list_form = CompareRunForm()
    
    ctx = {
        'run': run,
        'compare_run': run_c,
        'compare_list_form': compare_list_form,
    }
    
    return render_to_response('katipo/run_detail.html', ctx)

def url_redirect(request, url):
    u = Url.objects.filter(url=url)[:1]
    if not len(u):
        raise Http404()
    else:
        return HttpResponseRedirect(u[0].get_absolute_url())

def url_detail(request, run_id):
    u = get_object_or_404(Url, url=request.GET.get('u'), run=run_id)
    
    # handle requests for link-lists
    if 'links' in request.GET:
        lt = request.GET['links']
        if lt == 'incoming':
            return render_to_response('katipo/_url_table.html', {'urls':u.incoming_links.all()})
        elif lt == 'outgoing':
            return render_to_response('katipo/_url_table.html', {'urls':u.outgoing_links.all()})
        else:
            raise Http404
        
    run_qs = Url.objects.filter(url=u.url)
    class RunForm(forms.Form):
        run = forms.ChoiceField(choices=[(url.id, unicode(url.run)) for url in run_qs], initial=u.id)
    
    if 'run' in request.REQUEST:
        run_form = RunForm(request.REQUEST)
        if run_form.is_valid():
            dest_url = get_object_or_404(Url, pk=run_form.cleaned_data['run'])
            return HttpResponseRedirect(dest_url.get_absolute_url())
    else:
        run_form = RunForm()
    
    ctx = {
        'url': u,
        'run_form': run_form,
    }

    return render_to_response('katipo/url_detail.html', ctx)

def url_search(request):
    if 'u' in request.GET:
        return url_redirect(request, request.GET['u'])
    
    ctx = {
        'search': False
    }
    status = 200
    if 'search' in request.REQUEST:
        search = request.REQUEST.get('search', '').strip()
        ctx['search'] = search
        ctx['urls'] = Url.objects.search(search)
        ctx['notfound'] = not (ctx['urls']['exact'] or len(ctx['urls']['inexact']))
    
    return render_to_response('katipo/url_search.html', ctx)
    