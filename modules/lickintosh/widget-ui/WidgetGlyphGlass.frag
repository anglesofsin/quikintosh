#version 440
layout(location=0) in vec2 v_TexCoord;
layout(location=0) out vec4 fragColor;
layout(binding=1) uniform sampler2D maskTex;
layout(binding=2) uniform sampler2D backTex;
layout(std140,binding=0) uniform buf {
 mat4 qt_Matrix; float qt_Opacity;
 vec2 size; vec2 screenOrigin; vec2 backgroundSize;
 float ringRadius; float thickness; float highlightStrength;
 float highlightWidth; float saturation; float lift;
};
float coverage(vec2 uv){
 if(uv.x<0.0 || uv.y<0.0 || uv.x>1.0 || uv.y>1.0)return 0.0;
 return texture(maskTex,uv).a;
}
void main(){
 float a=coverage(v_TexCoord);
 if(a<=0.003){fragColor=vec4(0.0);return;}
 vec2 stepSize=vec2(clamp(ringRadius,0.75,2.5))/max(size,vec2(1.0));
 float l=coverage(v_TexCoord-vec2(stepSize.x,0.0));
 float r=coverage(v_TexCoord+vec2(stepSize.x,0.0));
 float t=coverage(v_TexCoord-vec2(0.0,stepSize.y));
 float b=coverage(v_TexCoord+vec2(0.0,stepSize.y));
 vec2 gradient=vec2(r-l,b-t);
 float len=length(gradient);
 vec2 normal=len>0.0001 ? -gradient/len:vec2(0.0);
 float edge=clamp(1.0-min(min(l,r),min(t,b)),0.0,1.0);
 vec2 uv=(screenOrigin+v_TexCoord*size-normal*min(thickness,3.0)*edge)/max(backgroundSize,vec2(1.0));
 vec3 col=texture(backTex,clamp(uv,0.0,1.0)).rgb;
 float lum=dot(col,vec3(0.2126,0.7152,0.0722));
 col=mix(vec3(lum),col,saturation)+lift;
 // A restrained adaptive fill keeps the glyph legible without a second,
 // detached outline or a large-font-dependent lens displacement.
 vec3 tone=mix(vec3(0.96,0.98,1.0),vec3(0.08,0.10,0.14),smoothstep(0.40,0.75,lum));
 col=mix(col,tone,0.18);
 float facing=dot(normal,normalize(vec2(-0.5,-1.0)));
 float bevel=clamp(edge*highlightStrength,0.0,0.65);
 col=mix(col,vec3(1.0),bevel*max(0.0,facing));
 col=mix(col,vec3(0.05,0.07,0.10),bevel*0.45*max(0.0,-facing));
 fragColor=vec4(clamp(col,0.0,1.0)*a,a)*qt_Opacity;
}
