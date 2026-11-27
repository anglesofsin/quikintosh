// Native input for private nested-compositor tests only. Refuse the host runtime.
#include <wayland-client.h>
#include "virtual-pointer.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
static struct zwlr_virtual_pointer_manager_v1 *manager;
static void global(void*d,struct wl_registry*r,uint32_t n,const char*i,uint32_t v){
 if(strcmp(i,zwlr_virtual_pointer_manager_v1_interface.name)==0)manager=wl_registry_bind(r,n,&zwlr_virtual_pointer_manager_v1_interface,v>2?2:v);
}
static void removed(void*d,struct wl_registry*r,uint32_t n){}
static uint32_t now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint32_t)(t.tv_sec*1000+t.tv_nsec/1000000);}
int main(void){
 const char*runtime=getenv("XDG_RUNTIME_DIR");if(!runtime||strncmp(runtime,"/tmp/",5))return 2;
 struct wl_display*d=wl_display_connect(NULL);if(!d)return 3;
 struct wl_registry*r=wl_display_get_registry(d);const struct wl_registry_listener l={global,removed};wl_registry_add_listener(r,&l,NULL);wl_display_roundtrip(d);if(!manager)return 4;
 struct zwlr_virtual_pointer_v1*p=zwlr_virtual_pointer_manager_v1_create_virtual_pointer(manager,NULL);wl_display_roundtrip(d);
 char line[128];while(fgets(line,sizeof line,stdin)){
  double x,y;if(sscanf(line,"move %lf %lf",&x,&y)==2)zwlr_virtual_pointer_v1_motion(p,now(),wl_fixed_from_double(x),wl_fixed_from_double(y));
  else if(!strncmp(line,"down",4))zwlr_virtual_pointer_v1_button(p,now(),0x110,WL_POINTER_BUTTON_STATE_PRESSED);
  else if(!strncmp(line,"up",2))zwlr_virtual_pointer_v1_button(p,now(),0x110,WL_POINTER_BUTTON_STATE_RELEASED);
  else if(!strncmp(line,"quit",4))break;
  zwlr_virtual_pointer_v1_frame(p);wl_display_roundtrip(d);puts("ok");fflush(stdout);
 }
 zwlr_virtual_pointer_v1_destroy(p);wl_display_disconnect(d);return 0;
}
