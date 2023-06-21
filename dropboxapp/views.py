from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.urls import reverse
from django.views.defaults import server_error

from .wrapper import DropboxWrapper

dropbox = DropboxWrapper(settings.DROPBOX_APP_KEY)



def request_access(request):
    '''Display the authorization request page.'''
    redirect = request.build_absolute_uri(reverse('confirm'))
    url = dropbox.request_access(request.session, redirect)
    context = {'url': url}
    return render(request, 'access.html', context)

# ----------------------------------------------------------------------------
def confirm_access(request):
    '''Finish the authorization flow and redirect to listfolder.

    This page is a redirection from the authorization request page.
    '''
    if dropbox.conclude_access(request.GET):
        return HttpResponseRedirect(reverse('index'))
    return server_error(request)

# ----------------------------------------------------------------------------
def listfolder(request, url='', uploaded=None, created=None):
    '''List all contents from a Dropbox folder.

    This is the main page, that contains the links for file download, as well
    forms for file upload and folder creation. All pages redirect here.
    If there is no access to a Dropbox account, it redirects to the
    authorization page.

    Parameters:
    url      : the current Dropbox folder being displayed
    uploaded : the name of the last file uploaded, to be notified
    created  : the name of the last folder created, to be notified
    '''
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
              }
    return render(request, 'index.html', context)

# ----------------------------------------------------------------------------
def download(request, name):
    '''Download the named file from Dropbox.

    If there is no access to a Dropbox account, it redirects to the
    authorization page.
    '''
    if not dropbox.has_access():
        return HttpResponseRedirect(reverse('auth'))

    fd = dropbox.get_file(name)
    nice_name = name.split('/')[-1]
    response = HttpResponse(fd.read(), content_type="application/octet-stream")
    response['Content-Disposition'] = f'inline; filename={nice_name}'
    return response
    
# ----------------------------------------------------------------------------
def upload(request):
    '''Upload the file sent by POST to Dropbox.

    Redirect to listfolder afterwards. If there is no access to a Dropbox 
    account, it redirects to the authorization page.
    '''
    if not dropbox.has_access():
        return HttpResponseRedirect(reverse('auth'))

    if request.method == 'POST' and request.FILES['input_file']:
        path = request.POST['folder_path']
        name = dropbox.upload_file(path=path,
                upfile=request.FILES['input_file'])
        return listfolder(None, url=path, uploaded=name)
    return HttpResponseRedirect(reverse('index'))

# ----------------------------------------------------------------------------
def newfolder(request):
    '''Create the folder sent by POST in Dropbox.
    
    Redirect to listfolder afterwards. If there is no access to a Dropbox 
    account, it redirects to the authorization page.
    '''
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
