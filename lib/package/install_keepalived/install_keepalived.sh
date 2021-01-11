
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
  # shellcheck disable=SC2164
  cd "${download_path}"
  # shellcheck disable=SC1009
  if [ ! -f "$package".tar.gz ]; then
    download "$download_path" "$package"
  fi
  # shellcheck disable=SC2164
  tar -zxvf "${package}".tar.gz && cd "${package}" && ./configure --prefix=/usr/local/keepalived && make && make install
  # shellcheck disable=SC2181
  if [ $? -ne 0 ];then
    echo "执行失败：tar -zxvf ${package}.tar.gz && cd ${package} && ./configure --prefix=/usr/local/keepalived && make && make install"
    exit 1
  fi
  ln -s /usr/local/keepalived/sbin/keepalived /usr/sbin/ && cp ./keepalived/etc/init.d/keepalived /etc/init.d/keepalived && ln -s /usr/local/keepalived/etc/sysconfig/keepalived /etc/sysconfig && chmod +x /etc/init.d/keepalived && chkconfig --add keepalived && chkconfig keepalived on
  # shellcheck disable=SC2181
  if [ $? -ne 0 ];then
    echo "执行失败：ln -s /usr/local/keepalived/sbin/keepalived /usr/sbin/ && cp ./keepalived/etc/init.d/keepalived /etc/init.d/keepalived && ln -s /usr/local/keepalived/etc/sysconfig/keepalived /etc/sysconfig && chmod +x /etc/init.d/keepalived && chkconfig --add keepalived && chkconfig keepalived on"
    exit 1
  fi
}
install "$1" "$2"
