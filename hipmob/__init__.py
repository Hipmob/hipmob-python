# Hipmob python bindings
# API docs at https://www.hipmob.com/documentation/api.html
# Author: Femi Omojola <femi@hipmob.com>

# Imports
import urllib2, urllib
from urlparse import urlparse
import os
from pprint import pprint
import base64
import json
import re
import time
import hashlib
from datetime import datetime

# core object
class Hipmob:
    class HipmobApp:
        def __init__(self, parent, id, sourcedata):
            self._parent = parent
            self._sourcedata = sourcedata
            self._id = id
            if 'name' in sourcedata:
                self._name = sourcedata['name']
            if 'url' in sourcedata:
                self._url = sourcedata['url']
            self.modified = False
            self.created = False
            if sourcedata != None:
                if 'created' in sourcedata:
                    self.created = datetime.strptime(sourcedata['created'], "%Y-%m-%dT%H:%M:%S.%fZ")
                if 'modified' in sourcedata:
                    self.modified = datetime.strptime(sourcedata['modified'], "%Y-%m-%dT%H:%M:%S.%fZ")

        def send_text_messages(self, text, devices, **kwargs):
            return self._parent.__send_text_messages__(self._id, text, devices, **kwargs)

        def __str__(self):
            return "(HipmobApp) "+self._name+" ["+self._id+"]";

    class HipmobUser:
        def __init__(self, parent, username, sourcedata):
            self._parent = parent
            self._sourcedata = sourcedata
            self._username = username
            if 'first_name' in sourcedata:
                self._first_name = sourcedata['first_name']
            if 'last_name' in sourcedata:
                self._last_name = sourcedata['last_name']
            if 'status' in sourcedata:
                self._status = sourcedata['status']

        def username(self):
            return self._username

        def first_name(self):
            return self._first_name

        def last_name(self):
            return self._last_name

        def status(self):
            return self._status

        def set_status(self, status, **kwargs):
            return self._parent.__set_user_status__(self._username, status, **kwargs)

        def __str__(self):
            return "(HipmobUser) "+self._username+" ("+self._first_name+" "+self._last_name+") ["+self._status+"]"

    class HipmobDevice:
        def __init__(self, parent, app, id):
            self._parent = parent
            self._app = app
            self._id = id
            self._loaded = False
            
        def id(self):
            return self._id

        def __str__(self):
            return "(HipmobDevice) ["+self._app+"/"+self._id+"]";

        def __apply_source__(self, source):
            self.platform = source['platform'];
            self.version = source['version'];
            self.created = datetime.strptime(source['created'], "%Y-%m-%dT%H:%M:%S.%fZ")
            self.modified = False
            if 'modified' in source:
                self.modified = datetime.strptime(source['modified'], "%Y-%m-%dT%H:%M:%S.%fZ")
            self.userdata = {}
            if 'userdata' in source:
                self.userdata = source['userdata']
            loaded = True

        def load(self):
            if self._loaded:
                return
            
            self.__apply_source__(self._parent.__load_device__(self._app, self._id))

        def get_available_message_count(self):
            return self._parent.__get_available_message_count__(self._app, self._id)

        def check_device_status(self):
            return self._parent.__check_device_status__(self._app, self._id)
        
        def send_text_message(self, text, **kwargs):
            return self._parent.__send_text_message__(self._app, self._id, text, **kwargs)

        def send_json_message(self, content, **kwargs):
            return self._parent.__send_json_message__(self._app, self._id, content, **kwargs)

        def send_binary_message(self, content, **kwargs):
            return self._parent.__send_binary_message__(self._app, self._id, content, **kwargs)

        def send_picture_message(self, picturefile, mimetype, **kwargs):
            return self._parent.__send_picture_message__(self._app, self._id, picturefile, mimetype, **kwargs)

        def send_audio_message(self, audiofile, mimetype, **kwargs):
            return self._parent.__send_audio_message__(self._app, self._id, audiofile, mimetype, **kwargs)

        def list_friends(self):
            return self._parent.__list_friends__(self._app, self._id)

        def remove_friend(self, friend):
            return self._parent.__remove_friends__(self._app, self._id, [friend.id()])

        def remove_friends(self, friends):
            ids = []
            for x in friends:
                ids.append(x.id())
            return self._parent.__remove_friends__(self._app, self._id, ids)

        def remove_all_friends(self):
            return self._parent.__remove_all_friends__(self._app, self._id)
        
        def add_friend(self, friend):
            return self._parent.__add_friends__(self._app, self._id, [friend.id()])

        def add_friends(self, friends):
            ids = []
            for x in friends:
                ids.append(x.id())
            return self._parent.__add_friends__(self._app, self._id, ids)
        
        def set_friends(self, friends):
            ids = []
            for x in friends:
                ids.append(x.id())
            return self._parent.__set_friends__(self._app, self._id, ids)

        def generate_peer_token(self, secret, friend):
            now = str(int(time.time()))
            return now +'|'+ hashlib.sha512(self._id+'|'+friend.id()+'|'+now+'|'+secret).hexdigest()

        def generate_auth_token(self, secret):
            now = str(int(time.time()))
            return now +'|'+ hashlib.sha512(self._id+'|'+now+'|'+secret).hexdigest()

    def __init__(self, username, apikey = None):
        self._serverurl = 'https://api.hipmob.com/'
        if username == None or "" == username.strip():
            # throw an exception
            raise ValueError("username can not be null or blank. Get one at https://hipmob.com/.")
        else:
            self._username = username

        if apikey == None or "" == apikey.strip():
            # try and parse it
            bits = urlparse(username)
            
            if bits.username != None and bits.password != None and bits.hostname != None:
                self._username = bits.username
                self._apikey = bits.password
                self._serverurl = "https://"+bits.hostname+"/"
            else:
                # throw an exception
                raise ValueError("apikey can not be null or blank. Log into your account at https://hipmob.com/ to retrieve your api key.")
        else:
            # save the values
            self._apikey = apikey

        # get the url, and override it if necessary
        if 'hipmob_server' in os.environ:
            self._serverurl = os.environ['hipmob_server']
        
        # setup all the regular expressions we use
        # error patterns
        self._pattern1 = re.compile(r"No application specified\.")
        self._pattern2 = re.compile(r"No device specified\.")
        self._pattern3 = re.compile(r"API Request Failed\.")
        self._pattern4 = re.compile(r"Device not found\.")
        self._pattern5 = re.compile(r"Application not found\.")
        self._pattern6 = re.compile(r"No friends specified\.")
        self._pattern7 = re.compile(r"Unauthorized/")
        self._pattern8 = re.compile(r"Authentication required/")
        self._pattern9 = re.compile(r"Invalid message content-type\.")
        self._pattern10 = re.compile(r"User not found\.")
        self._pattern11 = re.compile(r"No status specified\.")
        self._pattern12 = re.compile(r"Invalid status specified\.")
        self._pattern13 = re.compile(r"You can only change your own status\.")

        # response patterns
        self._message_sent_pattern = re.compile(r"Message sent\.")
        self._multiple_messages_sent_pattern = re.compile(r"(\d*) messages sent\.")
        self._friend_removed_pattern = re.compile(r"Friend removed\.")
        self._no_changes_made_pattern = re.compile(r"No changes made\.")
        self._all_friends_removed_pattern = re.compile(r"Friend list cleared \((\d*) friends removed\)\.")
        self._friends_set_pattern = re.compile(r"Friend list updated \((\d*) friends added\)\.")
        self._status_updated_pattern = re.compile(r"\[(\w*)\] status updated to \"(\w*)\"")
            
    def __handle_error__(self, e, resp):
        #print e.code
        #print e.read()
        if resp != None:
            self.__check_for_errors__(resp, err=True)
        if e.code == 404:
            raise ValueError("Unauthorized")
        raise ValueError("["+str(e.code)+"] "+e.read())
        
    def __check_for_errors__(self, resp, **kwargs):
        if 'x-hipmob-reason' not in resp:
            if 'err' in kwargs:
                raise ValueError("No response from API")
            else:
                return
        reason = resp['x-hipmob-reason']
        if self._pattern7.match(reason) != None:
            raise ValueError("Unauthorized")
        elif self._pattern8.match(reason) != None:
            raise ValueError("Authentication required")
        elif self._pattern9.match(reason) != None:
            raise ValueError("Invalid message content type")
        elif self._pattern1.match(reason) != None:
            raise ValueError("No application specified")
        elif self._pattern2.match(reason) != None:
            raise ValueError("No device specified")
        elif self._pattern3.match(reason) != None:
            raise ValueError("Invalid request")
        elif self._pattern4.match(reason) != None:
            raise ValueError("Device not found")
        elif self._pattern5.match(reason) != None:
            raise ValueError("Application not found")
        elif self._pattern6.match(reason) != None:
            raise ValueError("No friends specified")

    def get_applications(self):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        req = urllib2.Request(self._serverurl + 'apps')
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)  
        u = None
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)
            
        self.__check_for_errors__(resp)
        res = []
        if 'content-type' in resp and resp['content-type'] == 'application/vnd.com.hipmob.App-list+json; version=1.0':
            sourcedata = json.loads(u.read())
            if 'count' in sourcedata and sourcedata['count'] > 0 and 'values' in sourcedata:
                for x in sourcedata['values']:
                    res.append(Hipmob.HipmobApp(self, x['id'], x))
        return res
                
    def get_application(self, mobilekey, **kwargs):
        if 'verify' in kwargs and kwargs['verify'] == False:
            return Hipmob.HipmobApp(self, str(mobilekey), {
                        'id': mobilekey,
                        'name': 'not set',
                        'url': 'not set'
                        })
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        req = urllib2.Request(self._serverurl + 'apps/'+str(mobilekey))
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)  
        u = None
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)

        self.__check_for_errors__(resp)
        res = None
        if 'content-type' in resp and resp['content-type'] == 'application/vnd.com.hipmob.App+json; version=1.0':
            res = Hipmob.HipmobApp(self, str(mobilekey), json.loads(u.read()))
        return res

    def get_user(self, username):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        req = urllib2.Request(self._serverurl + 'user/'+str(username))
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)  
        u = None
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)

        self.__check_for_errors__(resp)
        res = None
        if 'content-type' in resp and resp['content-type'] == 'application/vnd.com.hipmob.User+json; version=1.0':
            res = Hipmob.HipmobUser(self, str(username), json.loads(u.read()))
        return res

    def get_device(self, mobilekey, deviceid, **kwargs):
        # create the device
        res = Hipmob.HipmobDevice(self, str(mobilekey), str(deviceid))
        if "verify" not in kwargs or kwargs['verify'] != True:
            return res
        else:
            # build the request
            opener = urllib2.build_opener(urllib2.HTTPHandler)
            req = urllib2.Request(self._serverurl+'apps/'+str(mobilekey)+'/devices/'+str(deviceid))
            req.get_method = lambda: 'HEAD'
            base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
            req.add_header("Authorization", "Basic %s" % base64string)  
            resp = None
            try:
                u = opener.open(req)
                resp = dict(u.info())
            except urllib2.HTTPError, e:
                self.__handle_error__(e, resp)
                
            self.__check_for_errors__(resp)                
            
            # we're here, so go
            return res


    def __load_device__(self, mobilekey, deviceid):
        # build the request
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        req = urllib2.Request(self._serverurl+'apps/'+mobilekey+'/devices/'+deviceid)
        req.get_method = lambda: 'GET'
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)  
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)
            
        self.__check_for_errors__(resp)                
            
        # we're here, so go
        if 'content-type' in resp and resp['content-type'] == 'application/vnd.com.hipmob.Device+json; version=1.0':
            return json.loads(u.read())
        return None

    def __get_available_message_count__(self, mobilekey, deviceid):
        # build the request
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        req = urllib2.Request(self._serverurl+'apps/'+mobilekey+'/devices/'+deviceid+"/messagecount")
        req.get_method = lambda: 'GET'
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)  
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)
            
        self.__check_for_errors__(resp)                
            
        # we're here, so go
        if 'content-type' in resp and resp['content-type'] == 'application/vnd.com.hipmob.Device.pendingmessagecount+json; version=1.0':
            bits = json.loads(u.read())
            if 'count' in bits:
                return bits['count']
        return 0

    def __check_device_status__(self, mobilekey, deviceid):
        # build the request
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        req = urllib2.Request(self._serverurl+'apps/'+mobilekey+'/devices/'+deviceid+"/status")
        req.get_method = lambda: 'GET'
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)  
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)
            
        self.__check_for_errors__(resp)                
            
        # we're here, so go
        if 'content-type' in resp and resp['content-type'] == 'application/vnd.com.hipmob.Device.status+json; version=1.0':
            bits = json.loads(u.read())
            if 'online' in bits:
                return bits['online']
        return False

    def __send_text_message__(self, mobilekey, deviceid, text, **kwargs):
        # build the request
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        txdata = { "text": text }
        if 'autocreate' in kwargs and kwargs['autocreate'] == True:
            txdata['autocreate'] = "true"
        req = urllib2.Request(self._serverurl+'apps/'+mobilekey+'/devices/'+deviceid+"/messages")
        req.get_method = lambda: 'POST'
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)
        req.add_data(urllib.urlencode(txdata))
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)
        self.__check_for_errors__(resp)                
            
        # we're here, so go
        if 'x-hipmob-reason' in resp and self._message_sent_pattern.match(resp['x-hipmob-reason']) != None:
            return True
        else:
            return False

    def __send_json_message__(self, mobilekey, deviceid, content, **kwargs):
        if isinstance(content, basestring):
            # ensure it is a valid JSON object
            data = json.loads(content)
            data = content
        elif isinstance(content, dict):
            data = json.dumps(content)
        else:
            raise ValueError("Invalid JSON content specified.")

        # build the request
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        req = urllib2.Request(self._serverurl+'apps/'+mobilekey+'/devices/'+deviceid+"/messages")
        req.get_method = lambda: 'POST'
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)
        req.add_header("Content-Type", "application/json")
        if 'autocreate' in kwargs and kwargs['autocreate'] == True:
            req.add_header("X-Hipmob-Autocreate", 'true')
        req.add_data(data)
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)
        self.__check_for_errors__(resp)                
            
        # we're here, so go
        if 'x-hipmob-reason' in resp and self._message_sent_pattern.match(resp['x-hipmob-reason']) != None:
            return True
        else:
            return False

    def __send_binary_message__(self, mobilekey, deviceid, content, **kwargs):
        if not hasattr(content, 'read'):
            raise ValueError("Invalid binary content specified: must have a \"read\" method.")

        # build the request
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        req = urllib2.Request(self._serverurl+'apps/'+mobilekey+'/devices/'+deviceid+"/messages")
        req.get_method = lambda: 'POST'
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)
        req.add_header("Content-Type", "application/octet-stream")
        if 'autocreate' in kwargs and kwargs['autocreate'] == True:
            req.add_header("X-Hipmob-Autocreate", 'true')
        req.add_data(content.read())
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)
        self.__check_for_errors__(resp)                
            
        # we're here, so go
        if 'x-hipmob-reason' in resp and self._message_sent_pattern.match(resp['x-hipmob-reason']) != None:
            return True
        else:
            return False

    def __send_picture_message__(self, mobilekey, deviceid, picturefile, mimetype, **kwargs):
        # build the request
        if not os.path.exists(picturefile):
            raise ValueError("Invalid picture file specified.")

        statinfo = os.stat(picturefile)
        if statinfo == None or statinfo.st_size == 0:
            raise ValueError("Invalid picture file specified.")

        return self.__send_file_message__(mobilekey, deviceid, picturefile, mimetype, statinfo, **kwargs)

    def __send_audio_message__(self, mobilekey, deviceid, audiofile, mimetype, **kwargs):
        # build the request
        if not os.path.exists(audiofile):
            raise ValueError("Invalid audio file specified.")

        statinfo = os.stat(audiofile)
        if statinfo == None or statinfo.st_size == 0:
            raise ValueError("Invalid audio file specified.")

        return self.__send_file_message__(mobilekey, deviceid, audiofile, mimetype, statinfo, **kwargs)

    def __send_file_message__(self, mobilekey, deviceid, filename, mimetype, statinfo, **kwargs):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        req = urllib2.Request(self._serverurl+'apps/'+mobilekey+'/devices/'+deviceid+"/messages")
        req.add_data(open(filename, 'rb').read())
        req.get_method = lambda: 'POST'
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)
        req.add_header("Content-Type", mimetype)
        req.add_header("Content-Length", str(statinfo.st_size))
        if 'autocreate' in kwargs and kwargs['autocreate'] == True:
            req.add_header("X-Hipmob-Autocreate", 'true')

        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)
        self.__check_for_errors__(resp)                
            
        # we're here, so go
        if 'x-hipmob-reason' in resp and self._message_sent_pattern.match(resp['x-hipmob-reason']) != None:
            return True
        else:
            return False

    def __list_friends__(self, mobilekey, deviceid):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        req = urllib2.Request(self._serverurl+'apps/'+mobilekey+'/devices/'+deviceid+"/friends")
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)  
        u = None
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)
            
        self.__check_for_errors__(resp)
        res = []

        if 'content-type' in resp:
            if resp['content-type'] == 'application/vnd.com.hipmob.DeviceFriends+json; version=1.0':
                sourcedata = json.loads(u.read())
                if 'pagesize' in sourcedata and sourcedata['pagesize'] > 0 and 'friends' in sourcedata:
                    for x in sourcedata['friends']:
                        res.append(Hipmob.HipmobDevice(self, mobilekey, x))
            else:
                raise ValueError("Invalid response type ["+resp['content-type']+"]")
        else:
            raise ValueError("Invalid response type (No Content-Type header)")
        return res

    def __remove_friends__(self, mobilekey, deviceid, friendids):
        res = 0
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        for friendid in friendids:
            req = urllib2.Request(self._serverurl+'apps/'+mobilekey+'/devices/'+deviceid+"/friends/"+friendid)
            req.get_method = lambda: 'DELETE'
            req.add_header("Authorization", "Basic %s" % base64string)  
            u = None
            resp = None
            try:
                u = opener.open(req)
                resp = dict(u.info())
            except urllib2.HTTPError, e:
                self.__handle_error__(e, resp)
            
            self.__check_for_errors__(resp)

            if 'x-hipmob-reason' in resp:
                if self._friend_removed_pattern.match(resp['x-hipmob-reason']) != None:
                    res = res + 1
                elif self._no_changes_made_pattern.match(resp['x-hipmob-reason']) == None:
                    raise ValueError("Invalid response from server: "+resp['x-hipmob-reason'])
            else:
                raise ValueError("Invalid response from server: "+resp['x-hipmob-reason'])

        return res

    def __remove_all_friends__(self, mobilekey, deviceid):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        req = urllib2.Request(self._serverurl+'apps/'+mobilekey+'/devices/'+deviceid+"/friends")
        req.get_method = lambda: 'DELETE'
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)  
        u = None
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)
            
        self.__check_for_errors__(resp)

        if 'x-hipmob-reason' in resp:
            match = self._all_friends_removed_pattern.match(resp['x-hipmob-reason'])
            if match != None:
                return int(match.group(1))
            else:
                if self._no_changes_made_pattern.match(resp['x-hipmob-reason']) != None:
                    return 0
                else:
                    raise ValueError("Invalid response from server: "+resp['x-hipmob-reason'])
        else:
            raise ValueError("No valid response from server")

    def __add_friends__(self, mobilekey, deviceid, friendids):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        txdata = { "friend": friendids }
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req = urllib2.Request(self._serverurl+'apps/'+mobilekey+'/devices/'+deviceid+"/friends")
        req.get_method = lambda: 'POST'
        req.add_data(urllib.urlencode(txdata, doseq=True))
        req.add_header("Authorization", "Basic %s" % base64string)  
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        u = None
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)
            
        self.__check_for_errors__(resp)
            
        if 'x-hipmob-reason' in resp:
            match = self._friends_set_pattern.match(resp['x-hipmob-reason'])
            if match != None:
                return int(match.group(1))
            else:
                if self._no_changes_made_pattern.match(resp['x-hipmob-reason']) != None:
                    return 0
                else:
                    raise ValueError("Invalid response from server: "+resp['x-hipmob-reason'])
        else:
            raise ValueError("Invalid response from server: "+resp['x-hipmob-reason'])

    def __set_friends__(self, mobilekey, deviceid, friendids):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        txdata = { "friend": friendids }
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req = urllib2.Request(self._serverurl+'apps/'+mobilekey+'/devices/'+deviceid+"/friends")
        req.get_method = lambda: 'PUT'
        req.add_data(urllib.urlencode(txdata, doseq=True))
        req.add_header("Authorization", "Basic %s" % base64string)  
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        u = None
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)
            
        self.__check_for_errors__(resp)
            
        if 'x-hipmob-reason' in resp:
            match = self._friends_set_pattern.match(resp['x-hipmob-reason'])
            if match != None:
                return int(match.group(1))
            else:
                if self._no_changes_made_pattern.match(resp['x-hipmob-reason']) != None:
                    return 0
                else:
                    raise ValueError("Invalid response from server: "+resp['x-hipmob-reason'])
        else:
            raise ValueError("Invalid response from server: "+resp['x-hipmob-reason'])

    def __set_user_status__(self, username, status, **kwargs):
        # build the request
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        txdata = { "status": status }
        req = urllib2.Request(self._serverurl+'user/'+username+'/status')
        req.get_method = lambda: 'POST'
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)
        req.add_data(urllib.urlencode(txdata))
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)
        self.__check_for_errors__(resp)                
            
        # we're here, so go
        if 'x-hipmob-reason' in resp and self._status_updated_pattern.match(resp['x-hipmob-reason']) != None:
            return True
        else:
            return False

    def __send_text_messages__(self, mobilekey, text, devices, **kwargs):
        # build the request
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        txtdata = urllib.urlencode({ "text": text })
        for device in devices:
            txtdata = txtdata + "&" + urllib.urlencode({'devices': device })
        req = urllib2.Request(self._serverurl+'apps/'+mobilekey+'/devices/messages')
        req.get_method = lambda: 'POST'
        base64string = base64.encodestring('%s:%s' % (self._username, self._apikey)).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % base64string)
        req.add_data(txtdata)
        resp = None
        try:
            u = opener.open(req)
            resp = dict(u.info())
        except urllib2.HTTPError, e:
            self.__handle_error__(e, resp)
        self.__check_for_errors__(resp)                
            
        # we're here, so go
        if 'x-hipmob-reason' in resp:
            match = self._multiple_messages_sent_pattern.match(resp['x-hipmob-reason'])
            if match != None:
                return int(match.group(1))
            elif self._message_sent_pattern.match(resp['x-hipmob-reason']) != None:
                return 1

        # no match: return false
        return False
