FILESEXTRAPATHS_prepend := "${THISDIR}/${PN}:"

SRC_URI = "git://github.com/intel-iot-devkit/mraa.git;protocol=git;rev=e2aaa349ff42038dc56b7a4e0407b08e45e816c6"

PACKAGECONFIG ??= "python nodejs java"

PACKAGECONFIG[java] = "-DBUILDSWIGJAVA=ON, -DBUILDSWIGJAVA=OFF, swig-native openjdk-8"

JAVA_HOME="${STAGING_LIBDIR}/jvm/java-8-openjdk"
export JAVA_HOME="${STAGING_LIBDIR}/jvm/java-8-openjdk"

cmake_do_generate_toolchain_file_append() {
  echo "
set (JAVA_AWT_INCLUDE_PATH ${JAVA_HOME}/include CACHE PATH \"AWT include path\" FORCE)
set (JAVA_AWT_LIBRARY ${JAVA_HOME}/jre/lib/amd64/libjawt.so CACHE FILEPATH \"AWT Library\" FORCE)
set (JAVA_INCLUDE_PATH ${JAVA_HOME}/include CACHE PATH \"java include path\" FORCE)
set (JAVA_INCLUDE_PATH2 ${JAVA_HOME}/include/linux CACHE PATH \"java include path\" FORCE)
set (JAVA_JVM_LIBRARY ${JAVA_HOME}/jre/lib/amd64/libjvm.so CACHE FILEPATH \"path to JVM\" FORCE)
" >> ${WORKDIR}/toolchain.cmake
}

FILES_${PN}-dbg += " ${libdir}/iotdk/*/.debug/libmraajava.so"
