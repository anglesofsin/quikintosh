var index = [];
WorkerScript.onMessage = function(message) {
    if (message.type === "index") {
        index = indexPaths(message.paths);
        WorkerScript.sendMessage({type: "indexed"});
    } else if (message.type === "search") {
        WorkerScript.sendMessage({type: "results", serial: message.serial,
            query: message.query, paths: search(index, message.query, 40)});
    }
};
