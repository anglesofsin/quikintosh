/* Refresh the user's Finder material/palette after atomic profile updates. */
#include <gtk/gtk.h>
#include <gio/gio.h>
#include <unistd.h>
#include <string.h>
static GtkCssProvider *provider;
static GFileMonitor *monitor;
static char *stylesheet;
static guint pending;
static gboolean reload_css(gpointer unused) {
    (void)unused; pending=0;
    if(g_file_test(stylesheet,G_FILE_TEST_IS_REGULAR))
        gtk_css_provider_load_from_path(provider,stylesheet);
    return G_SOURCE_REMOVE;
}
static void changed(GFileMonitor *m,GFile *file,GFile *other,GFileMonitorEvent event,gpointer unused) {
    (void)m;(void)other;(void)event;(void)unused;
    char *name=g_file_get_basename(file);
    if(g_strcmp0(name,"quickintosh-live.css")==0 && !pending)
        pending=g_timeout_add(80,reload_css,NULL);
    g_free(name);
}
static gboolean install(gpointer unused) {
    (void)unused;
    GdkDisplay *display=gdk_display_get_default();
    if(!display)return G_SOURCE_CONTINUE;
    provider=gtk_css_provider_new();
    stylesheet=g_build_filename(g_get_user_config_dir(),"gtk-4.0","quickintosh-live.css",NULL);
    gtk_style_context_add_provider_for_display(display,GTK_STYLE_PROVIDER(provider),GTK_STYLE_PROVIDER_PRIORITY_USER+1);
    reload_css(NULL);
    char *directory=g_path_get_dirname(stylesheet);
    GFile *folder=g_file_new_for_path(directory);
    monitor=g_file_monitor_directory(folder,G_FILE_MONITOR_NONE,NULL,NULL);
    if(monitor)g_signal_connect(monitor,"changed",G_CALLBACK(changed),NULL);
    g_object_unref(folder);g_free(directory);
    return G_SOURCE_REMOVE;
}
__attribute__((constructor)) static void initialize(void) {
    char exe[4096]; ssize_t length=readlink("/proc/self/exe",exe,sizeof(exe)-1);
    if(length<0)return;
    exe[length]='\0';
    if(!strstr(exe,"/.nautilus-wrapped") && !g_getenv("QUICKINTOSH_THEME_LIVE_TEST"))return;
    /* Do not propagate this GTK4-only provider into applications Finder opens. */
    const char *preload=g_getenv("LD_PRELOAD");
    if(preload){
        char **parts=g_strsplit(preload,":",-1);GString *kept=g_string_new(NULL);
        for(guint i=0;parts[i];i++)if(!strstr(parts[i],"quickintosh-finder-theme-live")){
            if(kept->len)g_string_append_c(kept,':');
            g_string_append(kept,parts[i]);
        }
        if(kept->len)g_setenv("LD_PRELOAD",kept->str,TRUE);else g_unsetenv("LD_PRELOAD");
        g_string_free(kept,TRUE);g_strfreev(parts);
    }
    g_timeout_add(50,install,NULL);
}
