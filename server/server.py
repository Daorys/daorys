import pymongo
from pymongo import MongoClient
import time
import tornado.ioloop
import tornado.web
from tornado.web import StaticFileHandler

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


class Messages(BaseHandler):
    def get(self):
        username = self.get_query_argument('u', None)
        logged_username = self.current_user
        if not logged_username or logged_username != username:
            self.write('Not authorized')
            return
        self.render('messages.html', username=username)


class PostMessage(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        target_user = self.get_query_argument('search_user', None)
        record = users_coll.find_one({'username':target_user})
        if record:
            self.render('initiate.html', receiver=target_user)
        else:
            self.write('no such receiver user!')

    @tornado.web.authenticated
    def post(self):
        message = self.get_body_argument('comment', None)
        receiver = self.get_body_argument('receiver', None)
        sender = self.current_user
        timestamp = time.time()
        record = messages_coll.find_one({'$and': [{'receiver':receiver}, {'sender': sender}]})
        if not record:
            messages_coll.insert({
                'receiver': receiver,
                'sender': sender,
                'messages': [{'content': message, 'sender': sender, 'timestamp': timestamp}]
            })

        else:
            messages_coll.update(
                {'$and': [{'receiver': receiver}, {'sender': sender}]},
                {'$addToSet': {'messages': {'content': message, 'sender': sender, 'timestamp': timestamp}}}
            )

        self.write('Send message %s to %s from %s' % (message, receiver, sender))

settings = {
    'cookie_secret': 'Mysecret',
    'login_url': '/login',
    'xsrf_cookies': True,
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
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
