/* Refresh the user's Finder material/palette after atomic profile updates. */
#include <gtk/gtk.h>
#include <gio/gio.h>
#include <gdk/wayland/gdkwayland.h>
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
/* Only native portal choosers receive the floating-dialog application id. */
static void chooser_realized(GtkWidget *widget,gpointer unused) {
    (void)unused;
    GdkSurface *surface=gtk_native_get_surface(GTK_NATIVE(widget));
    if(surface && GDK_IS_WAYLAND_TOPLEVEL(surface))
        gdk_wayland_toplevel_set_application_id(GDK_TOPLEVEL(surface),"org.quickintosh.Finder.FileChooser");
}
static void windows_changed(GListModel *windows,guint position,guint removed,guint added,gpointer unused) {
    (void)removed;(void)unused;
    for(guint i=position;i<position+added;i++){
        GtkWindow *window=g_list_model_get_item(windows,i);
        if(g_strcmp0(G_OBJECT_TYPE_NAME(window),"NautilusFileChooser")==0 && !g_object_get_data(G_OBJECT(window),"qi-chooser")){
            g_object_set_data(G_OBJECT(window),"qi-chooser",GINT_TO_POINTER(1));
            g_signal_connect(window,"realize",G_CALLBACK(chooser_realized),NULL);
            /* GTK may restore its app id during map; set the chooser id in
             * that same mapping turn, before the compositor presents it. */
            g_signal_connect(window,"map",G_CALLBACK(chooser_realized),NULL);
            if(gtk_widget_get_realized(GTK_WIDGET(window)))chooser_realized(GTK_WIDGET(window),NULL);
        }
        g_object_unref(window);
    }
}
static gboolean install(gpointer unused) {
    (void)unused;
    GdkDisplay *display=gdk_display_get_default();
    if(!display)return G_SOURCE_CONTINUE;
    GListModel *windows=gtk_window_get_toplevels();
    g_signal_connect(windows,"items-changed",G_CALLBACK(windows_changed),NULL);
    windows_changed(windows,0,0,g_list_model_get_n_items(windows),NULL);
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
