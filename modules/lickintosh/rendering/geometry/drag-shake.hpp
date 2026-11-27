#pragma once
#include <chrono>
#include <cmath>
struct DragShake {
 using Clock=std::chrono::steady_clock;
 bool tracking=false,fired=false;
 int reversals=0,dx=0,dy=0;
 double lastX=0,lastY=0,turnX=0,turnY=0,travel=0;
 Clock::time_point start{},lastTurn{};
 void reset(){*this=DragShake{};}
 bool sample(bool drag,double x,double y,Clock::time_point now){
  if(!drag){reset();return false;}
  if(!tracking){tracking=true;lastX=turnX=x;lastY=turnY=y;start=lastTurn=now;return false;}
  if(fired)return false;
  const double mx=x-lastX,my=y-lastY;lastX=x;lastY=y;
  const int nx=std::abs(mx)>1 ? (mx>0 ? 1:-1):dx,ny=std::abs(my)>1 ? (my>0 ? 1:-1):dy;
  const bool turn=(dx && nx!=dx && std::abs(x-turnX)>24)||(dy && ny!=dy && std::abs(y-turnY)>24);
  travel+=std::hypot(mx,my);
  if(now-lastTurn>std::chrono::milliseconds(700)){reversals=0;travel=0;start=now;}
  if(turn){++reversals;turnX=x;turnY=y;lastTurn=now;}
  dx=nx;dy=ny;
  if(reversals>=5 && travel>=280 && now-start<std::chrono::milliseconds(2200)){fired=true;return true;}
  return false;
 }
};
