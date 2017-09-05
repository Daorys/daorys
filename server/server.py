import pymongo
from pymongo import MongoClient
import time
import tornado.ioloop
import tornado.web
from tornado.web import StaticFileHandler
import string
import random
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

dbusername = "daorys_rw"
dbpw = "somepw"

client = pymongo.MongoClient('127.0.0.1',27017)
db = client.daorys
db.authenticate(dbusername,dbpw)
users_coll = db.users
messages_coll = db.messages


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('Authorized-user')


class Root(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect('/login')
            return
        else:
            username = self.current_user
            self.redirect('/messages?u=%s' % username)


class Login(BaseHandler):
    def get(self):
        self.render('login.html', message='')

    def post(self):
        username = self.get_body_argument('username', None)
        password = self.get_body_argument('password', None)
        verified = self.verify(username, password)
        if verified:
            # Set cookie
            cookie_name = 'Authorized-user'
            cookie_value = username
            cookie_expiry = 1
            self.set_secure_cookie(name=cookie_name, value=cookie_value, expires_days=cookie_expiry)
            self.redirect('/messages?u=%s' % username)
        else:
            self.render('login.html', message='Invalid credentials')

    def verify(self, username, password):
        record = users_coll.find_one({'username':username})
        if record:
            if password == record.get('password'):
                return True
        return False


class Logout(BaseHandler):
    def get(self):
        self.clear_cookie('Authorized-user')
        self.redirect('/login')
        return


class Register(BaseHandler):
    def get(self):
        self.render('register.html', message='')

    def post(self):
        username = self.get_body_argument('username', None)
        password = self.get_body_argument('password', None)
        email = self.get_body_argument('email', None)
        available = self.check_availability(username)
        if not available:
            self.render('register.html', message='Username not available')
            return
        users_coll.insert({
            'username': username,
            'password': password,
            'email': email
        })
        self.redirect('/login')

    def check_availability(self, username):
        record = users_coll.find_one({'username':username})
        if record:
            return False
        else:
            return True
class conversation:
    msgs = []
    def __init__(self,other_party):
        self.other_party=other_party


class Messages(BaseHandler):
    def get_initiated_chats(self,username):
        a = messages_coll.find({"initiator":username})
        initiated_chats = []
        for b in a:
            other_party = b.get('receiver')
            chat = conversation(other_party)
            chat.msgs = []
            for message in b.get('messages'):
                if message.get("type") == 1:
                    chat.msgs.append("You: "+message.get('content'))
                else:
                    chat.msgs.append(other_party+": "+message.get('content'))
            initiated_chats.append(chat)
        return initiated_chats

    def get_nym_chats(self,username):
        a = messages_coll.find({"receiver":username})
        nym_chats = []
        for b in a:
            other_party = b.get('initiator_mask')
            chat = conversation(other_party)
            chat.msgs = []
            for message in b.get('messages'):
                if message.get("type") == 1:
                    chat.msgs.append(other_party+": "+message.get('content'))
                else:
                    chat.msgs.append("You: "+message.get('content'))
            nym_chats.append(chat)
        return nym_chats

    def get(self):
        username = self.get_query_argument('u', None)
        logged_username = self.current_user
        if not logged_username or logged_username != username:
            self.write('Not authorized')
            return
        initiated_chats = self.get_initiated_chats(username)
        nym_chats = self.get_nym_chats(username)
        self.render('messages.html', username=username,initiated_chats=initiated_chats,nym_chats=nym_chats)

class PostMessage(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        target_user = self.get_query_argument('search_user', None)
        record = users_coll.find_one({'username':target_user})
        if record:
            self.render('initiate.html', receiver=target_user)
        else:
            record_mask = messages_coll.find_one({'initiator_mask':target_user})
            if record_mask:
                self.render('initiate.html',receiver=None,receiver_mask=target_user)
            else:
                self.write('no such receiver user!')

    @tornado.web.authenticated
    def post(self):
        message = self.get_body_argument('comment', None)
        #print message, receiver, receiver_mask, sender
        receiver = self.get_body_argument('receiver', None)
        receiver_mask = self.get_body_argument('receiver_mask', None)
        sender = self.current_user
        timestamp = time.time()
        if receiver:
            record = messages_coll.find_one({'$and': [{"receiver":receiver}, {"initiator":sender}]})
            if not record:
                random_string = id_generator()
                messages_coll.insert({
                    "receiver":receiver,
                    "initiator":sender,
                    "initiator_mask":random_string,
                    'messages': [{'content': message, 'type': 1, 'timestamp': timestamp}]
                })
            else:
                messages_coll.update(
                        {'$and': [{"receiver":receiver}, {"initiator":sender}]},
                        {'$addToSet': {'messages': {'content': message, 'type': 1, 'timestamp': timestamp}}}
                )
            self.redirect('/messages?u={}#initiated_chats'.format(sender))
        elif receiver_mask:
            record = messages_coll.find_one({'$and': [{"initiator_mask":receiver_mask},{"receiver":sender}]})
            messages_coll.update(
                    {'$and': [{"initiator_mask":receiver_mask},{"receiver":sender}]},
                    {'$addToSet': {'messages': {'content': message, 'type': 2, 'timestamp': timestamp}}}
            )
            self.redirect('/messages?u={}#nym_chats'.format(sender))

settings = {
    'cookie_secret': 'Mysecret',
    'login_url': '/messages',
    'xsrf_cookies': False,
}


def make_app():
    return tornado.web.Application([
        (r"/", Root),
        (r"/login", Login),
        (r"/logout", Logout),
        (r"/register", Register),
        (r"/messages", Messages),
        (r"/post", PostMessage),
        # (r'^/static/(.*)', StaticFileHandler, {'path': '/Users/aastha.nandwani/asset-verification'}),
    ], **settings)

if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()
