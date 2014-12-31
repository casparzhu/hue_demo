import os.path
#!/usr/bin/env python
# Licensed to Cloudera, Inc. under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  Cloudera, Inc. licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import stat
import time
import sys

from desktop.lib.django_util import render
import datetime

import posixpath
import json
from filebrowser.forms import UploadFileForm
from desktop.lib.exceptions_renderable import PopupException
from django import forms
from django.http import Http404, HttpResponse, HttpResponseNotModified, HttpResponseRedirect
from django.utils.translation import ugettext as _

#for hbasedemo
import re
import urllib
import json
from hbase.api import HbaseApi
from filebrowser.


class LocalFileSystem():
    """
    Local File System Interface.
    """
    def __init__(self, path='/'):
        if os.path.isdir(path):
            self.path = path
        else:
            raise IOError
    
    def list(self, path=''):
        if not path:
            path = self.path
        dirs = os.listdir(path)
        return dirs
    
    def chdir(self, path):
        if os.path.isdir(path):
            self.path = path
            os.chdir(path)
            return True
        else:
            return False
    
    def get_file_stat(self, file):
        return os.stat(file)
    
    def _get_file_type(self, filestat):
#        filestat = self.getFileStat(file)
        if stat.S_ISREG(filestat.st_mode):
            return 'R'
        elif stat.S_ISDIR(filestat.st_mode):
            return 'D'
        else:
            return 'O'
    
    def _get_file_size(self, filestat):
        return filestat.st_size
    
    def _get_file_owner(self, filestat):
        return filestat.st_uid
    
    def _get_file_group(self, filestat):
        return filestat.st_gid
    
    def _get_file_mode(self, filestat):
        return filestat.st_mode
    
    def _get_file_time(self, filestat):
        return filestat.st_ctime
    
    def get_file_info(self, file):
        filestat = self.get_file_stat(file)
        fileinfo = {}
        fileinfo['name'] = os.path.basename(file)
        fileinfo['type'] = self._get_file_type(filestat)
        fileinfo['size'] = self._get_file_size(filestat)
        fileinfo['owner'] = self._get_file_owner(filestat)
        fileinfo['group'] = self._get_file_group(filestat)
        fileinfo['mode'] = self._get_file_mode(filestat)
        fileinfo['time'] = time.asctime(time.localtime(self._get_file_time(filestat)))
        return fileinfo
    


#class FileSystem():
#    def __init__(self, type='local', path='/'):
#        self.type = type
#        self.path = path
#        if type == 'local':
#            self.fs = LocalFileSystem(self.path)




def index(request):
    if request.GET.get('type') == 'hdfs':
        return hdfsindex(request)
    
    dir = os.sep if not request.GET.get('dir') else request.GET.get('dir')
#    if dir[-1] != os.sep:
#        dir += os.sep
    fs = LocalFileSystem(dir)
    list = fs.list()

    file_info_list = [ fs.get_file_info(dir + f if dir == os.sep else dir + os.sep + f) for f in list]
    if dir != os.sep:
        parent_dir = fs.get_file_info(os.path.dirname(dir))
        parent_dir['name'] = '..'
        file_info_list.insert(0, parent_dir)
    return render('index.mako', request, dict(date=datetime.datetime.now(), \
                section='local', currentdir=dir, dirinfo=file_info_list, debug='', debug2=''))

def hdfsindex(request):
    fs = request.fs
    dir = '/' if not request.GET.get('dir') else request.GET.get('dir')
    
    response = {}
    if request.method == 'POST':
        response = {'status': -1, 'data': ''}
        try:
            resp = _upload_file(request)
            response.update(resp)
        except Exception, ex:
            response['data'] = unicode(ex)
            hdfs_file = request.FILES.get('hdfs_file')
            if hdfs_file:
                hdfs_file.remove()
        if response['status'] == 0:
            request.info(_('%(destination)s upload succeeded') % {'destination': response['path']})
#        return HttpResponse(json.dumps(response), content_type="text/plain")
#    else:
#        response['data'] = _('A POST request is required.')

    
    list = fs.listdir_stats(dir)
    if dir != '/':
        parent_dir = fs.stats(os.path.dirname(dir))
        parent_dir.name = '..'
        list.insert(0, parent_dir)
    file_info_list = [{'name': f.name, 'type': f.type, 'size': f.size, 'owner': f.user, 'group': f.group, 'mode': f.aclBit, 'time': time.asctime(time.localtime(f.mtime))} for f in list]
    debug = ''
    debug2 = json.dumps(response) if response.get('status') else ''
    return render('index.mako', request, dict(date=datetime.datetime.now(), \
                section='hdfs', currentdir=dir, dirinfo=file_info_list, debug=debug, debug2=debug2))


def _upload_file(request):
    """
    Handles file uploaded by HDFSfileUploadHandler.

    The uploaded file is stored in HDFS at its destination with a .tmp suffix.
    We just need to rename it to the destination path.
    """
    form = UploadFileForm(request.POST, request.FILES)
    response = {'status': -1, 'data': ''}

    if request.META.get('upload_failed'):
      raise PopupException(request.META.get('upload_failed'))

    if form.is_valid():
        uploaded_file = request.FILES['hdfs_file']
        dest = form.cleaned_data['dest']

        if request.fs.isdir(dest) and posixpath.sep in uploaded_file.name:
            raise PopupException(_('Sorry, no "%(sep)s" in the filename %(name)s.' % {'sep': posixpath.sep, 'name': uploaded_file.name}))

        dest = request.fs.join(dest, uploaded_file.name)
        tmp_file = uploaded_file.get_temp_path()
        username = request.user.username

        try:
            # Remove tmp suffix of the file
            request.fs.do_as_user(username, request.fs.rename, tmp_file, dest)
            response['status'] = 0
        except IOError, ex:
            already_exists = False
            try:
                already_exists = request.fs.exists(dest)
            except Exception:
              pass
            if already_exists:
                msg = _('Destination %(name)s already exists.')  % {'name': dest}
            else:
                msg = _('Copy to %(name)s failed: %(error)s') % {'name': dest, 'error': ex}
            raise PopupException(msg)

        response.update({
          'path': dest,
#          'result': _massage_stats(request, request.fs.stats(dest)),
#          'next': request.GET.get("next")
        })

        return response
    else:
        raise PopupException(_("Error in upload form: %s") % (form.errors,))


##hbase demo code
##fetch hbase cluster and table
def hbasedemo(request, url):
    url = url.strip('/')
    
    clusterlist = HbaseApi().query('getClusters')
    tablelist = HbaseApi().query('getTableList', clusterlist[0]['name'])
    print "url:", url
    print "tablelist:", tablelist
    response = None
    if url:
        decoded_url_params = [urllib.unquote(arg) for arg in re.split(r'(?<!\\)/', url.strip('/'))]
        response = HbaseApi().query(*decoded_url_params)

    # tablelist = []
    return render('hbasedemo.mako', request, dict(date=datetime.datetime.now(), \
                section='hbasedemo', clusterlist=clusterlist, tablelist=tablelist, rowlist=response, debug='', debug2=''))

##interaction between action and hbaseapi
def hbaseapi(request):
    action = request.GET.get('action')
    print action
    if action == 'getrows':
        cluster = request.GET.get('cluster')
        table = request.GET.get('table')
        rowkey = request.GET.get('params[rowkey]', None)
        print rowkey
        scan_length = 10 if rowkey in ('', None)  else 1
        params = ['getRowQuerySet', cluster, table, [], [{"row_key":rowkey,"scan_length":scan_length,"columns":[],"prefix":"false","filter":None,"editing":True}]]
        print params
        tablerows = HbaseApi().query(*params)
        print tablerows
        return api_dump(tablerows)
    elif action == 'getColumnDescriptors':
        cluster = request.GET.get('cluster')
        table = request.GET.get('table')
        columndescriptor = HbaseApi().query('getColumnDescriptors', cluster, table)
        print columndescriptor
        return api_dump(columndescriptor)
    elif action == 'addnewrow':
        cluster = request.POST.get('cluster')
        table = request.POST.get('table')
        rowkey = request.POST.get('rowkey')
        clumnname = request.POST.get('columnname')
        columnvalue = request.POST.get('columnvalue')
        params = ['putRow', cluster, table, rowkey, {clumnname:columnvalue}]
        response = {'status': False}
        print params
        try:
            result = HbaseApi().query(*params)
        except PopupException as e:
            print "exception:" + e.message
            # request.info(_('add row failed: %(errormsg)s ') % {'errormsg': e.message})
            response['msg'] = _('add row failed: %(errormsg)s ') % {'errormsg': e.message}
        else:
            response['status'] = True
            response['msg'] = _('add row succeeded')
        return HttpResponse(json.dumps(response), content_type="application/json")
    elif action == 'deleterow':
        cluster = request.POST.get('cluster')
        table = request.POST.get('table')
        rowkey = request.POST.get('rowkey')
        params = ['deleteAllRow', cluster, table, rowkey, {}]
        response = {'status': False}
        try:
            result = HbaseApi().query(*params)
        except PopupException, e:
            print "exception:", e.message
            response['msg'] = _('delete row failed: %(errormsg)s ') % {'errormsg': e.message}
        else:
            response['status'] = True
            response['msg'] = _('delete row succeeded')
            # request.info(_('add row succeeded'))

            # HttpResponseRedirect('/caspar_app/hbasedemo')
        # print type(result)
        return HttpResponse(json.dumps(response), content_type="application/json")
    elif action == 'createtable':
        cluster = request.POST.get('cluster')
        table = request.POST.get('tablename')
        cf = request.POST.get('cf')
        params = ['createTable', cluster, table, [{'properties':{'name':cf}}]]
        response = {'status': False}
        try:
            result =HbaseApi().query(*params)
        except PopupException, e:
            print "exception:", e.message
            response['msg'] = _('create table failed: %(errormsg)s ') % {'errormsg': e.message}
        else:
            response['status'] = True
            response['msg'] = _('create table succeeded')
        return HttpResponse(json.dumps(response), content_type="application/json")
    elif action == 'deletetable':
        cluster = request.POST.get('cluster')
        table = request.POST.get('table')
        params = ['deleteTable', cluster, table]
        response = {'status': False}
        try:
            result = HbaseApi().query(*params)
        except PopupException, e:
            print "exception:", e.message
            response['msg'] = _('delete table failed: %(errormsg)s ') % {'errormsg': e.message}
        else:
            response['status'] = True
            response['msg'] = _('delete table succeeded')
        return HttpResponse(json.dumps(response), content_type="application/json")
    elif action == 'disabletable':
        cluster = request.POST.get('cluster')
        table = request.POST.get('table')
        params = ['disableTable', cluster, table]
        response = {'status': False}
        try:
            result = HbaseApi().query(*params)
        except PopupException, e:
            print "exception:", e.message
            response['msg'] = _('disable table failed: %(errormsg)s ') % {'errormsg': e.message}
        else:
            response['status'] = True
            response['msg'] = _('disable table succeeded')
        return HttpResponse(json.dumps(response), content_type="application/json")
    elif action == 'enabletable':
        cluster = request.POST.get('cluster')
        table = request.POST.get('table')
        params = ['enableTable', cluster, table]
        response = {'status': False}
        try:
            result = HbaseApi().query(*params)
        except PopupException, e:
            print "exception:", e.message
            response['msg'] = _('enable table failed: %(errormsg)s ') % {'errormsg': e.message}
        else:
            response['status'] = True
            response['msg'] = _('enable table succeeded')
        return HttpResponse(json.dumps(response), content_type="application/json")
    elif action == 'editcell':
        cluster = request.POST.get('cluster')
        table = request.POST.get('table')
        rowkey = request.POST.get('rowkey')
        column = request.POST.get('column')
        timestamp = long(request.POST.get('timestamp'))
        params = ['getVerTs', cluster, table, rowkey, column, timestamp, 10, None]
        print params
        try:
            result = HbaseApi().query(*params)
        except PopupException, e:
            print "exception:", e.message
            response['msg'] = _('fetch cell failed: %(errormsg)s ') % {'errormsg': e.message}
        else:
            print result
        return api_dump(result)
    elif action == 'updaterow':
        cluster = request.POST.get('cluster')
        table = request.POST.get('table')
        rowkey = request.POST.get('rowkey')
        clumnname = request.POST.get('columnname')
        columnvalue = request.POST.get('columnvalue')
        params = ['putColumn', cluster, table, rowkey, clumnname, columnvalue]
        response = {'status': False}
        print params
        try:
            result = HbaseApi().query(*params)
        except PopupException as e:
            print "exception:" + e.message
            response['msg'] = _('update column failed: %(errormsg)s ') % {'errormsg': e.message}
        else:
            response['status'] = True
            response['msg'] = _('update column succeeded')
        return HttpResponse(json.dumps(response), content_type="application/json")
    # decoded_url_params = [urllib.unquote(arg) for arg in re.split(r'(?<!\\)/', url.strip('/'))]
    # return HttpResponse(json.dumps({ 'columndescriptor': columndescriptor, 'tablerows':tablerows, 'truncated': True, 'limit': 100 }), content_type="application/json")


def api_dump(response):
  ignored_fields = ('thrift_spec', '__.+__')
  trunc_limit = 100#conf.TRUNCATE_LIMIT.get()

  def clean(data):
    try:
      json.dumps(data)
      return data
    except:
      cleaned = {}
      lim = [0]
      if isinstance(data, str): # Not JSON dumpable, meaning some sort of bytestring or byte data
        #detect if avro file
        if(data[:3] == '\x4F\x62\x6A'):
          #write data to file in memory
          output = StringIO.StringIO()
          output.write(data)

          #read and parse avro
          rec_reader = io.DatumReader()
          df_reader = datafile.DataFileReader(output, rec_reader)
          return json.dumps(clean([record for record in df_reader]))
        return base64.b64encode(data)

      if hasattr(data, "__iter__"):
        if type(data) is dict:
          for i in data:
            cleaned[i] = clean(data[i])
        elif type(data) is list:
          cleaned = []
          for i, item in enumerate(data):
            cleaned += [clean(item)]
        else:
          for i, item in enumerate(data):
            cleaned[i] = clean(item)
      else:
        for key in dir(data):
          value = getattr(data, key)
          if value is not None and not hasattr(value, '__call__') and sum([int(bool(re.search(ignore, key)))
                                                                           for ignore in ignored_fields]) == 0:
            cleaned[key] = clean(value)
      return cleaned

  return HttpResponse(json.dumps({ 'data': clean(response), 'truncated': True, 'limit': trunc_limit }), content_type="application/json")



