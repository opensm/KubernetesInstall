function download() {
  if [[ $1 == */ ]]; then
    download_path=${1%?}
  else
    download_path=$1
  fi
  package=$2
  if [ ! -d "${download_path}" ]; then
    echo "目录不存在即将创建：$1"
  fi
  mkdir -pv "${download_path}"
  # shellcheck disable=SC2181
  if [ $? -ne 0 ]; then
    echo "创建下载目录失败：$1"
    exit 1
  fi
  wget -O "${download_path}"/"${package}".tar.gz https://keepalived.org/software/"${package}".tar.gz
  # shellcheck disable=SC2181
  if [ $? -ne 0 ]; then
    echo "下载文件失败：${download_path}/${package}.tar.gz"
    exit 1
  fi
}

function install() {
  download_path=$1
  package=$2
  tmp_install=$3
  # shellcheck disable=SC2164
  cd "${download_path}"
  # shellcheck disable=SC1009
  if [ ! -f "$package".tar.gz ]; then
    #    download "$download_path" "$package"
    echo "${download_path} 下不存在 $package.tar.gz"
  fi
  # shellcheck disable=SC2164
  tar -zxvf "${package}".tar.gz && cd "${package}" && ./configure --prefix="${tmp_install}" && make && make install
  # shellcheck disable=SC2181
  if [ $? -ne 0 ]; then
    echo "执行失败：tar -zxvf ${package}.tar.gz && cd ${package} && ./configure --prefix=${tmp_install} && make && make install"
    exit 1
  fi
}
install "$1" "$2" "$3"
