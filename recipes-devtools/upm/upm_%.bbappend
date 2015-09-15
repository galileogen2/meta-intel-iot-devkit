FILESEXTRAPATHS_prepend := "${THISDIR}/${PN}:"

SRC_URI = "git://github.com/intel-iot-devkit/upm.git;protocol=git;rev=f983719ef303e72518571bcf7f0ae4f379e1d0a4 \
           file://0001-cmake-revert-to-depend-on-mraa-0.7.5.patch \
           file://0001-adafruitms1438-CMakeLists.txt-stop-RPATH-being-added.patch"

PACKAGECONFIG ??= "python nodejs java"

JAVA_HOME="${STAGING_LIBDIR}/jvm/java-8-openjdk"
export JAVA_HOME="${STAGING_LIBDIR}/jvm/java-8-openjdk"

PACKAGECONFIG ??= "python nodejs java"

PACKAGECONFIG[java] = "-DBUILDSWIGJAVA=ON, -DBUILDSWIGJAVA=OFF, swig-native openjdk-8"

cmake_do_generate_toolchain_file_append() {
  echo "
set (JAVA_AWT_INCLUDE_PATH ${JAVA_HOME}/include CACHE PATH \"AWT include path\" FORCE)
set (JAVA_AWT_LIBRARY ${JAVA_HOME}/jre/lib/amd64/libjawt.so CACHE FILEPATH \"AWT Library\" FORCE)
set (JAVA_INCLUDE_PATH ${JAVA_HOME}/include CACHE PATH \"java include path\" FORCE)
set (JAVA_INCLUDE_PATH2 ${JAVA_HOME}/include/linux CACHE PATH \"java include path\" FORCE)
set (JAVA_JVM_LIBRARY ${JAVA_HOME}/jre/lib/amd64/libjvm.so CACHE FILEPATH \"path to JVM\" FORCE)
" >> ${WORKDIR}/toolchain.cmake
}

FILES_${PN}-dbg += "${libdir}/iotdk/*/.debug \
                    ${libdir}/java/.debug"
