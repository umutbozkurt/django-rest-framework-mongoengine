from django.shortcuts import render

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
# Create your views here.

def home(request):
    
    param1 = "parameter_1"
    return render_to_response('homepage/index.html',
    {
        'param':param1
    },
    context_instance = RequestContext(request))                                    
