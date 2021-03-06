#!/usr/bin/env python

import os
import logging
import json

import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.web
from tornado.web import asynchronous
from tornado import gen
from tornado.options import define, options

from tornado_stripe import Stripe

#import psycopg2
#import momoko


define("environment", default="development", help="Pick you environment", type=str)
define("site_title", default="Pop-Up Payment Page", help="Site Title", type=str)
define("cookie_secret", default="sooooooosecret", help="Your secret cookie dough", type=str)
define("port", default="8000", help="Listening port", type=str)
define("stripe_publishable_key", default="Your Stripe public key", help="", type=str)
define("stripe_private_key", default="Your Stripe private key", help="", type=str)

tornado.options.parse_command_line()
stripe = Stripe(options.stripe_private_key, blocking=False)


# Load plans from JSON file, move to DB
stripe_plans  = json.load(open('plans.json', 'rb'))



 

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db


class LandingHandler(BaseHandler):
    def get(self):
        self.render("main.html")

    @gen.coroutine
    def post(self):
        self.token = self.get_argument('stripeToken', False)
        self.plan = self.get_argument('planId', False)
        self.email = self.get_argument('email', False)
 
        if self.token:
            self.PLAN = {
                    'source': self.token,
                    'plan':   self.plan,
                    'email':  self.email
                   }
            resp = yield stripe.customers.post(**self.PLAN)
            self.redirect("/thank-you")


class ThankyouHandler(BaseHandler):
    def get(self):
        self.render("thank-you.html")


class ApiHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        pass


class FourOhFourHandler(BaseHandler):
    def get(self, slug):
        self.render("404.html")


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
           (r"/", LandingHandler),
           (r"/api", ApiHandler),
           (r"/thank-you", ThankyouHandler),
           (r"/([^/]+)", FourOhFourHandler),
        ]
        settings = dict(
            site_title=options.site_title,
            stripe_publishable_key=options.stripe_publishable_key,
            plans=stripe_plans,
            cookie_secret=options.cookie_secret,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            debug=True,
        )

        #application.db = momoko.Pool(
        #    dsn='dbname=your_db user=your_user password=very_secret_password '
        #        'host=localhost port=5432',
        #    size=1
        #)

        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    print "Server listening on port " + str(options.port)
    logging.getLogger().setLevel(logging.DEBUG)
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
