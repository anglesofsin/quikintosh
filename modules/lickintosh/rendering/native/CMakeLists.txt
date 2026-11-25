cmake_minimum_required(VERSION 3.21)
project(QuickintoshRendering LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_AUTOMOC ON)
find_package(Qt6 REQUIRED COMPONENTS Core Gui Qml Quick Network)
qt_add_qml_module(quickintosh_render
 URI Quickintosh.Render VERSION 1.0
 OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/Quickintosh/Render
 SOURCES FramePacer.h FramePacer.cpp)
set_target_properties(quickintosh_render quickintosh_renderplugin PROPERTIES INSTALL_RPATH "$ORIGIN")
target_link_libraries(quickintosh_render PRIVATE Qt6::Core Qt6::Gui Qt6::Qml Qt6::Quick Qt6::Network)
install(TARGETS quickintosh_render quickintosh_renderplugin LIBRARY DESTINATION lib/qt-6/qml/Quickintosh/Render)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/Quickintosh/Render/qmldir
 ${CMAKE_CURRENT_BINARY_DIR}/Quickintosh/Render/quickintosh_render.qmltypes
 DESTINATION lib/qt-6/qml/Quickintosh/Render)
