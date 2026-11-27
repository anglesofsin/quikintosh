"""Bounded, offline developer transformations; never evaluates pasted code."""
import base64
import hashlib
import json
import uuid
import html
import datetime
from urllib.parse import quote,unquote


def transform(text,operation):
    if not isinstance(text,str) or len(text)>1024*1024:raise ValueError('Input is limited to 1 MiB')
    if operation=='html':return html.escape(text)
    if operation=='unhtml':return html.unescape(text)
    if operation=='hex':return text.encode().hex()
    if operation=='unhex':return bytes.fromhex(text).decode()
    if operation=='lines':return '\n'.join(sorted(text.splitlines()))
    if operation=='unique':return '\n'.join(dict.fromkeys(text.splitlines()))
    if operation=='count':return json.dumps(dict(characters=len(text),words=len(text.split()),lines=len(text.splitlines())),indent=2)
    if operation=='timestamp':
        value=float(text.strip())
        if abs(value)>100000000000:value/=1000
        return datetime.datetime.fromtimestamp(value,datetime.timezone.utc).isoformat()
    if operation=='json':return json.dumps(json.loads(text),ensure_ascii=False,indent=2)
    if operation=='minify':return json.dumps(json.loads(text),ensure_ascii=False,separators=(',',':'))
    if operation=='base64':return base64.b64encode(text.encode()).decode()
    if operation=='unbase64':return base64.b64decode(text.strip(),validate=True).decode()
    if operation=='url':return quote(text,safe='')
    if operation=='unurl':return unquote(text,errors='strict')
    if operation=='uuid':return str(uuid.uuid4())
    if operation=='sha256':return hashlib.sha256(text.encode()).hexdigest()
    if operation=='sha512':return hashlib.sha512(text.encode()).hexdigest()
    if operation=='jwt':
        parts=text.strip().split('.')
        if len(parts)!=3:raise ValueError('Enter a three-part JWT')
        def decode(value):return json.loads(base64.urlsafe_b64decode(value+'='*((4-len(value)%4)%4)))
        return json.dumps(dict(header=decode(parts[0]),payload=decode(parts[1]),signatureVerified=False),ensure_ascii=False,indent=2)
    raise ValueError('Unknown developer tool')
