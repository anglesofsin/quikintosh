#version 440
layout(location=0) in vec2 qt_TexCoord0;
layout(location=0) out vec4 fragColor;
layout(std140,binding=0) uniform buf {
 mat4 qt_Matrix;
 float qt_Opacity;
 vec2 surfaceSize;
 vec4 cornerRadii;
 vec4 backgroundColor;
 vec4 borderColor;
 float borderWidth;
};
layout(binding=1) uniform sampler2D contentTexture;
void main(){
 vec2 halfSize=surfaceSize*.5;
 vec2 p=qt_TexCoord0*surfaceSize-halfSize;
 float r=p.x<0. ? (p.y<0. ? cornerRadii.x:cornerRadii.w):(p.y<0. ? cornerRadii.y:cornerRadii.z);
 r=clamp(r,0.,min(halfSize.x,halfSize.y));
 vec2 q=abs(p)-halfSize+r;
 float d=length(max(q,0.))+min(max(q.x,q.y),0.)-r;
 float aa=max(fwidth(d),1.);
 float coverage=clamp(.5-d/aa,0.,1.);
 float inner=clamp(.5-(d+borderWidth)/aa,0.,1.);
 float band=borderWidth>0. ? clamp(1.-inner/max(coverage,.0001),0.,1.):0.;
 vec4 content=texture(contentTexture,qt_TexCoord0);
 vec4 base=content+backgroundColor*(1.-content.a);
 fragColor=(base*(1.-borderColor.a*band)+borderColor*band)*coverage*qt_Opacity;
}
