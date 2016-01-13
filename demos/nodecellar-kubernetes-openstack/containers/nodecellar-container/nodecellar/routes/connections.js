
exports.show = function(req, res) {
  var readline = require('readline');
  var cp = require('child_process');
  var ns = cp.spawn('netstat', ['-pnat']);
  var lineReader = readline.createInterface(ns.stdout,ns.stdin);

  var i=-1;
  lineReader.on('line',function(line){
    var val=line.split(/[ ]+/)[3].split(/:/)[1];
    if(val==="3000")i++;
  });
  
  ns.on('close',function(code,signal){
    res.send(i.toString());
  });
}

