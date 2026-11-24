from pathlib import Path
import sys
root=Path(sys.argv[1]);here=Path(__file__).parent;p=root/'ui/topbar/statusarea/spotlight/SpotlightWindow.qml';s=p.read_text();s='import "Search.js" as FileSearch\n'+s
s=s.replace('readonly property var lowercaseFileIndex: root.fileIndex.map(function(path) { return path.toLowerCase() })','readonly property var searchableFileIndex:FileSearch.indexPaths(root.fileIndex)')
a=s.index('    function searchIndex(query, limit) {');z=s.index('\n    property bool _spotlightLoaded:',a)
s=s[:a]+'''    function searchIndex(query, limit) {
        return FileSearch.search(root.searchableFileIndex,query,limit)
    }
'''+s[z:]
p.chmod(p.stat().st_mode|0o200);p.write_text(s);(p.parent/'Search.js').write_text((here/'Search.js').read_text())
