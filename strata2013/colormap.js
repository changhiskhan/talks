function onresult(records) {
  /*
   * We will get contributions to each party 
   * So just need to normalize it to get % DEM (vs GOP)
   */
  var normdata = {numer: {}, denom: {}};
  _.each(records,
         function (r) {
           if (r.Amount !== r.Amount) { r.Amount = 0; }
           if (r.PoliticalParty === 'DEM') {
             normdata.numer[r.StateID] = r.Amount;
           }
           normdata.denom[r.StateID] = (normdata.denom[r.StateID] || 0) + r.Amount;
         });
    var data = {}, numer, denom;

  for (var st in normdata.numer) {
    numer = normdata.numer[st];
    denom = normdata.denom[st];
    if (numer === 0 && denom === 0) {
      data[st] = 0.5;
    } else {
      data[st] = numer / denom;
    }
  }

  // lifted from bl.ocks.org/mbostock/

  // red is 0% DEM and blue is 100% DEM
  var color_scale = d3.scale.linear()
                    .domain([0., 1.])
                    .range(["red", "blue"]);

  var svg = d3.select("body").append("svg")
            .attr("width", 1000)
            .attr("height", 800);

  // Request the base US map
  d3.json("static/us.json", function(whatevs, us) {

    //draw map and fill state colors
    var states = topojson.object(us, us.objects.states).geometries;
    var color = function(d) { return color_scale(data[d.id]); };

    svg.append("g")
    .selectAll("path")
    .data(states)
    .enter()
    .append("path")
    .attr('d', d3.geo.path())
    .style("fill", color);

    // draw borders
    svg.append("path")
    .datum(topojson.mesh(us, us.objects.states,
                         function(a, b) { return a.id !== b.id; }))
    .attr("class", "states")
    .attr("d", d3.geo.path());
  });
}

/*
 * Create a new client, hook up to the server, and request the data
 */
var conn = new WSChannel('localhost', 8877, 'websocket');
conn.register_listener('handle_agg_response', onresult);
setTimeout(function () {
  conn.send(JSON.stringify({source: 'fec',
                            type: 'agg',
                            handler: 'handle_agg_response',
                            spec: {Amount : {agg: 'sum'},
                                   PoliticalParty: {axis: 1},
                                   StateID : {dropna: true}}}));
  }, 250);