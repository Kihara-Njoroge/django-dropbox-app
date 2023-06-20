from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.urls import reverse
from django.views.defaults import server_error

from .wrapper import DropboxWrapper

dropbox = DropboxWrapper(settings.DROPBOX_APP_KEY)

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
    return render(request, 'viewer/index.html', context)