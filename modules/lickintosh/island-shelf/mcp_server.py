"""Opt-in stdio MCP bridge. No network listener or shell evaluation."""
import argparse,base64,json,subprocess,sys,time
from pathlib import Path

class Server:
    def __init__(self,permissions=(),runner=None):
        self.permissions=set(permissions);self.runner=runner or self.ipc;self.calls=[]
    @staticmethod
    def ipc(target,method,*arguments):
        result=subprocess.run(['quickintosh','ipc','call',target,method,*arguments],capture_output=True,text=True,timeout=10)
        if result.returncode:raise ValueError('Quickintosh is unavailable')
        return result.stdout.strip()[:65536]
    def tools(self):
        def tool(name,description,properties,required=()):return dict(name=name,description=description,inputSchema=dict(type='object',properties=properties,required=list(required),additionalProperties=False))
        rows=[tool('quickintosh_status','Read shell and shelf availability; no file contents.',{})]
        if 'ui' in self.permissions:rows.append(tool('shelf_open','Open a shelf page.',{'page':dict(type='integer',minimum=0,maximum=14)},['page']))
        if 'files' in self.permissions:rows.append(tool('shelf_add_files','Add explicitly supplied local files to the file tray. Originals stay in place.',{'paths':dict(type='array',maxItems=256,items=dict(type='string'))},['paths']))
        if 'activities' in self.permissions:rows.append(tool('shelf_activity','Publish bounded progress for an agent or build.',{'id':dict(type='string',maxLength=120),'title':dict(type='string',maxLength=160),'subtitle':dict(type='string',maxLength=240),'progress':dict(type='number',minimum=0,maximum=1),'ttl':dict(type='integer',minimum=1,maximum=3600)},['id','title']))
        return rows
    def call(self,name,args):
        tool=next((t for t in self.tools() if t['name']==name),None)
        if tool is None:raise ValueError('Tool is not enabled. Launch the bridge with its explicit permission flag.')
        if not isinstance(args,dict) or set(args)-set(tool['inputSchema']['properties']):raise ValueError('Invalid tool arguments')
        if any(key not in args for key in tool['inputSchema']['required']):raise ValueError('Missing required argument')
        now=time.monotonic();self.calls=[t for t in self.calls if now-t<60]
        if len(self.calls)>=60:raise ValueError('Rate limit reached')
        self.calls.append(now)
        if name=='quickintosh_status':return json.dumps(dict(shell=self.runner('rice','state'),shelf=self.runner('shelf','status')))
        if name=='shelf_open':
            page=args['page']
            if type(page) is not int or not 0<=page<=14:raise ValueError('Page must be an integer from 0 to 14')
            return self.runner('shelf','open',str(page))
        if name=='shelf_add_files':
            paths=args['paths']
            if not isinstance(paths,list) or not 1<=len(paths)<=256:raise ValueError('Choose 1 to 256 local files')
            if any(not isinstance(p,str) or not Path(p).is_absolute() or not Path(p).exists() for p in paths):raise ValueError('Every path must identify an existing absolute local file')
            return self.runner('shelf','addFiles',base64.b64encode(json.dumps(paths,ensure_ascii=True).encode()).decode())
        if name=='shelf_activity':
            if any(not isinstance(args.get(k,''),str) or len(args.get(k,''))>limit for k,limit in [('id',120),('title',160),('subtitle',240)]):raise ValueError('Invalid activity text')
            if not args['id'].strip() or not args['title'].strip():raise ValueError('Activity id and title are required')
            progress=args.get('progress',0);ttl=args.get('ttl',60)
            if type(progress) not in (int,float) or not 0<=progress<=1 or type(ttl) is not int or not 1<=ttl<=3600:raise ValueError('Invalid progress or duration')
            return self.runner('shelf','activity',json.dumps(args))
    def dispatch(self,message):
        identifier=message.get('id');method=message.get('method');params=message.get('params',{})
        if identifier is None:return None
        response=dict(jsonrpc='2.0',id=identifier)
        if method=='initialize':response['result']=dict(protocolVersion='2025-03-26',capabilities=dict(tools=dict(listChanged=False)),serverInfo=dict(name='quickintosh-shelf',version='1.0.0'))
        elif method=='ping':response['result']={}
        elif method=='tools/list':response['result']=dict(tools=self.tools())
        elif method=='tools/call':
            try:text=self.call(params.get('name'),params.get('arguments',{}));response['result']=dict(content=[dict(type='text',text=text)],isError=False)
            except (ValueError,OSError,subprocess.SubprocessError) as error:response['result']=dict(content=[dict(type='text',text=str(error))],isError=True)
        else:response['error']=dict(code=-32601,message='Method not found')
        return response

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for permission in ('ui','files','activities'):parser.add_argument('--allow-'+permission,action='store_true')
    options=parser.parse_args();server=Server([key for key in ('ui','files','activities') if getattr(options,'allow_'+key)])
    while True:
        line=sys.stdin.readline(65537)
        if not line:break
        if len(line)>65536:
            while line and not line.endswith('\n'):line=sys.stdin.readline(65537)
            print(json.dumps(dict(jsonrpc='2.0',id=None,error=dict(code=-32700,message='Request too large'))),flush=True);continue
        try:
            if len(line)>65536:raise ValueError('Request too large')
            message=json.loads(line)
            if not isinstance(message,dict):raise ValueError('Request must be an object')
            response=server.dispatch(message)
        except (ValueError,TypeError,AttributeError):response=dict(jsonrpc='2.0',id=None,error=dict(code=-32700,message='Invalid request'))
        if response is not None:print(json.dumps(response),flush=True)

if __name__=='__main__':main()
