
exports.show = function(req, res) {
  var readline = require('readline');
  var cp = require('child_process');
  var ns = cp.spawn('netstat', ['-plt']);
  var lineReader = readline.createInterface(ns.stdout,ns.stdin);

  var i=-4;
  lineReader.on('line',function(line){
    i++;
  });
  
  ns.on('close',function(code,signal){
    res.send(i.toString());
  });
}

