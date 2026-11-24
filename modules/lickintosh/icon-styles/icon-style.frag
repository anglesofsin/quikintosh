#version 440
layout(location=0) in vec2 qt_TexCoord0;
layout(location=0) out vec4 fragColor;
layout(std140,binding=0) uniform buf {
 mat4 qt_Matrix;
 float qt_Opacity;
 vec4 lowColor;
 vec4 highColor;
 float treatment;
 float strength;
};
layout(binding=1) uniform sampler2D source;
void main(){
 vec4 pixel=texture(source,qt_TexCoord0);
 vec3 rgb=pixel.a>0.0001 ? pixel.rgb/pixel.a:vec3(0.0);
 float lum=dot(rgb,vec3(0.2126,0.7152,0.0722));
 vec3 styled=rgb;
 if(treatment>2.5) styled=mix(lowColor.rgb,highColor.rgb,smoothstep(0.06,0.94,lum));
 else if(treatment>1.5) styled=mix(lowColor.rgb,highColor.rgb,lum);
 else if(treatment>0.5){float saturation=max(max(rgb.r,rgb.g),rgb.b)-min(min(rgb.r,rgb.g),rgb.b);styled=mix(rgb*0.82,mix(lowColor.rgb,highColor.rgb,lum*0.3),(1.0-smoothstep(0.02,0.20,saturation))*smoothstep(0.5,1.0,lum));}
 float alpha=pixel.a*((treatment>1.5 && treatment<2.5) ? 0.82:1.0);
 fragColor=vec4(mix(rgb,styled,strength)*alpha,alpha)*qt_Opacity;
}
