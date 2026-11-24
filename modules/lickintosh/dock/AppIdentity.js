.pragma library
function discordKey(value) {
    const text=String(value || '').toLowerCase();
    const patterns=[['discord-canary','discord[-_. ]?canary'],['discord-ptb','discord[-_. ]?ptb'],['equibop','equibop'],['discord','discord(?:[-_. ]stable)?']];
    for(const pair of patterns)if(new RegExp('(?:^|[/_. -])'+pair[1]+'(?:$|[/_. -])').test(text))return pair[0];
    return '';
}
function same(a,b) {
    if(!a || !b)return false;
    const left=discordKey(a),right=discordKey(b);
    if(left || right)return !!left && left===right;
    return a.indexOf(b)>=0 || b.indexOf(a)>=0;
}
