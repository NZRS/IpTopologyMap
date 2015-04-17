var deg_domain = [1, 250];

var radius = d3.scale.log()
        .domain(deg_domain)
        .range([5, 60]);

var border = d3.scale.linear()
        .domain(deg_domain)
        .range([2, 8]);

var edge_width = d3.scale.sqrt()
        .domain([1, 23000])
        .range([1, 20]);

var node_color = {
    'other': d3.scale.linear()
                .domain(deg_domain)
                .range(['limegreen', 'darkgreen']),
    'IX':    d3.scale.linear()
                .domain(deg_domain)
                .range(['#E34234', '#A40000']),
    'AU':    d3.scale.linear()
                .domain(deg_domain)
                .range(['#FFF066', '#E5CE15']),
    'NZ':    d3.scale.linear()
                .domain(deg_domain)
                .range(['#707070', 'black']),
    'priv':  d3.scale.linear()
                .domain(deg_domain)
                .range(['blue', 'blue'])
};

var config = {
    dataSource: '/misc/data/nz-ip-map.json',
    nodeTypes: { "country": ["AU", "NZ", "IX", "priv", "other"] },
    nodeLabels: { 'AU': 'Australian AS', 'NZ': 'New Zealand AS',
    'IX': 'Internet Exchange', 'priv': 'Private AS', 'other':
    'Other Country AS' },
    edgeTypes: [ 'p2c', 'p2p', 's2s', 'unk' ],
    edgeLabels: { 'p2c': 'Customer to Provider',
        'p2p': 'Peer to Peer',
        's2s': 'Sibling to Sibling',
        'unk': 'Unknown' },
    edgeStrike: function(e) { return edge_width(e._weight); },
    cluster: false,
    nodeCaption: function(n, i) { if (i == 0) { return n.name; } else { return "(" + n.id + ")"; }},
    nodeRadius: function(n) { return radius(n.degree); },
    nodeStrike: function(n) { return border(n.degree); },
    nodeColour: function(n) { return node_color[n.country](n.degree); },
    linkDistance: function(edge, k) { return 15; },
    preLoad: function() {
        // There is extra info in the input file we could use to
        // set the right domain for the color scales
        this.preLoad.caller.arguments[0].dr.forEach(function(d) {
            if (node_color[d.country]) {
                node_color[d.country].domain([d.min, d.max])
            }
        });
        // There is also information about the range of weights in the edges
        edge_width.domain(this.preLoad.caller.arguments[0].wr);
    },
    afterLoad: function() {
        jQuery(".progress-label").text("Complete!");
        document.title = "NZ IP Topology Map";
        d3.select("#brand-title").append("span")
            .html("NZ IP Topology Map");
        d3.select("#last_updated").append("h3")
            .attr("class", "legendHeader")
            .html("Data prepared on");
        d3.select("#last_updated").append("h4")
            .attr("class", "legendHeader")
            .html(this.afterLoad.caller.arguments[0].lastupdate);
        var mx = 0, my = 0;
        alchemy.nodes.forEach(function(n) {
            mx += n.x;
            my += n.y;
        });
        mx = mx / alchemy.nodes.length;
        my = my / alchemy.nodes.length;
        console.log("Xbar = " + mx + " Ybar = " + my);
        var g_width = d3.select("svg#alchemy-canvas g").node().getBBox().width,
            g_height = d3.select("svg#alchemy-canvas g").node().getBBox().height;
        var sy = alchemy.conf.graphHeight() / g_height,
            sx = alchemy.conf.graphWidth() / g_width;
        alchemy.conf.initialTranslate = [ -mx + (alchemy.conf.graphWidth() / 2), -my + (alchemy.conf.graphHeight() / 2)];
        alchemy.interactions.clickZoom("reset");
        // alchemy.conf.initialScale = Math.min(sx, sy);
        // alchemy.interactions.zoom().translate(alchemy.conf.initialTranslate);
        // alchemy.interactions.zoom().scale(alchemy.conf.initialScale);
        console.log("ScaleX = " + sx + " ScaleY = " + sy);
    },
    zoomControls: true,
    initialScale: 1.0,
    initialTranslate: [ -10000, -10000 ],
    scaleExtent: [ 1.0, 3.0 ],
    showFilters: true,
    showControlDash: true,
    nodeFilters: false,
    customFilters: true,
    showLegend: true,
    nodeLegend: true,
    edgeLegend: true,
    forceLocked: true
    };

alchemy.begin(config);
