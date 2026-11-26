.pragma library
function normalize(value) {
    var text=String(value || '').split('?')[0];
    try{text=decodeURIComponent(text)}catch(e){}
    return text.split('/').pop().toLowerCase().replace(/\.(desktop|svg|png|ico|icns)$/,'').replace(/[ _]/g,'-');
}
function candidates(value) {
    var key=normalize(value),result=[key];
    var aliases={'chromium-browser':'chromium','google-chrome-stable':'google-chrome','com.google.chrome':'google-chrome','com.github.eloston.ungoogled-chromium':'ungoogled-chromium'};
    if(aliases[key])result.push(aliases[key]);
    // Flatpak/reverse-DNS IDs retain the app name in their final component.
    // Generic entry points must not impersonate a system application.
    if(/^[a-z0-9-]+(?:\.[a-z0-9-]+){2,}$/.test(key)){
        var last=key.split('.').pop();
        if(['app','main','client','desktop','settings','terminal','browser','launcher'].indexOf(last)<0){
            result.push(last);
            if(aliases[last])result.push(aliases[last]);
        }
    }
    return result;
}
function lookup(table,source,name) {
    var keys=candidates(name).concat(candidates(source));
    for(var i=0;i<keys.length;i++)if(table[keys[i]])return table[keys[i]];
    return '';
}
