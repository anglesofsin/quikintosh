#pragma once
#include <QObject>
#include <QHash>
#include <QVariantList>
#include <QMap>
#include <QByteArray>
#include <QtQml/qqmlregistration.h>
#include <atomic>
#include <memory>
class QQuickWindow;
class QLocalSocket;
class QTimer;
class QChronoTimer;
struct FramePolicy;
struct WindowFrames;
class FramePacer : public QObject {
 Q_OBJECT
 QML_ELEMENT
 QML_SINGLETON
 Q_PROPERTY(QVariantMap geometry READ geometry NOTIFY geometryChanged)
 Q_PROPERTY(bool geometryAvailable READ geometryAvailable NOTIFY geometryChanged)
 Q_PROPERTY(int maximumFps READ maximumFps WRITE setMaximumFps NOTIFY maximumFpsChanged)
 Q_PROPERTY(bool measuring READ measuring WRITE setMeasuring NOTIFY measuringChanged)
public:
 explicit FramePacer(QObject *parent=nullptr);
 ~FramePacer() override;
 int maximumFps() const;
 void setMaximumFps(int value);
 bool measuring() const;
 void setMeasuring(bool value);
 QVariantMap geometry()const{return renderedGeometry;}
 bool geometryAvailable()const{return hasGeometry;}
 Q_INVOKABLE void requestGeometry();
 Q_INVOKABLE void setGeometryMotion(bool active,int fps);
 Q_INVOKABLE void prepareWindows(bool keep);
 Q_INVOKABLE void label(QObject *window,const QString &role);
 Q_INVOKABLE QVariantList statistics();
signals:
 void geometryChanged();
 void maximumFpsChanged();
 void measuringChanged();
protected:
 bool eventFilter(QObject *,QEvent *) override;
private:
 void attach(QQuickWindow *window);
 QVariantMap renderedGeometry;
 bool hasGeometry=false;
 QChronoTimer *motionTimer=nullptr;
 bool motionRequested=false,nativeAnimating=false;
 int geometryLimit=0;
 double reportedRefresh=0;
 void updateGeometryTimer();
 QLocalSocket *geometrySocket=nullptr;
 QTimer *geometryTimeout=nullptr;
 QByteArray geometryReply;
 qint64 nextGeometryAttempt=0;
 bool keepPrepared=true;
 std::shared_ptr<FramePolicy> policy;
 QHash<QQuickWindow *,std::shared_ptr<WindowFrames>> windows;
};
