"""Sample only the wallpaper's menu-bar strip, once per wallpaper/display change."""
import json,subprocess,sys,os,urllib.parse

def foreground(rgb):
    values=[v/255 for v in rgb]
    linear=[v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4 for v in values]
    luminance=sum(x*w for x,w in zip(linear,[.2126,.7152,.0722]))
    return '#17171a' if (luminance+.05)/(.00872+.05) > (.95597+.05)/(luminance+.05) else '#fafafa'

def sample(path,screens):
    expanded=os.path.expanduser(urllib.parse.unquote(path[7:]) if path.startswith('file://') else path)
    out={}
    for screen in screens:
        width=max(1,int(screen['width']));height=max(32,int(screen['height']))
        try:
            pixels=subprocess.check_output(['magick',expanded+'[0]','-auto-orient','-resize',f'{width}x{height}^','-gravity','center','-extent',f'{width}x{height}','-gravity','north','-crop',f'{width}x32+0+0','+repage','-resize','2x1!','-colorspace','sRGB','-depth','8','rgb:-'],stderr=subprocess.DEVNULL,timeout=10)
            if len(pixels)==6:out[screen['name']]={'left':foreground(pixels[:3]),'right':foreground(pixels[3:])}
        except (OSError,subprocess.SubprocessError):pass
    return {'path':path,'screens':out}
if __name__=='__main__':print(json.dumps(sample(sys.argv[1],json.loads(sys.argv[2]))))
