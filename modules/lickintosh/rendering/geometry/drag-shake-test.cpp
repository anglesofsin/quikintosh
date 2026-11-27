#include "drag-shake.hpp"
#include <cassert>
int main(){
 DragShake d;auto t=DragShake::Clock::now();bool fired=false;
 for(int i=0;i<20;++i)assert(!d.sample(false,i*60,0,t+std::chrono::milliseconds(i*30)));
 for(int i=0;i<20;++i)assert(!d.sample(true,i*60,0,t+std::chrono::milliseconds(i*30)));
 d.reset();
 for(int i=0;i<18;++i)fired=d.sample(true,i%2 ? 100:0,20,t+std::chrono::milliseconds(i*80))||fired;
 assert(fired);assert(!d.sample(true,0,0,t+std::chrono::milliseconds(1800)));
 d.sample(false,0,0,t);assert(!d.tracking);
}
