#include "focus-restore-policy.hpp"
int main() {
 for(int bits=0;bits<32;++bits){
  const bool monitor=bits&1,exclusive=bits&2,window=bits&4,workspace=bits&8,visible=bits&16;
  const bool expected=monitor && !exclusive && window && workspace && !visible;
  if(shouldRefocusPointer(monitor,exclusive,window,workspace,visible)!=expected)return bits+1;
 }
 static_assert(shouldRefocusPointer(true,false,true,true,false));
 static_assert(!shouldRefocusPointer(true,false,true,true,true));
 static_assert(!shouldRefocusPointer(true,true,true,true,false));
 return 0;
}
