function WSChannel(host, port, route) {

  var ws_path = 'ws://' + host + ':' + port + '/' + route;
  this.ws = new WebSocket(ws_path);

  var listeners = this.listeners = {};

  this.ws.onmessage = function (evt) {
    var received_msg = evt.data,
        obj = JSON.parse(received_msg);

    var handler = listeners[obj.handler];

    var resp;
    try {
      resp = JSON.parse(obj.response);
    } catch (e) {
      resp = obj.response;
    }

    handler(resp);
  };
  this.ws.onclose = function() {};
  this.ws.onopen = function() {};
}

var wsp = WSChannel.prototype;

wsp.send = function(msg){
  this.ws.send(msg);
}

wsp.register_listener = function(name, cb) {
  this.listeners[name] = cb;
}
