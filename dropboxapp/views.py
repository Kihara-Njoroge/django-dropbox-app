from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.urls import reverse
from django.views.defaults import server_error
from decouple import config
from dropbox.exceptions import ApiError

from .wrapper import DropboxWrapper
dropbox = DropboxWrapper(config("DROPBOX_APP_KEY"))

def request_access(request):
    redirect = request.build_absolute_uri(reverse('confirm'))
    url = dropbox.request_access(request.session, redirect)
    context = {'url': url}
    return render(request, 'access.html', context)

def confirm_access(request):
    if dropbox.conclude_access(request.GET):
        return HttpResponseRedirect(reverse('index'))
    return server_error(request)

# ----------------------------------------------------------------------------
def listfolder(request, url='', uploaded=None, created=None, deleted=None):
    '''List all contents from a Dropbox folder.'''
    if not dropbox.has_access():
        return HttpResponseRedirect(reverse('auth'))

    files = dropbox.listdir('' if len(url) == 0 else ('/' + url))

    # The hierarchy of folders, for easy navigation
    levels = [{'url': '', 'name': ''}]
    if url != '':
        for part in url.split('/'):
            up = levels[-1]['url']
            info = {'url' : ((up + '/') if len(up) > 0 else '') + part,
                    'name': part}
            levels.append(info)

    context = {'url': url, 
               'levels': levels,
               'files': files,
               'current': levels[-1]['name'],
               'uploaded': uploaded,
               'created': created,
               'deleted': deleted,
              }
    return render(request, 'index.html', context)

def download(request, name):
    if not dropbox.has_access():
        return HttpResponseRedirect(reverse('auth'))

    fd = dropbox.get_file(name)
    nice_name = name.split('/')[-1]
    response = HttpResponse(fd.read(), content_type="application/octet-stream")
    response['Content-Disposition'] = f'inline; filename={nice_name}'
    return response
    
def upload(request):
    if not dropbox.has_access():
        return HttpResponseRedirect(reverse('auth'))

    if request.method == 'POST' and request.FILES['input_file']:
        path = request.POST['folder_path']
        name = dropbox.upload_file(path=path,
                upfile=request.FILES['input_file'])
        return listfolder(None, url=path, uploaded=name)
    return HttpResponseRedirect(reverse('index'))

def newfolder(request):
    if not dropbox.has_access():
        return HttpResponseRedirect(reverse('auth'))

    if request.method == 'POST':
        path = request.POST['folder_path']
        name = request.POST['folder_name']
        if len(name) == '':
            return listfolder(None, url=path)
        dropbox.create_folder(path=path, name=name)
        return listfolder(None, url=path, created=name)
    return HttpResponseRedirect(reverse('index'))

def delete(request, path):
    if not dropbox.has_access():
        return HttpResponseRedirect(reverse('auth'))

    try:
        dropbox.delete_file(path)
        return listfolder(None,deleted=path)
    except ApiError as e:
        if e.error.is_path() and e.error.get_path().is_not_found():
            # File not found
            return HttpResponseRedirect(reverse('error'))
    return HttpResponseRedirect(reverse('index'))


