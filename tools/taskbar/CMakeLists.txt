cmake_minimum_required(VERSION 3.20)
project(wtmm_taskbar LANGUAGES CXX)
add_library(wtmm_taskbar SHARED taskbar_pin.cpp)
target_compile_features(wtmm_taskbar PRIVATE cxx_std_20)
target_link_libraries(wtmm_taskbar PRIVATE windowsapp runtimeobject advapi32)
set_target_properties(wtmm_taskbar PROPERTIES
  OUTPUT_NAME "wtmm_taskbar"
  WINDOWS_EXPORT_ALL_SYMBOLS OFF
)
