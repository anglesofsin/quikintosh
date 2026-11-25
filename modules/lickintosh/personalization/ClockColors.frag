#version 440
layout(location=0) in vec2 qt_TexCoord0;
layout(location=0) out vec4 fragColor;
layout(std140,binding=0) uniform buf{
 mat4 qt_Matrix;float qt_Opacity;
 vec4 firstColor;vec4 secondColor;vec4 thirdColor;
 float mode;float split;float softness;float glass;
};
layout(binding=1) uniform sampler2D maskTex;
layout(binding=2) uniform sampler2D glassTex;
void main(){
 vec2 uv=qt_TexCoord0;float a=texture(maskTex,uv).a;
 float p=mode<1.5 ? uv.x:mode<2.5 ? uv.y:mode<3.5 ? (uv.x+uv.y)*.5:fract(uv.x*4.);
 float edge=max(.0001,softness);float t=smoothstep(split-edge,split+edge,p);
 vec4 ink=mix(firstColor,secondColor,t);
 if(mode>4.5)ink=mix(mix(firstColor,secondColor,smoothstep(.15,.5,uv.x)),thirdColor,smoothstep(.5,.85,uv.x));
 vec4 material=texture(glassTex,uv);
 vec3 color=mix(ink.rgb,mix(material.rgb,ink.rgb,.42),glass);
 fragColor=vec4(color*a*ink.a,a*ink.a)*qt_Opacity;
}
