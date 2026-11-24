/* Lickintosh voice metadata only. No tokens, messages or audio capture; explicit user call controls only. */
;(() => {
    const key = '__lickintoshVoiceBridge';
    if (globalThis[key]) return;
    globalThis[key] = true;
    let ws, reconnect, pending, common, lastChannel, joinedAt = 0, stopped = false;
    const speaking = new Map();
    const subscriptions = [];
    const stores = [];
    let lastSnapshot = "";
    const nativeChannel=globalThis.__lickintoshVoiceClient || globalThis.DiscordNative?.app?.getReleaseChannel?.();
    const client = ['canary','ptb','stable','equibop'].includes(nativeChannel) ? nativeChannel : globalThis.VesktopNative ? 'equibop'
        : location.hostname.startsWith('canary.') ? 'canary'
        : location.hostname.startsWith('ptb.') ? 'ptb' : 'stable';
    function incoming() {
        const self=common?.UserStore?.getCurrentUser();
        const calls=common?.CallStore?.getAllCalls?.() || {};
        return Object.values(calls).find(c=>Array.isArray(c?.ringing) && c.ringing.includes(self?.id)) || null;
    }
    function snapshot() {
        if (ws?.readyState !== WebSocket.OPEN || !common) return;
        try {
            const {UserStore, VoiceStateStore, ChannelStore, GuildStore, GuildMemberStore, StreamerModeStore, ChannelRTCStore, MediaEngineStore} = common;
            const self = UserStore.getCurrentUser();
            const ringing=incoming();
            const joinedId = (self && VoiceStateStore.getVoiceStateForUser?.(self.id)?.channelId) || common.SelectedChannelStore?.getVoiceChannelId?.();
            const channelId=ringing?.channelId || ringing?.channel_id || joinedId;
            const state=ringing ? 'incoming':joinedId ? 'active':'idle';
            if (channelId !== lastChannel) { speaking.clear(); lastChannel = channelId; joinedAt = Date.now(); }
            const channel = channelId && ChannelStore?.getChannel?.(channelId);
            const guildId = channel?.guild_id || channel?.guildId;
            const guild = guildId ? GuildStore?.getGuild?.(guildId) : null;
            const states = channelId ? Object.values(VoiceStateStore.getVoiceStatesForChannel?.(channelId) || {}) : [];
            let rtc = [];
            try { rtc = ChannelRTCStore?.getSpeakingParticipants(channelId) || []; } catch {}
            // Local audio controls update before gateway voice state, including offline.
            let localMute, localDeaf;
            try { localMute=MediaEngineStore?.getSelfMute(); localDeaf=MediaEngineStore?.getSelfDeaf(); } catch {}
            if(channelId && self && !states.some(s=>s.userId===self.id)) states.push({userId:self.id,channelId});
            const participants = states.slice(0, 64).map(s => {
                const user = UserStore.getUser(s.userId);
                const hash = user?.avatar;
                return {id:s.userId, name:(guildId ? GuildMemberStore?.getNick?.(guildId, s.userId) : null) || user?.globalName || user?.username || 'Participant',
                    avatar:hash ? `https://cdn.discordapp.com/avatars/${s.userId}/${hash}.png?size=80` : '',
                    self:s.userId === self.id, muted:s.userId===self.id && typeof localMute==="boolean" ? !!(localMute || localDeaf || s.mute) : !!(s.mute || s.selfMute),
                    deaf:s.userId===self.id && typeof localDeaf==="boolean" ? !!(localDeaf || s.deaf) : !!(s.deaf || s.selfDeaf),
                    speaking:speaking.has(s.userId) ? speaking.get(s.userId) : rtc.some(p => p.user?.id === s.userId && p.speaking)};
            });
            // Recipients exist before remote voice states: ringing DMs must not
            // depend on the other participant having joined the channel.
            const recipients = !guildId ? (channel?.recipients || channel?.getRecipientIds?.() || [])
                .map(value=>typeof value==='string' ? value:value?.id).filter(id=>id && id!==self?.id)
                .map(id=>UserStore.getUser(id)).filter(Boolean) : [];
            const recipientNames=recipients.map(user=>user.globalName || user.global_name || user.username).filter(Boolean);
            const recipient=recipients[0];
            let recipientAvatar='';
            try { recipientAvatar=recipient?.getAvatarURL?.(null,80,false) || ''; } catch {}
            if(!recipientAvatar && recipient?.avatar)recipientAvatar=`https://cdn.discordapp.com/avatars/${recipient.id}/${recipient.avatar}.png?size=80`;
            const payload=JSON.stringify({type:'voice', version:1, client, active:!!channelId, state,
                channelId:channelId || '', channel:channel?.name || recipientNames.join(', ') || participants.filter(p=>!p.self).map(p=>p.name).join(', ') || 'Private call',
                guild:guild?.name || '', joinedAt, controls:true,
                incomingControls:!!ringing && typeof common.VoiceActions?.selectVoiceChannel==='function' && typeof common.CallActions?.stopRinging==='function',
                image:guild?.icon
                    ? `https://cdn.discordapp.com/icons/${guildId}/${guild.icon}.png?size=80`
                    : channel?.icon ? `https://cdn.discordapp.com/channel-icons/${channelId}/${channel.icon}.png?size=80`
                    : recipientAvatar || participants.find(p=>!p.self)?.avatar || '',
                streamer:!!StreamerModeStore?.enabled, participants});
            if(payload!==lastSnapshot) {ws.send(payload);lastSnapshot=payload;}
        } catch { /* Discord stores can be temporarily unavailable during login. */ }
    }
    function schedule() { if (!pending) pending = setTimeout(() => {pending = null; snapshot();}, 35); }
    function connect() {
        if (stopped) return;
        ws = new WebSocket('ws://127.0.0.1:6891/voice');
        ws.onopen = () => {lastSnapshot=""; snapshot();};
        ws.onmessage = event => {
            try {
                const data=JSON.parse(event.data);
                const self=common.UserStore.getCurrentUser();
                if(data.type!=="control" || !self)return;
                if(['accept','reject'].includes(data.action)){
                    const ring=incoming();
                    if(!ring || data.channelId!==(ring.channelId || ring.channel_id))return;
                    if(data.action==='accept')common.VoiceActions?.selectVoiceChannel?.(data.channelId);
                    else common.CallActions?.stopRinging?.(data.channelId,[self.id]);
                    schedule();return;
                }
                if(data.channelId!==common.VoiceStateStore.getVoiceStateForUser?.(self.id)?.channelId) return;
                const actions={mute:"AUDIO_TOGGLE_SELF_MUTE",deaf:"AUDIO_TOGGLE_SELF_DEAF",disconnect:"VOICE_CHANNEL_SELECT"};
                if(!actions[data.action]) return;
                common.FluxDispatcher.dispatch(data.action==="disconnect" ? {type:actions[data.action],channelId:null}
                    : {type:actions[data.action],syncRemote:true,playSoundEffect:true,context:"default"});
                schedule();
            } catch {}
        };
        ws.onerror = () => ws.close();
        ws.onclose = () => { if (!stopped) reconnect = setTimeout(connect, 2500); };
    }
    async function init() {
        const api = globalThis.Vencord || globalThis.Equicord;
        if (api?.Webpack?.onceReady) await api.Webpack.onceReady;
        if (stopped) return;
        common = Object.assign({},api?.Webpack?.Common || {});
        // Store exports move between builds; resolve by identity and capability,
        // without depending on webpack numeric module IDs or source file paths.
        let require;
        try{globalThis.webpackChunkdiscord_app?.push([[Symbol('lickintosh-voice')],{},r=>{require=r}]);}catch{}
        const exports=[];
        if(require?.c)for(const module of Object.values(require.c)){
            const value=module?.exports;if(!value)continue;
            exports.push(value);try{for(const v of Object.values(value))if(v && (typeof v==='object'||typeof v==='function'))exports.push(v)}catch{}
        }
        const names=['VoiceStateStore','UserStore','ChannelStore','GuildStore','GuildMemberStore','StreamerModeStore','ChannelRTCStore','MediaEngineStore','SelectedChannelStore','CallStore'];
        for(const name of names)if(!common[name]){
            try{common[name]=api?.Webpack?.findStore?.(name)}catch{}
            if(!common[name])common[name]=exports.find(value=>{try{return value.getName?.()===name}catch{return false}});
        }
        if(!common.FluxDispatcher)common.FluxDispatcher=exports.find(v=>typeof v.dispatch==='function' && typeof v.subscribe==='function' && typeof v.unsubscribe==='function');
        common.VoiceActions=exports.find(v=>typeof v.selectVoiceChannel==='function') || common.VoiceActions;
        common.CallActions=exports.find(v=>typeof v.stopRinging==='function') || common.CallActions;
        if (!common?.VoiceStateStore || !common?.UserStore || !common?.FluxDispatcher) {
            reconnect = setTimeout(init, 2000); return;
        }
        for (const type of ['CALL_CREATE','CALL_UPDATE','CALL_DELETE','CALL_RING','CALL_STOP_RINGING','VOICE_STATE_UPDATES','RTC_CONNECTION_STATE','CONNECTION_OPEN','CURRENT_USER_UPDATE','STREAMER_MODE_UPDATE','AUDIO_TOGGLE_SELF_MUTE','AUDIO_TOGGLE_SELF_DEAF','AUDIO_SET_SELF_MUTE','AUDIO_SET_SELF_DEAF']) {
            const handler = () => { if(type === 'CONNECTION_OPEN') speaking.clear(); schedule(); };
            common.FluxDispatcher.subscribe(type, handler); subscriptions.push([type,handler]);
        }
        const handler = e => { speaking.set(e.userId, !!(e.speakingFlags & 1)); schedule(); };
        common.FluxDispatcher.subscribe('SPEAKING', handler); subscriptions.push(['SPEAKING',handler]);
        for(const store of [common.CallStore,common.MediaEngineStore,common.VoiceStateStore,common.UserStore,common.ChannelStore]) {
            if(store?.addChangeListener) {store.addChangeListener(schedule);stores.push(store);}
        }
        connect();
    }
    addEventListener('beforeunload', () => {
        stopped = true; clearTimeout(reconnect); clearTimeout(pending);
        for(const [type,handler] of subscriptions) common?.FluxDispatcher.unsubscribe(type,handler);
        for(const store of stores) store.removeChangeListener?.(schedule);
        ws?.close(); speaking.clear();
    }, {once:true});
    init();
})();
