import os
from collections import defaultdict

import numpy as np
import pandas as pd

import pandasjson
import _pandasujson as json

import tornado.httpserver
import tornado.web
import tornado.websocket as websocket
import tornado.ioloop

# Serve up the colormap
class ColorMapHandler(tornado.web.RequestHandler):

    def get(self):
        self.write(open("colormap.html").read())

# Serve up the force diagram
class ForceVectorHandler(tornado.web.RequestHandler):

    def get(self):
        self.write(open("force.html").read())

# Implement the websocket server
class DataSocket(websocket.WebSocketHandler):
    """
    handle inbound messages
    dispatch to appropriate data methods
    send back a response
    """

    def on_message(self, message):
        request = json.loads(message)
        handler = self._get_handler(request)
        frame = SOURCES[request['source']]
        resp = handler(request, frame)
        return self._respond(resp, request['handler'])

    def _respond(self, response, handler):
        output = {'response': response,
                  'handler': handler}
        result = json.dumps(output);
        self.write_message(unicode(result))

    def _get_handler(self, req):
        kind = req.get('type', 'data')
        return getattr(self, 'handle_%s' % kind)

    def allow_draft76(self):
        return True

    def handle_agg(self, request, frame):
        return aggregate(frame, request).to_json(orient='records')

    def handle_agg_force(self, request, frame):
        return json.dumps(get_force_data(frame, request))

    def handle_refresh(self, request, frame):
        vname = request['source']
        store = pd.HDFStore('fec.h5')
        SOURCES[vname] = store['fec']
        store.close()
        return vname + ' updated'

# Utility method to do aggregations
def aggregate(frame, req):
    print 'aggregating'
    spec = req['spec']
    subset = frame.ix[:, spec.keys()]
    dropna_keys = [k for k, v in spec.iteritems() if 'dropna' in v]
    subset = subset.dropna(subset=dropna_keys)

    for k, v in spec.iteritems():
        if 'in' in v:
            subset = subset[subset[k].isin(v['in'])]

    group_keys = [k for k, v in spec.iteritems() if 'agg' not in v]
    grouped = subset.groupby(group_keys)

    agg_keys = [k for k, v in spec.iteritems() if 'agg' in v]
    rs = grouped.agg({k: spec[k]['agg'] for k in agg_keys})

    print rs
    return rs.reset_index()

# Generate the tree structure for the force diagram
def get_force_data(frame, req):
    print 'force'
    keys = ['PoliticalParty', 'State', 'Employer'];
    subset = frame.ix[frame.PoliticalParty.isin(['DEM', 'GOP'])]

    rs = subset.groupby(keys).Amount.sum().reset_index()

    def get_top10(x):
        head = x.sort('Amount', ascending=False).head(10)
        return head.set_index(['Employer']).ix[:, ['Amount']]

    top10 = rs.groupby(keys[:-1]).apply(get_top10)

    def to_records(df):
        if df.index.nlevels == 1:
            df = df.ix[:, ['Amount']]
            df.index.name = 'name'
            df.columns = ['size']
            return df.reset_index().to_json(orient='records')
        else:
            rs = []
            grouped = df.groupby(level=0)
            for k, v in grouped:
                rs.append({'name': k,
                           'children': to_records(v.reset_index(0, drop=True))})
            return rs

    return {'name': "contributions", 'children': to_records(top10)}

# static file directory
settings = {
    'static_path': os.path.dirname(__file__).rsplit('/')[0]
}

# inport the FEC data
fpath = os.path.expanduser('~/Dropbox/data/fec.h5')
store = pd.HDFStore(fpath)
fec = store['fec_full']
store.close()

if __name__ == '__main__':
    import sys
    args = sys.argv[1:]

    SOURCES = {'fec' : fec}
    print 'data loaded'

    application = tornado.web.Application([
        (r'/colormap', ColorMapHandler),
        (r'/force', ForceVectorHandler),
        (r'/websocket', DataSocket),
        (r"/static/(.*)", tornado.web.StaticFileHandler,
         dict(path=settings['static_path']))
    ], **settings)

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8877)
    tornado.ioloop.IOLoop.instance().start()
