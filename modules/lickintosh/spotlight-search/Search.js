function normalize(value) {
    return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}
function indexPaths(paths) {
    return paths.map(function(path) {
        var value=normalize(path),name=value.slice(value.lastIndexOf('/')+1);
        return {path:path,value:value,name:name};
    });
}
function search(index, query, limit) {
    var words=normalize(query).trim().split(/\s+/).filter(Boolean);
    if(!words.length)return [];
    var ranked=[],count=Math.max(1,Math.min(100,limit || 30));
    for(var i=0;i<index.length;i++) {
        var item=index[i],score=0,matched=true;
        for(var j=0;j<words.length;j++) {
            var word=words[j],position=item.name.indexOf(word);
            if(position===0)score+=100;
            else if(position>0)score+=60;
            else if(item.value.indexOf(word)>=0)score+=10;
            else {matched=false;break;}
        }
        if(!matched)continue;
        if(item.name===words.join(' ') || item.name.replace(/\.[^.]+$/,'')===words.join(' '))score+=200;
        var result={path:item.path,score:score,order:i};
        var at=0;while(at<ranked.length && ranked[at].score>=score)at++;
        if(at<count){ranked.splice(at,0,result);if(ranked.length>count)ranked.pop();}
    }
    return ranked.map(function(item){return item.path;});
}
