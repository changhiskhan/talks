// lifted from bl.ocks.org/mbostock/

var conn = new WSChannel('localhost', 8877, 'websocket');

function onresult(records) {
  var normdata = {numer: {}, denom: {}};
  _.each(records,
         function (r) {
           if (r.Amount !== r.Amount) { r.Amount = 0; }
           if (r.PoliticalParty === 'DEM') {
             normdata.numer[r.StateID] = r.Amount;
           }
           normdata.denom[r.StateID] = (normdata.denom[r.StateID] || 0) + r.Amount;
         });
  var data = {};
  for (var st in normdata.numer) {
    data[st] = normdata.numer[st] / normdata.denom[st];
  }

  var color_scale = d3.scale.linear()
                    .domain([0., 1.])
                    .range(["red", "blue"]);

  var svg = d3.select("body").append("svg")
            .attr("width", 1000)
            .attr("height", 800);

  d3.json("static/us.json", function(whatevs, us) {
    //fill color
    svg.append("g")
    .selectAll("path")
    .data(topojson.object(us, us.objects.states).geometries)
    .enter()
    .append("path")
    .attr('d', d3.geo.path())
    .style("fill", function(d) { return color_scale(data[d.id]); });

    // borders
    svg.append("path")
    .datum(topojson.mesh(us, us.objects.states,
                         function(a, b) { return a.id !== b.id; }))
    .attr("class", "states")
    .attr("d", d3.geo.path());
  });
}

conn.register_listener('handle_agg_response', onresult);
setTimeout(function () {
  conn.send(JSON.stringify({source: 'fec',
                            type: 'agg',
                            handler: 'handle_agg_response',
                            spec: {Amount : {agg: 'sum'},
                                   PoliticalParty: {axis: 1},
                                   StateID : {dropna: true}}}));
  }, 250);