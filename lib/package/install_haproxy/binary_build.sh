function install() {
  if [[ $1 == */ ]]; then
    download_path=${1%?}
  else
    download_path=$1
  fi
  package=$2
  tmp_install=$3
  # shellcheck disable=SC2164
  cd "${download_path}"
  # shellcheck disable=SC1009
  if [ ! -f "${download_path}"/"${package}".tar.gz ]; then
    echo "文件:${download_path}/${package}.tar.gz,不存在，退出！"
    exit 1
  fi
#  if [ ! -f "${tmp_install}"/'haproxy.service' ]; then
#    echo "启动脚本不存在：$tmp_install/haproxy.service"
#    exit 1
#  fi
  # shellcheck disable=SC2164
  tar -zxvf "${package}".tar.gz && cd "${package}" && make clean && make PREFIX="$tmp_install" TARGET=linux2628 && make install PREFIX="$tmp_install"
  # shellcheck disable=SC2181
  if [ $? -ne 0 ]; then
    echo "执行失败：tar -zxvf ${package}.tar.gz && cd haproxy &&  make PREFIX=$tmp_install TARGET=linux2628 && make install PREFIX=$tmp_install"
    exit 1
  fi
}
install "$1" "$2" "$3"
